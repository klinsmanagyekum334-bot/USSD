# USSD Menu Simulator (Anasdata example)

Build and test your USSD menu logic in a browser before connecting to any telco.

## Structure

- `ussd_engine.py` — the actual menu logic (network-agnostic, pure Python).
  This is the only file you need to edit to change menu text, add options,
  or hook up real APIs (payments, provisioning, etc).
- `app.py` — Flask server with two routes:
  - `/ussd` — the endpoint you'll register with a real telco/aggregator later
    (Africa's Talking, Infobip, etc.). Speaks their standard protocol:
    receives `sessionId`, `phoneNumber`, `serviceCode`, `text` and returns
    plain text starting with `CON` (continue) or `END` (terminate).
  - `/simulate` — JSON version used by the browser simulator.
- `templates/index.html` — a phone-shaped web UI that mimics the native
  USSD dialog, so you can click through your menu exactly like a user would.

## Run it

```bash
pip install flask
python3 app.py