# Python script to process speedTest Tracker results and calculate rebate from downtime.

## Rebate Calculation logic (monthly)

- Slot size: 1 Hour
- Expected Total slots = 30 days x 24 Hours = 720 
- Unstable if any test in the hour is:
    - Status == Failed
    - Download < 25 Mbps
    - Upload < 25 Mbps
- Missing test results get status = complete
- Rebate = (unstable slots / total slots) * ₹580
