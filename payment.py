"""
Payment module - handles initiating Mobile Money charges via PaySwitch
(TheTeller) and sending SMS notifications via Arkesel.

Kept separate from ussd_engine.py so that if you ever switch providers
again, you only need to change this one file.

SETUP REQUIRED (PaySwitch / TheTeller):
1. Create a merchant account: https://www.payswitch.com.gh/
2. From your TheTeller merchant dashboard, get:
     - your API username and API key (used for Basic Auth)
     - your Merchant ID
3. Set these as environment variables (never hardcode them in real code):
     export PAYSWITCH_API_USER="your_api_username"
     export PAYSWITCH_API_KEY="your_api_key"
     export PAYSWITCH_MERCHANT_ID="your_merchant_id"
     export PAYSWITCH_WEBHOOK_SECRET="your_webhook_signing_secret"
4. Use the sandbox host (test.theteller.net) while testing, and switch to
   the live host (theteller.net) only once you're ready to charge real
   customers. Toggle with the PAYSWITCH_LIVE environment variable:
     export PAYSWITCH_LIVE="true"   # use production host
5. In your PaySwitch dashboard, set your webhook/callback URL to:
     https://yourdomain.com/payment-callback

IMPORTANT: PaySwitch's exact webhook payload shape and signature header
name can change between merchant accounts/products. Confirm both against
your own dashboard docs before going live - the verify_webhook_signature()
function below is written generically (HMAC-SHA512 over the raw body) and
may need the header name adjusted to match what PaySwitch actually sends you.
"""

import os
import uuid
import requests

PAYSWITCH_API_USER = os.environ.get("PAYSWITCH_API_USER", "")
PAYSWITCH_API_KEY = os.environ.get("PAYSWITCH_API_KEY", "")
PAYSWITCH_MERCHANT_ID = os.environ.get("PAYSWITCH_MERCHANT_ID", "")
PAYSWITCH_WEBHOOK_SECRET = os.environ.get("PAYSWITCH_WEBHOOK_SECRET", "")

PAYSWITCH_LIVE = os.environ.get("PAYSWITCH_LIVE", "false").lower() == "true"
PAYSWITCH_HOST = "https://theteller.net" if PAYSWITCH_LIVE else "https://test.theteller.net"
PAYSWITCH_CHARGE_URL = f"{PAYSWITCH_HOST}/v1.1/transaction/process"

# processing_code for a mobile money debit/charge (collecting from a customer)
MOMO_CHARGE_PROCESSING_CODE = "000200"

# PaySwitch's "r-switch" network codes (Ghana)
NETWORK_SWITCH_CODES = {
    "MTN": "MTN",
    "TELECEL": "VDF",   # Telecel Cash (formerly Vodafone Cash)
}


# ============================================================
# ARKESEL SMS SETTINGS
# ============================================================

ARKESEL_API_KEY = os.environ.get("ARKESEL_API_KEY", "")
ARKESEL_SENDER_ID = os.environ.get("ARKESEL_SENDER_ID", "EasyData")

# This is the SMS API URL shown in your Arkesel account
ARKESEL_URL = "https://sms.arkesel.com/sms/api"


def _basic_auth_header() -> str:
    import base64
    raw = f"{PAYSWITCH_API_USER}:{PAYSWITCH_API_KEY}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("utf-8")


