(function () {
  const D = DATA;
  const $ = (id) => document.getElementById(id);
  const KIND = {
    files: "File của bạn", tools: "Công cụ & cấu hình", app: "Ứng dụng (AppData)", agent: "Lịch sử AI agent",
    build: "Build & thư viện dự án", cache: "Cache", docker: "Docker & WSL", ai: "Model AI",
  };
  const GB = 1024 ** 3, MB = 1024 ** 2;
  const fmt = (b) => b >= GB ? (b / GB).toFixed(b >= 100 * GB ? 0 : 1) + " GB"
    : b >= MB ? Math.round(b / MB) + " MB" : Math.max(0, Math.round(b / 1024)) + " KB";
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const grew = (d) => d != null && d >= D.grow_threshold;
  const sum = (list) => list.reduce((s, i) => s + i.size, 0);
  const itemById = Object.fromEntries(D.items.map((i) => [i.id, i]));

  function renderHeader() {
    $("sub").textContent = `Quét lúc ${D.scanned_at} · ${D.roots.join(", ")} · chỉ đọc dung lượng, không mở nội dung file`;
    const safe = D.items.filter((i) => i.cat === "safe"), review = D.items.filter((i) => i.cat === "review");
    const stats = [
      ["Còn trống", fmt(D.disk.free), `trên ${fmt(D.disk.total)} · ổ ${D.disk.drive}`, "free"],
      ["An toàn để xóa", fmt(sum(safe)), `${safe.length} mục`, "safe"],
      ["Cần xem lại", fmt(sum(review)), `${review.length} mục`, "review"],
      ["Ngoài vùng quét", fmt(D.unmapped), "Windows, phần mềm, thư mục bỏ qua", "out"],
    ];
    $("stats").innerHTML = stats.map(([k, v, s, c]) =>
      `<div class="stat stat-${c}"><span class="stat-k">${k}</span><span class="stat-v">${v}</span><span class="stat-s">${s}</span></div>`).join("");
    const skipped = D.skipped.length ? `Bỏ qua (không quét): ${D.skipped.map(esc).join(", ")}. ` : "";
    $("skipped").innerHTML = `${skipped}${D.denied} thư mục bị Windows từ chối quyền đọc nên được bỏ qua. Dữ liệu gốc: <code>~/disk-report/scan.json</code>.`;
  }

  function renderGrowth() {
    const el = $("grow");
    if (!D.prev_scanned_at) {
      el.innerHTML = "<p>Lần quét đầu tiên. Dung lượng từng mục đã ghi vào <code>~/disk-report/sizes.csv</code>; lần sau sẽ so sánh và đánh dấu mục tăng.</p>";
    } else if (!D.increases.length) {
      el.innerHTML = `<p>So với lần quét ${esc(D.prev_scanned_at)}: không mục nào tăng quá ${fmt(D.grow_threshold)}.</p>`;
    } else {
      el.innerHTML = `<p><strong>Tăng từ lần quét ${esc(D.prev_scanned_at)}</strong> <span class="muted small">(viền cam trên bản đồ)</span></p><ul class="grow-list">` +
        D.increases.map((g) => `<li><span class="up">▲ ${fmt(g.delta)}</span> <span class="mono">${esc(g.label)}</span> <span class="muted">→ ${fmt(g.size)}</span></li>`).join("") + "</ul>";
    }
  }

  // Squarified treemap (Bruls et al.): items sorted by v desc, returns rects in px.
  function squarify(items, x, y, w, h) {
    const out = [], total = items.reduce((s, i) => s + i.v, 0);
    if (!total || w <= 0 || h <= 0) return out;
    const scale = (w * h) / total;
    const worst = (row, side) => {
      const a = row.map((r) => r.v * scale), s = a.reduce((p, q) => p + q, 0);
      return Math.max((side * side * Math.max(...a)) / (s * s), (s * s) / (side * side * Math.min(...a)));
    };
    const place = (row) => {
      const s = row.reduce((p, r) => p + r.v * scale, 0);
      if (w >= h) {
        const cw = s / h; let cy = y;
        for (const r of row) { const rh = (r.v * scale) / cw; out.push({ item: r, x, y: cy, w: cw, h: rh }); cy += rh; }
        x += cw; w -= cw;
      } else {
        const rh = s / w; let cx = x;
        for (const r of row) { const rw = (r.v * scale) / rh; out.push({ item: r, x: cx, y, w: rw, h: rh }); cx += rw; }
        y += rh; h -= rh;
      }
    };
    let row = [];
    for (const it of items) {
      const side = Math.min(w, h);
      if (!row.length || worst(row, side) >= worst(row.concat(it), side)) row.push(it);
      else { place(row); row = [it]; }
    }
    if (row.length) place(row);
    return out;
  }

  function tileEl(t, group) {
    const c = t.item, b = document.createElement("button");
    b.type = "button";
    b.className = `tile k-${c.kind}${c.safe ? " hatch" : ""}${grew(c.delta) ? " grew" : ""}`;
    b.style.cssText = `left:${t.x + 1}px;top:${t.y + 1}px;width:${Math.max(0, t.w - 2)}px;height:${Math.max(0, t.h - 2)}px`;
    b.title = `${c.path || c.name} · ${fmt(c.size)}`;
    b.setAttribute("aria-label", b.title);
    if (t.w > 54 && t.h > 30) {
      const big = Math.min(t.w, t.h) > 120 ? " big" : "";
      b.innerHTML = `<span class="t-name">${esc(c.name)}</span><span class="t-size${big}">${fmt(c.size)}</span>` +
        (grew(c.delta) && t.h > 60 ? `<span class="t-up">▲ ${fmt(c.delta)}</span>` : "");
    }
    b.addEventListener("click", () => showInfo(c, group));
    return b;
  }

  function showInfo(c, group) {
    const rule = c.rule && itemById[c.rule];
    const parts = [`<strong class="mono">${esc(c.path || `${group.name} › ${c.name}`)}</strong>`, fmt(c.size), KIND[c.kind] || ""];
    if (c.delta != null && c.delta !== 0) parts.push(`${c.delta > 0 ? "+" : "−"}${fmt(Math.abs(c.delta))} so với lần trước`);
    $("info").innerHTML = parts.join(" · ") + (rule ? `<br><span class="muted">${esc(rule.why)}</span>` : "");
  }

  function renderMap() {
    const box = $("treemap"), W = box.clientWidth, H = box.clientHeight;
    box.innerHTML = "";
    const groups = D.groups.filter((g) => g.size > 0).map((g) => ({ ...g, v: g.size }));
    for (const r of squarify(groups, 0, 0, W, H)) {
      const g = r.item, el = document.createElement("div");
      el.className = "grp";
      el.style.cssText = `left:${r.x + 1}px;top:${r.y + 1}px;width:${r.w - 2}px;height:${r.h - 2}px`;
      const head = r.h > 48 && r.w > 70 ? 20 : 0;
      if (head) el.innerHTML = `<div class="grp-head"><span>${esc(g.name)}</span><span class="mono">${fmt(g.size)}</span></div>`;
      box.appendChild(el);
      const kids = (g.children && g.children.length ? g.children : [g]).filter((c) => c.size > 0)
        .map((c) => ({ ...c, v: c.size })).sort((a, b) => b.v - a.v);
      for (const t of squarify(kids, 1, head + 1, r.w - 4, r.h - head - 4)) el.appendChild(tileEl(t, g));
    }
    const kinds = new Set(D.groups.flatMap((g) => [g.kind, ...(g.children || []).map((c) => c.kind)]));
    $("legend").innerHTML = Object.keys(KIND).filter((k) => kinds.has(k))
      .map((k) => `<span><i class="k-${k}"></i>${KIND[k]}</span>`).join("") +
      '<span><i class="k-cache hatch-sw" style="background-image:repeating-linear-gradient(135deg,transparent 0 3px,var(--hatch) 3px 5px)"></i>An toàn để xóa</span>';
  }

  function recHtml(i) {
    const list = i.paths.length > 1
      ? `<details><summary>${i.paths.length} thư mục</summary><ul class="paths">${i.paths.slice(0, 40)
        .map((p) => `<li><span class="mono">${esc(p.path)}</span> <span class="muted">${fmt(p.size)}</span></li>`).join("")}${
        i.paths.length > 40 ? `<li class="muted">… và ${i.paths.length - 40} thư mục nữa (đều có trong script)</li>` : ""}</ul></details>`
      : `<div class="mono muted path1">${esc(i.paths[0].path)}</div>`;
    return `<div class="rec"><label class="rec-top" for="cb-${i.id}"><input type="checkbox" id="cb-${i.id}">` +
      `<span class="dot k-${i.kind}"></span><span class="rec-name">${esc(i.label)}</span>` +
      `${grew(i.delta) ? `<span class="up">▲ ${fmt(i.delta)}</span>` : ""}<span class="rec-size mono">${fmt(i.size)}</span></label>` +
      `<code class="rec-cmd">${esc(i.preview)}</code><p class="rec-why">${esc(i.why)}</p>${list}</div>`;
  }

  function renderRecs() {
    const section = (cat, title, note) => {
      const list = D.items.filter((i) => i.cat === cat);
      return list.length ? `<h3 class="rec-h rec-h-${cat}">${title} · ${fmt(sum(list))}</h3><p class="rec-note">${note}</p>${list.map(recHtml).join("")}` : "";
    };
    $("recs").innerHTML = (section("safe", "Có thể xóa an toàn", "Công cụ tự tải lại hoặc build lại khi cần.") +
      section("review", "Cần xem lại trước khi xóa", "Có thể mất lịch sử phiên, model AI hoặc dữ liệu khó lấy lại.")) ||
      '<p class="muted">Không tìm thấy mục rác nào đáng kể.</p>';
    D.items.forEach((i) => $("cb-" + i.id).addEventListener("change", updateSelection));
    selectWhere((i) => i.cat === "safe");
  }

  const selected = () => D.items.filter((i) => $("cb-" + i.id).checked);
  function selectWhere(test) { D.items.forEach((i) => { $("cb-" + i.id).checked = test(i); }); updateSelection(); }
  function updateSelection() {
    const s = selected();
    $("selsum").innerHTML = `Đã chọn <strong>${fmt(sum(s))}</strong> · ${s.length} mục`;
    $("btn-copy").disabled = !s.length;
  }

  function copyScript() {
    const text = [D.script_header, ...selected().map((i) => i.script), D.script_footer].join("\n\n") + "\n";
    const ta = $("script-text"), status = (msg) => { $("copy-status").textContent = msg; };
    ta.value = text;
    $("script-box").hidden = false;
    const manual = () => { ta.focus(); ta.select(); status("Không copy tự động được: script đã được bôi đen, nhấn Ctrl+C."); };
    try {
      navigator.clipboard.writeText(text).then(() => status("Đã copy. Dán vào PowerShell, đọc lại rồi mới chạy."), manual);
    } catch (e) { manual(); }
    $("script-box").scrollIntoView({ block: "nearest" });
  }

  renderHeader();
  renderGrowth();
  renderRecs();
  renderMap();
  $("btn-safe").addEventListener("click", () => selectWhere((i) => i.cat === "safe"));
  $("btn-none").addEventListener("click", () => selectWhere(() => false));
  $("btn-copy").addEventListener("click", copyScript);
  let raf = 0;
  const rerender = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(renderMap); };
  if (window.ResizeObserver) new ResizeObserver(rerender).observe($("treemap"));
  else window.addEventListener("resize", rerender);
})();
