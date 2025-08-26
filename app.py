
#  app.py

from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os, smtplib, math
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ================= Flask App =================
app = Flask(__name__)
load_dotenv()

# ================= Files =================
CSV_FILE = "hourly_water_levels.csv"
GRAPH_FILE = "static/graph.png"
USERS_FILE = "users.csv"
ALERT_FILE = "manual_alert_log.csv"

#  City danger levels
CITY_DANGER = {
    "Varanasi": 72,
    "Haridwar": 293,
    "Prayagraj": 84
}

# ================= Email Config =================
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email(to_email, subject, body):
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            print("❌ Missing EMAIL_USER or EMAIL_PASS in .env")
            return
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Email sent to {to_email}")

    except Exception as e:
        print(f"❌ Email error: {e}")


def notify_users(city, level, timestamp):
    if os.path.exists(USERS_FILE):
        users = pd.read_csv(USERS_FILE)
        for _, user in users.iterrows():
            subscribed_cities = [c.strip().lower() for c in str(user["cities"]).split(",")]
            if city.lower() in subscribed_cities:
                subject = f"🚨 Water Level Alert for {city}"
                body = f"""
                Dear {user['name']},

                The water level in {city} has crossed the danger threshold.

                Current Level: {level} m
                Time: {timestamp}
                Danger Level: {CITY_DANGER[city]} m

                Please stay safe.
                """
                send_email(user["email"], subject, body)


#  Create Graph
def create_plot(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    plt.figure(figsize=(10, 6))
    plt.plot(df["timestamp"], df["level"], label="Water Level", color="blue")
    plt.axhline(y=80, color="red", linestyle="--", label="Sample Danger Level (80 cm)")
    plt.title("Water Level - Last 7 Days (Hourly)")
    plt.xlabel("Time")
    plt.ylabel("Water Level (cm)")
    plt.legend()
    plt.tight_layout()

    if not os.path.exists("static"):
        os.makedirs("static")
    plt.savefig(GRAPH_FILE)
    plt.close()


# 📉 Prediction Model
def predict_exceed_time(df):
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour_index"] = (df["timestamp"] - df["timestamp"].min()).dt.total_seconds() / 3600

        x = df["hour_index"].values
        y = df["level"].values

        if len(set(y)) <= 1:
            return "Water level is constant."

        if y[-1] > y[0]:
            return "Water level is rising. Recession model not applicable."

        log_y = np.log(y)
        k, log_Q0 = np.polyfit(x, log_y, 1)
        Q0 = math.exp(log_Q0)

        if 80 >= Q0:
            return "Already below danger."

        t_exceed = -math.log(80 / Q0) / k
        predicted_time = df["timestamp"].min() + timedelta(hours=t_exceed)
        return f"Expected safe after {predicted_time.strftime('%Y-%m-%d %H:%M')}"
    except:
        return "Prediction error."


# ================= Routes =================
@app.route("/")
def home():
    status_msg = request.args.get("status")

    if not os.path.exists(CSV_FILE):
        return render_template("index.html", graph_path=None, status_msg="No data file found", 
                               city_danger=CITY_DANGER, level=None, time=None, prediction=None)

    df = pd.read_csv(CSV_FILE)
    latest = df.iloc[-1]
    create_plot(df)
    prediction = predict_exceed_time(df)

    return render_template("index.html",
                           graph_path=GRAPH_FILE,
                           level=latest["level"],
                           time=latest["timestamp"],
                           prediction=prediction,
                           status_msg=status_msg,
                           city_danger=CITY_DANGER)


@app.route("/submit", methods=["POST"])
def submit_alert():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []

    for city, danger_level in CITY_DANGER.items():
        level = request.form.get(city.lower() + "_level")
        if level:
            level = float(level)
            status = "Danger" if level >= danger_level else "Safe"

            alerts.append({
                "city": city,
                "timestamp": now,
                "manual_level": level,
                "status": status
            })

            if status == "Danger":
                notify_users(city, level, now)

    if alerts:
        alert_df = pd.DataFrame(alerts)
        if not os.path.exists(ALERT_FILE):
            alert_df.to_csv(ALERT_FILE, index=False)
        else:
            alert_df.to_csv(ALERT_FILE, mode="a", header=False, index=False)

    return redirect(url_for("home", status="Alerts processed"))


@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    selected_cities = request.form.getlist("cities")

    if not name or not email or not selected_cities:
        return redirect(url_for("home", status="Please fill all fields"))

    cities_str = ",".join(selected_cities)

    user_data = pd.DataFrame([{
        "name": name,
        "email": email,
        "cities": cities_str
    }])

    if not os.path.exists(USERS_FILE):
        user_data.to_csv(USERS_FILE, index=False)
    else:
        user_data.to_csv(USERS_FILE, mode="a", header=False, index=False)

    print(f"✅ New user added: {name}, {email}, Cities: {cities_str}")
    return redirect(url_for("home", status="Signup successful!"))


@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