def initiate_momo_charge(
    phone_number: str,
    amount_ghs: float,
    network: str,
    reference: str
) -> dict:
    """
    Sends a charge request to PaySwitch (TheTeller), which triggers the
    MoMo approval prompt on the customer's phone.

    Returns a dict with at least a 'status' key (True/False) and 'message'.
    A True status here means the charge request was ACCEPTED for processing,
    not that the customer has paid yet - final confirmation still comes via
    your /payment-callback webhook.
    """

    if not (
        PAYSWITCH_API_USER
        and PAYSWITCH_API_KEY
        and PAYSWITCH_MERCHANT_ID
    ):
        return {
            "status": False,
            "message": "Payment provider not configured (missing credentials)."
        }

    switch_code = NETWORK_SWITCH_CODES.get(network)

    if not switch_code:
        return {
            "status": False,
            "message": f"Unsupported network: {network}"
        }

    # PaySwitch expects amount as a 12-digit zero-padded string, in pesewas
    # (i.e. GHS 5.00 -> 500 pesewas -> "000000000500")
    amount_pesewas = int(round(amount_ghs * 100))
    amount_str = str(amount_pesewas).zfill(12)

    # transaction_id must be unique and, per their examples, numeric.
    # Derive a 12-digit numeric ID from our own order reference.
    numeric_txn_id = str(abs(hash(reference)) % (10 ** 12)).zfill(12)

    headers = {
        "Content-Type": "application/json",
        "Authorization": _basic_auth_header(),
        "Cache-Control": "no-cache",
    }

    payload = {
        "amount": amount_str,
        "processing_code": MOMO_CHARGE_PROCESSING_CODE,
        "transaction_id": numeric_txn_id,
        "desc": "Data bundle purchase",
        "merchant_id": PAYSWITCH_MERCHANT_ID,
        "subscriber_number": phone_number,
        "r-switch": switch_code,
    }

    try:
        response = requests.post(
            PAYSWITCH_CHARGE_URL,
            json=payload,
            headers=headers,
            timeout=15
        )

        data = response.json()

        # PaySwitch responses typically include a "code"
        # (e.g. "000" for success/accepted).
        code = str(data.get("code", ""))

        success = response.ok and code in ("000", "200")

        return {
            "status": success,
            "message": (
                data.get("reason")
                or data.get("message")
                or "Unknown response from payment provider."
            ),
            "raw": data,
        }

    except requests.RequestException as e:
        return {
            "status": False,
            "message": f"Payment request failed: {e}"
        }

    except ValueError:
        return {
            "status": False,
            "message": (
                "Payment provider returned an unexpected "
                "(non-JSON) response."
            )
        }


def verify_webhook_signature(
    request_body: bytes,
    signature_header: str
) -> bool:
    """
    Verifies that a webhook actually came from PaySwitch, using HMAC-SHA512
    over the raw request body with your webhook signing secret.

    CONFIRM WITH PAYSWITCH: the exact header name they send the signature in
    (this assumes something like 'x-payswitch-signature') and whether the
    hashing scheme matches what's documented for your specific account -
    these details can vary by merchant integration.
    """

    import hmac
    import hashlib

    if not PAYSWITCH_WEBHOOK_SECRET:
        return False

    computed_signature = hmac.new(
        PAYSWITCH_WEBHOOK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(
        computed_signature,
        signature_header or ""
    )


# ============================================================
# ARKESEL SMS
# ============================================================

def send_sms(recipient: str, message: str) -> dict:
    """
    Sends an SMS via Arkesel.

    Uses the SMS API format shown in the Arkesel account:

    https://sms.arkesel.com/sms/api
        ?action=send-sms
        &api_key=YOUR_API_KEY
        &to=PHONE_NUMBER
        &from=SENDER_ID
        &sms=YOUR_MESSAGE
    """

    if not ARKESEL_API_KEY:
        return {
            "status": False,
            "message": "SMS provider not configured (missing API key)."
        }

    # Parameters exactly according to the SMS API shown
    # in your Arkesel account.
    params = {
        "action": "send-sms",
        "api_key": ARKESEL_API_KEY,
        "to": recipient,
        "from": ARKESEL_SENDER_ID,
        "sms": message,
    }

    try:
        response = requests.get(
            ARKESEL_URL,
            params=params,
            timeout=15
        )

        # Arkesel's API response may be plain text rather than JSON,
        # so we keep the raw response.
        response_text = response.text.strip()

        return {
            "status": response.ok,
            "message": response_text or "SMS request completed.",
            "raw": response_text,
        }

    except requests.RequestException as e:
        return {
            "status": False,
            "message": f"SMS request failed: {e}"
        }
