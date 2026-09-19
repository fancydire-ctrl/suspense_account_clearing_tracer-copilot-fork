# Synthetic SAP ECC suspense-account dataset

Run from the repository root:

```bash
python3 data/generate_sap_ecc_dataset.py
```

This creates exactly 50,000 deterministic, synthetic detail rows at:

- `data/sap_ecc_suspense_50000.csv` — load this file with the dashboard's **Load CSV** button.
- `data/sap_ecc_suspense_50000_account_summary.csv` — account-level usage totals and open value.
- `data/sap_ecc_suspense_50000_monthly_summary.csv` — monthly transaction count, total value, and open value.

The detail file contains the dashboard's canonical fields plus generic SAP ECC-style fields such as `BUKRS`, `BELNR`, `GJAHR`, `BUZEI`, `BUDAT`, `HKONT`, `WAERS`, `DMBTR`, `WRBTR`, `SHKZG`, `BLART`, `XBLNR`, `ZUONR`, `SGTXT`, `LIFNR`, and `KUNNR`. Values are synthetic and must not be treated as production SAP data.

The generator uses a fixed seed so test runs are repeatable. To generate another size:

```bash
python3 data/generate_sap_ecc_dataset.py --rows 1000 --output data/sample.csv
```

The generated detail data spans two calendar years, allowing the existing dashboard's daily activity view to be used for daily monitoring and the generated monthly summary to be used for monthly reporting or validation.
