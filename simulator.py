# # simulator.py
# import pandas as pd
# import random
# from datetime import datetime, timedelta
# import numpy as np

# # === CONFIGURATION === #
# FILENAME = "hourly_water_levels.csv"
# START_LEVEL = 60          # starting water level
# WEEKS = 4                 # change this to 1, 2, 3, or 4 weeks
# HOURS = WEEKS * 7 * 24    # total hours to simulate

# def simulate_data():
#     data = []
#     now = datetime.now() - timedelta(days=WEEKS * 7)
#     level = START_LEVEL
#     rain_trigger = False
#     rain_hours = 0
#     rain_increase = 0

#     for i in range(HOURS):
#         hour_of_day = now.hour

#         # 🌞 Day-night sine wave fluctuation
#         daily_wave = 2 * np.sin((hour_of_day / 24) * 2 * np.pi)

#         # 📈 Slow long-term rising/falling trend
#         long_term_trend = i * 0.02  # slower rise

#         # 🌧️ Rainstorm simulation
#         if random.random() < 0.01:  # ~1% chance/hour
#             rain_trigger = True
#             rain_hours = random.randint(2, 6)
#             rain_increase = random.uniform(1.0, 3.0)

#         rain_boost = rain_increase if rain_trigger and rain_hours > 0 else 0
#         if rain_trigger and rain_hours > 0:
#             rain_hours -= 1
#         else:
#             rain_trigger = False
#             rain_increase = 0

#         # 🔁 Final water level update
#         level += daily_wave + 0.05 + random.uniform(-0.3, 0.4) + rain_boost
#         level = max(45, min(100, level))  # clamp between 45–100 cm

#         data.append({
#             "timestamp": now.strftime("%Y-%m-%d %H:%M"),
#             "level": round(level, 2)
#         })

#         now += timedelta(hours=1)

#     df = pd.DataFrame(data)
#     df.to_csv(FILENAME, index=False)
#     print(f"✅ Simulated {WEEKS} weeks of data ({HOURS} hours) saved to {FILENAME}")
#     return df

# if __name__ == "__main__":
#     simulate_data()

import random

# Base level and limits
BASE_LEVEL = 60   # starting normal level in cm
MAX_LEVEL = 100
MIN_LEVEL = 40

# Previous level stored globally (or you can keep it in a file or variable)
current_level = BASE_LEVEL

def simulate_level():
    global current_level

    # Simulate natural fluctuation
    change = random.uniform(-2.0, 3.5)  # small drop or rise

    # Occasionally simulate heavy rain (10% chance)
    if random.random() < 0.1:
        change += random.uniform(5.0, 12.0)

    # Occasionally simulate dry period (5% chance)
    if random.random() < 0.05:
        change -= random.uniform(4.0, 8.0)

    # Update and clip to min/max
    current_level += change
    current_level = max(MIN_LEVEL, min(current_level, MAX_LEVEL))

    return round(current_level, 2)
