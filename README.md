# Personal Claude Skills

Các skill tự làm cho [Claude Code](https://claude.com/claude-code). Mỗi skill là một thư mục trong `skills/`.

| Skill | Làm gì | Gọi bằng |
|---|---|---|
| [don-rac-o-dia](skills/don-rac-o-dia/SKILL.md) | Quét ổ đĩa Windows ở chế độ chỉ đọc, vẽ bản đồ dung lượng, đề xuất dọn rác (an toàn / cần xem lại) và tạo script PowerShell. Không tự xóa gì. | "dọn rác", "ổ C đầy", `/don-rac-o-dia` |

## Cài đặt

Chép thư mục skill cần dùng vào thư mục skills của Claude Code:

```powershell
git clone https://github.com/bonjourney1011/personal-claude-skills.git
Copy-Item -Recurse personal-claude-skills\skills\don-rac-o-dia "$env:USERPROFILE\.claude\skills\"
```

Sau đó mở Claude Code và gọi skill theo cột "Gọi bằng". Yêu cầu riêng của từng skill ghi trong `SKILL.md` của nó.

## Thêm skill mới

Tạo `skills/<ten-skill>/SKILL.md` (frontmatter `name`, `description`), thêm một dòng vào bảng trên.
