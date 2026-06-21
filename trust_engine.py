import threading
import time

# Active sessions storage
active_sessions = {}


class TrustEngine:

    def __init__(self, username, device_known=True, normal_time=True):
        self.username = username
        self.trust_score = 50
        self.active = True

        # activity tracking
        self.is_active_now = False

        # session tracking
        self.session_runtime = 0
        self.idle_counter = 0
        self.sensitive_access_count = 0

        # contextual signals
        self.device_known = device_known
        self.normal_time = normal_time

        self.last_event = "Session initialized"

        self.apply_initial_trust()

    # ---------------- TRUST ZONE ----------------
    def get_trust_zone(self):
        if self.trust_score >= 70:
            return "TRUSTED"
        elif self.trust_score >= 40:
            return "MONITORED"
        elif self.trust_score >= 30:
            return "RESTRICTED"
        return "BLOCKED"

    # ---------------- INITIAL TRUST ----------------
    def apply_initial_trust(self):

        # authentication success
        self.trust_score += 20

        # device context
        if self.device_known:
            self.trust_score += 10
            self.last_event = "Known device authenticated"
        else:
            self.trust_score -= 20
            self.last_event = "Unknown device detected"

        # login time context
        if not self.normal_time:
            self.trust_score -= 10
            self.last_event = "Login outside office hours"

        # max operational trust = 80
        if self.trust_score > 80:
            self.trust_score = 80

    # ---------------- TRUST EVALUATION ----------------
    def evaluate(self):

        self.session_runtime += 1

        # -------- ACTIVE USER BEHAVIOR --------
        if self.is_active_now:
            self.last_event = "ACTIVE (User interaction detected)"

            # trust recovery up to 80 only
            if self.trust_score < 80:
                self.trust_score += 1

            self.is_active_now = False

        # -------- IDLE TRACKING --------
        self.idle_counter += 1

        # trust decay every 10 seconds idle
        if self.idle_counter >= 10 and self.idle_counter % 10 == 0:
            self.trust_score -= 5
            self.last_event = "Idle behaviour detected"

        # -------- AUTO LOGOUT: INACTIVITY --------
        if self.idle_counter >= 60:
            self.last_event = "Session terminated: inactivity (60s)"
            self.active = False
            return

        # -------- AUTO LOGOUT: EXCESSIVE SECURE ACCESS --------
        if self.sensitive_access_count > 3:
            self.last_event = "Security policy triggered: excessive secure access"
            self.active = False
            return

        # -------- AUTO LOGOUT: LOW TRUST --------
        if self.trust_score < 30:
            self.last_event = "Security policy triggered: trust score below threshold"
            self.active = False
            return

        # clamp trust range
        if self.trust_score < 0:
            self.trust_score = 0

        if self.trust_score > 80:
            self.trust_score = 80

    # ---------------- SOC DASHBOARD ----------------
    def render_soc_dashboard(self):

        # clear terminal
        print("\033[2J\033[H", end="")

        zone = self.get_trust_zone()

        risk = "LOW"
        if self.trust_score < 50:
            risk = "MEDIUM"
        if self.trust_score < 30:
            risk = "HIGH"

        print("=" * 55)
        print("        ZERO TRUST SECURITY OPERATIONS CONSOLE")
        print("=" * 55)
        print()
        print(f" User            : {self.username}")
        print(f" Session Runtime : {self.session_runtime}s")
        print(f" Idle Time       : {self.idle_counter}s")
        print(f" Trust Score     : {self.trust_score} / 80")
        print(f" Trust Zone      : {zone}")
        print(f" Status          : {'ACTIVE' if self.active else 'TERMINATED'}")
        print()
        print(f" Recent Event    : {self.last_event}")
        print(f" Risk Level      : {risk}")
        print()
        print("=" * 55)

    # ---------------- ENGINE LOOP ----------------
    def engine_loop(self):
        while self.active:
            time.sleep(1)
            self.evaluate()

    # ---------------- CONSOLE LOOP ----------------
    def console_loop(self):
        while self.active:
            time.sleep(1)  # SOC refresh interval
            self.render_soc_dashboard()

        # final state render
        self.render_soc_dashboard()

    # ---------------- START ENGINE ----------------
    def start(self):
        threading.Thread(target=self.engine_loop, daemon=True).start()
        threading.Thread(target=self.console_loop, daemon=True).start()


# ---------------- ENGINE STARTER ----------------
def start_engine(username, device_known=True, normal_time=True):

    engine = TrustEngine(username, device_known, normal_time)
    active_sessions[username] = engine

    engine.start()
    return engine