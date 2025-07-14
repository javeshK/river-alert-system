# app.py

from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Needed to run matplotlib in Flask
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

app = Flask(__name__)

CSV_FILE = "hourly_water_levels.csv"
GRAPH_FILE = "static/graph.png"
DANGER_LEVEL = 80

# 📈 Create a line plot of the water level
def create_plot(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['level'], label="Water Level", color="blue")
    plt.axhline(y=DANGER_LEVEL, color='red', linestyle='--', label="Danger Level (80 cm)")
    plt.title("Water Level - Last 7 Days (Hourly)")
    plt.xlabel("Time")
    plt.ylabel("Water Level (cm)")
    plt.legend()
    plt.tight_layout()

    if not os.path.exists("static"):
        os.makedirs("static")
    plt.savefig(GRAPH_FILE)
    plt.close()

# 🔮 Predict when level will exceed the danger line
def predict_exceed_time(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour_index'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600

    x = df['hour_index'].values
    y = df['level'].values

    if len(set(y)) <= 1:
        return "Water level is constant."
    
    try:
        m, c = np.polyfit(x, y, 1)
        if m <= 0:
            return "Water level is decreasing. No danger."

        hour_to_cross = (DANGER_LEVEL - c) / m
        predicted_time = df['timestamp'].min() + timedelta(hours=hour_to_cross)

        if hour_to_cross < x[-1]:
            return f"Already exceeded on {predicted_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"Will exceed danger level on {predicted_time.strftime('%Y-%m-%d %H:%M')}"
    except:
        return "Prediction error."

@app.route("/")
def home():
    status_msg = request.args.get('status')
    df = pd.read_csv(CSV_FILE)
    latest = df.iloc[-1]
    create_plot(df)
    prediction = predict_exceed_time(df)

    return render_template("index.html",
                           level=latest['level'],
                           time=latest['timestamp'],
                           prediction=prediction,
                           graph_path=GRAPH_FILE,
                           status_msg=status_msg)

ALERT_FILE = "manual_alert_log.csv"

@app.route("/submit", methods=["POST"])
def submit_alert():
    level = request.form.get("manual_level")
    if level:
        level = float(level)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Danger" if level >= DANGER_LEVEL else "Safe"

        alert_data = pd.DataFrame([{
            "timestamp": now,
            "manual_level": level,
            "status": status
        }])

        if not os.path.exists(ALERT_FILE):
            alert_data.to_csv(ALERT_FILE, index=False)
        else:
            alert_data.to_csv(ALERT_FILE, mode='a', header=False, index=False)

        print(f"✅ Manual alert saved: {level} cm - {status} at {now}")
        return redirect(url_for('home', status=status))

    return redirect(url_for('home'))
