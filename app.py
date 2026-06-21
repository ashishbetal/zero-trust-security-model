from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from trust_engine import start_engine, active_sessions
from datetime import datetime

app = Flask(__name__)
app.secret_key = "zerotrustsecret"


# ---------------- LOGIN PAGE ----------------
@app.route("/")
def home():
    return render_template("login.html")


# ---------------- LOGIN HANDLER ----------------
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    # -------- ADMIN LOGIN --------
    if username == "admin" and password == "admin123":
        session["user"] = "admin"
        session["role"] = "admin"
        return redirect(url_for("admin_dashboard"))

    # -------- EMPLOYEE LOGIN --------
    if username == "alex" and password == "1234":

        session["user"] = username
        session["role"] = "employee"

        # contextual signals
        user_agent = request.headers.get("User-Agent", "")
        device_known = "Chrome" in user_agent

        hour = datetime.now().hour
        normal_time = 8 <= hour <= 20

        # start trust engine
        start_engine(username, device_known, normal_time)

        return redirect(url_for("dashboard"))

    return "Invalid credentials"


# ---------------- EMPLOYEE DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if session.get("role") != "employee":
        return redirect(url_for("home"))

    username = session["user"]

    if username not in active_sessions or not active_sessions[username].active:
        session.clear()
        return redirect(url_for("home"))

    return render_template("dashboard.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    sessions = []

    for username, engine in active_sessions.items():
        sessions.append({
            "username": username,
            "trust": engine.trust_score,
            "zone": engine.get_trust_zone(),
            "idle": engine.idle_counter,
            "status": "ACTIVE" if engine.active else "TERMINATED"
        })

    return render_template("admin.html", sessions=sessions)


# ---------------- API: SESSION DATA (JSON) ----------------
@app.route("/api/sessions")
def api_sessions():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    sessions = []
    for username, engine in active_sessions.items():
        zone = engine.get_trust_zone()
        risk = "LOW"
        if engine.trust_score < 50:
            risk = "MEDIUM"
        if engine.trust_score < 30:
            risk = "HIGH"
        sessions.append({
            "username": username,
            "trust": engine.trust_score,
            "zone": zone,
            "idle": engine.idle_counter,
            "runtime": engine.session_runtime,
            "last_event": engine.last_event,
            "risk": risk,
            "status": "ACTIVE" if engine.active else "TERMINATED"
        })

    return jsonify({"sessions": sessions})


# ---------------- SECURE RESOURCE ----------------
@app.route("/secure")
def secure():

    if session.get("role") != "employee":
        return redirect(url_for("home"))

    username = session["user"]

    if username in active_sessions:
        engine = active_sessions[username]
        engine.sensitive_access_count += 1
        engine.idle_counter = 0
        engine.is_active_now = True

    return redirect(url_for("dashboard"))


# ---------------- ACTIVITY HEARTBEAT ----------------
@app.route("/activity", methods=["POST"])
def activity():

    if session.get("role") != "employee":
        return ("", 204)

    username = session["user"]

    if username in active_sessions:
        engine = active_sessions[username]
        engine.idle_counter = 0
        engine.is_active_now = True

    return ("", 204)


# ---------------- ADMIN REVOKE SESSION ----------------
@app.route("/revoke/<username>")
def revoke(username):

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    if username in active_sessions:
        active_sessions[username].active = False

    return redirect(url_for("admin_dashboard"))


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    username = session.get("user")

    if username in active_sessions:
        active_sessions[username].active = False
        del active_sessions[username]

    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True) 