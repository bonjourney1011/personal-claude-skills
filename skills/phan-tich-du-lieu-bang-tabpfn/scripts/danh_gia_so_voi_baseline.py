"""Danh gia TabPFN va LightGBM tren cung mot tap test.

Cach dung:
    python danh_gia_so_voi_baseline.py data.csv --target <cot> [--time-col <cot ngay>] [--test-size 0.2]

- Co --time-col: cat theo thoi gian (phan cuoi lam test). Khong co: chia ngau nhien, seed co dinh.
- TabPFN chay qua tabpfn-client va can bien moi truong TABPFN_TOKEN. Thieu token thi chi chay baseline.
- Khong impute, khong one-hot: ca hai model nhan NaN va cot phan loai truc tiep.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split

QUANTILES = [0.1, 0.5, 0.9]
MAX_CLASSES = 20


def load_and_split(args):
    df = pd.read_csv(args.csv)
    if args.target not in df.columns:
        sys.exit(f"Khong thay cot muc tieu '{args.target}'. Cac cot: {list(df.columns)}")
    df = df.dropna(subset=[args.target])
    if args.time_col:
        df = df.sort_values(args.time_col)
        cut = int(len(df) * (1 - args.test_size))
        train, test = df.iloc[:cut], df.iloc[cut:]
        drop = [args.target, args.time_col]
    else:
        train, test = train_test_split(df, test_size=args.test_size, random_state=42)
        drop = [args.target]
    X_train, X_test = train.drop(columns=drop), test.drop(columns=drop)
    for col in X_train.select_dtypes(include=["object", "string"]).columns:
        cats = pd.Categorical(X_train[col]).categories
        X_train[col] = pd.Categorical(X_train[col], categories=cats)
        X_test[col] = pd.Categorical(X_test[col], categories=cats)
    return X_train, X_test, train[args.target], test[args.target]


def is_classification(y: pd.Series) -> bool:
    return not pd.api.types.is_numeric_dtype(y) or y.nunique() <= MAX_CLASSES


def score_classification(y_true, proba, classes) -> dict:
    pred = np.asarray(classes)[proba.argmax(axis=1)]
    out = {"accuracy": accuracy_score(y_true, pred), "log_loss": log_loss(y_true, proba, labels=classes)}
    if len(classes) == 2:
        out["roc_auc"] = roc_auc_score(y_true == classes[1], proba[:, 1])
    return out


def score_regression(y_true, q10, q50, q90) -> dict:
    inside = (y_true >= q10) & (y_true <= q90)
    return {
        "mae_trung_vi": mean_absolute_error(y_true, q50),
        "r2_trung_vi": r2_score(y_true, q50),
        "do_phu_dai_10_90": float(np.mean(inside)),
    }


def run_lightgbm(X_train, X_test, y_train, y_test, classify: bool) -> dict:
    import lightgbm as lgb

    if classify:
        model = lgb.LGBMClassifier(random_state=42, verbose=-1).fit(X_train, y_train)
        return score_classification(y_test, model.predict_proba(X_test), list(model.classes_))
    preds = [
        lgb.LGBMRegressor(objective="quantile", alpha=q, random_state=42, verbose=-1)
        .fit(X_train, y_train)
        .predict(X_test)
        for q in QUANTILES
    ]
    return score_regression(y_test.to_numpy(), *preds)


def run_tabpfn(X_train, X_test, y_train, y_test, classify: bool) -> dict | None:
    token = os.environ.get("TABPFN_TOKEN")
    if not token:
        print("Chua co TABPFN_TOKEN: bo qua TabPFN, chi chay baseline.")
        return None
    import tabpfn_client
    from tabpfn_client import TabPFNClassifier, TabPFNRegressor

    tabpfn_client.set_access_token(token)
    if classify:
        model = TabPFNClassifier().fit(X_train, y_train)
        return score_classification(y_test, model.predict_proba(X_test), list(model.classes_))
    model = TabPFNRegressor().fit(X_train, y_train)
    q10, q50, q90 = model.predict(X_test, output_type="quantiles", quantiles=QUANTILES)
    return score_regression(y_test.to_numpy(), np.asarray(q10), np.asarray(q50), np.asarray(q90))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv")
    p.add_argument("--target", required=True)
    p.add_argument("--time-col")
    p.add_argument("--test-size", type=float, default=0.2)
    args = p.parse_args()

    X_train, X_test, y_train, y_test = load_and_split(args)
    classify = is_classification(y_train)
    split = f"theo thoi gian ({args.time_col})" if args.time_col else "ngau nhien (seed 42)"
    print(f"Bai toan: {'phan loai' if classify else 'hoi quy'} | chia: {split}")
    print(f"Lich su: {len(X_train)} dong | Test: {len(X_test)} dong | Feature: {X_train.shape[1]}")

    results = {"LightGBM": run_lightgbm(X_train, X_test, y_train, y_test, classify)}
    try:
        tab = run_tabpfn(X_train, X_test, y_train, y_test, classify)
    except Exception as e:  # loi mang, het han muc, token sai
        print(f"TabPFN loi: {type(e).__name__}: {e}")
        tab = None
    if tab:
        results["TabPFN"] = tab

    print("\n" + pd.DataFrame(results).round(4).to_string())
    if not classify:
        print("\nDo phu dai 10-90 ky vong khoang 0.80. Thap hon nhieu la model qua tu tin.")


if __name__ == "__main__":
    main()
