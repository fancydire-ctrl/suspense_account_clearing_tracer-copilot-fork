#!/usr/bin/env python3
"""Generate deterministic, synthetic SAP ECC suspense-account test data.

The detail output uses the dashboard's canonical CSV columns plus common SAP ECC
references. No real company, customer, vendor, or account data is used.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

DEFAULT_ROWS = 50_000
SEED = 20260919
START_DATE = date(2024, 1, 1)
DAYS = 731  # Two years, including leap day.

ACCOUNTS = [
    ("001100", "Bank suspense"),
    ("001200", "AR clearing"),
    ("001300", "AP clearing"),
    ("001400", "GR/IR clearing"),
    ("001500", "Payroll suspense"),
    ("001600", "Tax suspense"),
    ("001700", "Intercompany clearing"),
    ("001800", "Cash application suspense"),
    ("001900", "Payment gateway suspense"),
    ("002000", "Manual journal suspense"),
]
COMPANIES = ["1000", "1100", "2000", "3000"]
CURRENCIES = ["USD", "EUR", "GBP", "CAD"]
OWNERS = ["A. Patel", "L. Gomez", "R. Singh", "J. Williams", "M. Clarke", "K. Moore"]
CATEGORIES = ["Bank reconciliation", "Vendor invoice", "Customer receipt", "Tax", "Payroll", "Intercompany"]
REASONS = ["Unmatched receipt", "Missing reference", "Timing difference", "Interface exception", "Duplicate suspected", "Approval pending"]
STATUSES = ["open", "cleared", "investigating", "disputed", "writtenoff"]
STATUS_WEIGHTS = [42, 34, 13, 8, 3]

DETAIL_FIELDS = [
    "transaction_id", "posting_date", "suspense_account", "owner", "category", "business_unit",
    "amount", "currency", "status", "age_days", "cleared_date", "reference", "reason",
    "source_system", "customer_vendor", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT",
    "HKONT", "WAERS", "DMBTR", "WRBTR", "SHKZG", "BLART", "XBLNR", "ZUONR", "SGTXT",
    "LIFNR", "KUNNR",
]


def money(rng: random.Random) -> Decimal:
    return Decimal(rng.randint(25_00, 250_000_00)) / 100


def generate(rows: int, output: Path, seed: int = SEED) -> None:
    rng = random.Random(seed)
    totals = defaultdict(lambda: {"transactions": 0, "amount": Decimal("0.00"), "open_amount": Decimal("0.00")})
    by_month = defaultdict(lambda: {"transactions": 0, "amount": Decimal("0.00"), "open_amount": Decimal("0.00")})

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS)
        writer.writeheader()
        for i in range(rows):
            posted = START_DATE + timedelta(days=rng.randrange(DAYS))
            account_no, account_name = ACCOUNTS[rng.randrange(len(ACCOUNTS))]
            currency = rng.choice(CURRENCIES)
            amount = money(rng)
            status = rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
            age = min(730, (date.today() - posted).days if status != "cleared" else rng.randint(0, 180))
            cleared = posted + timedelta(days=rng.randint(1, max(1, min(age or 1, 90)))) if status == "cleared" else None
            company = rng.choice(COMPANIES)
            document = f"{rng.randrange(1000000000, 9999999999)}"
            transaction = f"SAP-{i + 1:07d}"
            row = {
                "transaction_id": transaction,
                "posting_date": posted.isoformat(),
                "suspense_account": f"{account_no} - {account_name}",
                "owner": rng.choice(OWNERS),
                "category": rng.choice(CATEGORIES),
                "business_unit": f"BU-{rng.randint(1, 12):02d}",
                "amount": f"{amount:.2f}",
                "currency": currency,
                "status": status,
                "age_days": str(max(0, age)),
                "cleared_date": cleared.isoformat() if cleared else "",
                "reference": f"REF-{i + 1:08d}",
                "reason": rng.choice(REASONS),
                "source_system": "SAP ECC",
                "customer_vendor": f"{rng.choice(['Customer', 'Vendor'])}-{rng.randint(100000, 999999)}",
                "BUKRS": company,
                "BELNR": document,
                "GJAHR": str(posted.year),
                "BUZEI": str(rng.randint(1, 9)),
                "BUDAT": posted.isoformat(),
                "HKONT": account_no,
                "WAERS": currency,
                "DMBTR": f"{amount:.2f}",
                "WRBTR": f"{amount * Decimal(str(rng.uniform(0.85, 1.15))):.2f}",
                "SHKZG": rng.choice(["S", "H"]),
                "BLART": rng.choice(["SA", "DZ", "KR", "DR", "KZ"]),
                "XBLNR": f"EXT-{rng.randint(100000, 999999)}",
                "ZUONR": f"ASSIGN-{rng.randint(10000, 99999)}",
                "SGTXT": rng.choice(REASONS),
                "LIFNR": f"{rng.randint(100000, 999999)}" if rng.random() < 0.48 else "",
                "KUNNR": f"{rng.randint(100000, 999999)}" if rng.random() < 0.48 else "",
            }
            writer.writerow(row)
            account_key = row["suspense_account"]
            month_key = posted.strftime("%Y-%m")
            for bucket, key in ((totals, account_key), (by_month, month_key)):
                bucket[key]["transactions"] += 1
                bucket[key]["amount"] += amount
                if status in ("open", "investigating", "disputed"):
                    bucket[key]["open_amount"] += amount

    summary_path = output.with_name(output.stem + "_account_summary.csv")
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["suspense_account", "transactions", "amount", "open_amount"])
        writer.writeheader()
        for account, values in sorted(totals.items()):
            writer.writerow({"suspense_account": account, **{k: f"{v:.2f}" if isinstance(v, Decimal) else v for k, v in values.items()}})

    monthly_path = output.with_name(output.stem + "_monthly_summary.csv")
    with monthly_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["month", "transactions", "amount", "open_amount"])
        writer.writeheader()
        for month, values in sorted(by_month.items()):
            writer.writerow({"month": month, **{k: f"{v:.2f}" if isinstance(v, Decimal) else v for k, v in values.items()}})


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic SAP ECC suspense-account CSV files")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--output", type=Path, default=Path("data/sap_ecc_suspense_50000.csv"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be positive")
    generate(args.rows, args.output, args.seed)
    print(f"Generated {args.rows:,} detail rows: {args.output}")
    print(f"Generated account and monthly summaries beside the detail file")


if __name__ == "__main__":
    main()
