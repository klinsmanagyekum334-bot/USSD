"""
Flask app that:
1. Exposes /ussd  -> the endpoint a real telco gateway (e.g. Africa's Talking)
   would call. Accepts sessionId, phoneNumber, serviceCode, text.
2. Exposes /simulate -> a JSON-friendly version for the browser-based
   phone simulator, so you can test the whole flow before going live.
3. Serves the simulator UI itself at "/".
"""

from flask import Flask, request, render_template, jsonify
from ussd_engine import handle_ussd

app = Flask(__name__)

# Very simple in-memory session store: { session_id: accumulated_text }
# A real gateway sends you the FULL accumulated text each time, so we
# don't strictly need this - but we keep it so the simulator can just
# send single keystrokes like a real phone would.
SESSIONS = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ussd", methods=["POST"])
def ussd():
    """
    Standard telco-gateway-style endpoint.
    Real gateways (Africa's Talking, etc.) POST form-encoded data with:
        sessionId, serviceCode, phoneNumber, text
    and expect a plain-text response starting with CON or END.
    """
    session_id = request.values.get("sessionId", "")
    phone_number = request.values.get("phoneNumber", "")
    text = request.values.get("text", "")

    response = handle_ussd(session_id, phone_number, text)
    return response, 200, {"Content-Type": "text/plain"}


@app.route("/simulate", methods=["POST"])
def simulate():
    """
    Simulator-friendly endpoint used by the phone UI.
    The browser sends one digit/choice at a time plus a session_id;
    we keep track of the accumulated '*'-joined text server-side,
    then run it through the exact same handle_ussd() the real gateway uses.
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    phone_number = data.get("phone_number", "0800000000")
    choice = data.get("choice", None)  # None on first load

    if choice is None:
        # Fresh session - user just dialed the code
        SESSIONS[session_id] = ""
    else:
        existing = SESSIONS.get(session_id, "")
        SESSIONS[session_id] = f"{existing}*{choice}" if existing else choice

    text = SESSIONS[session_id]
    response = handle_ussd(session_id, phone_number, text)

    is_end = response.startswith("END")
    message = response[4:]  # strip "CON " or "END " prefix

    if is_end:
        SESSIONS.pop(session_id, None)  # session closed, like a real phone

    return jsonify({"message": message, "ended": is_end})


if __name__ == "__main__":
    app.run(debug=True, port=5000)