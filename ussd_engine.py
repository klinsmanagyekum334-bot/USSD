"""
USSD Menu Engine
----------------
Follows the Africa's Talking / standard telco USSD convention:

- Every request carries: sessionId, phoneNumber, serviceCode, text
- `text` accumulates the user's choices across the session, separated by '*'
    e.g. text = ""          -> user just dialed the code (first screen)
         text = "1"         -> user chose option 1 on first screen
         text = "1*2"       -> then chose option 2 on the next screen
- Response must start with:
    "CON " -> continue session, show more menu, wait for next input
    "END " -> terminate session, this is the final message shown

This file has ZERO dependency on Flask/HTTP so it can be unit-tested on
its own, reused in a CLI, or dropped behind any web framework.
"""

import uuid
from payment import initiate_momo_charge

NETWORKS = {
    "1": "MTN",
    "2": "TELECEL",
}

BUNDLES = {
    "1": "1GB",
    "2": "2GB",
    "3": "3GB",
    "4": "4GB",
    "5": "5GB",
    "6": "10GB",
    "7": "20GB",
    "8": "50GB",
    "9": "100GB",
}

BUNDLE_PRICES = {
    "1GB": 5.00,
    "2GB": 9.00,
    "3GB": 13.00,
    "4GB": 17.00,
    "5GB": 20.00,
    "10GB": 38.00,
    "20GB": 70.00,
    "50GB": 160.00,
    "100GB": 300.00,
}

SUPPORT_CONTACT = " 0531715785 "

ORDERS = {}


def handle_ussd(session_id: str, phone_number: str, text: str) -> str:
    parts = text.split("*") if text else []

    if text == "":
        return (
            "CON      EASY DATA BUNDLE. \nDATA TAKES FEW MINUTES "
            "\n"
            "1. Buy data bundle\n"
            "2. Contact support"
        )

    if parts[0] == "1":

        if len(parts) == 1:
            menu = "\n".join(f"{k}. {v}" for k, v in NETWORKS.items())
            return f"CON Select network:\n{menu}"

        network_choice = parts[1]
        if network_choice not in NETWORKS:
            return "END Invalid network selection. Please try again."

        if len(parts) == 2:
            menu = "\n".join(f"{k}. {size}" for k, size in BUNDLES.items())
            return f"CON Select bundle for {NETWORKS[network_choice]}:\n{menu}"

        bundle_choice = parts[2]
        if bundle_choice not in BUNDLES:
            return "END Invalid bundle selection. Please try again."

        # Screen 3: confirm purchase before triggering payment
        if len(parts) == 3:
            size = BUNDLES[bundle_choice]
            network = NETWORKS[network_choice]
            return (
                f"CON Confirm purchase:\n{size} {network} data bundle\n"
                f"1. Confirm\n"
                f"2. Cancel"
            )

        confirm_choice = parts[3]

        if confirm_choice == "2":
            return "END Purchase cancelled."

        if confirm_choice != "1":
            return "END Invalid option. Please dial the code again."

        # User confirmed: trigger the MoMo payment prompt
        if len(parts) == 4:
            size = BUNDLES[bundle_choice]
            network = NETWORKS[network_choice]
            price = BUNDLE_PRICES.get(size)

            if price is None:
                return "END This bundle is temporarily unavailable. Please try again later."

            order_ref = f"EASYDATA-{uuid.uuid4().hex[:10]}"
            ORDERS[order_ref] = {
                "phone_number": phone_number,
                "network": network,
                "bundle_size": size,
                "amount": price,
                "status": "pending",
            }

            result = initiate_momo_charge(
                phone_number=phone_number,
                amount_ghs=price,
                network=network,
                reference=order_ref,
            )

            if not result["status"]:
                return f"END Could not start payment: {result['message']}. Please try again."

            # Charge accepted - MoMo PIN prompt goes to the customer.
            # Your /payment-callback webhook fires once approved, and
            # THAT is what triggers the SMS to your support number.
            return (
                f"END A payment prompt has been sent to your phone.\n"
                f"Approve it with your MoMo PIN to receive your {size} {network} bundle.\n"
                f"Delivery takes 5-30 minutes. Order ref: {order_ref}"
            )

    if parts[0] == "2":
        return f"END {SUPPORT_CONTACT}"

    return "END Invalid option selected. Please dial the code again."