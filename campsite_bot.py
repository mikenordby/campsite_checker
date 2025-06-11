import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Config
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "mikenordby9@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "6514345915")
SMS_GATEWAY = "tmomail.net"  # T-Mobile SMS gateway

# Campsite API info
CAMPSITE_ID = "232463"  # Example campground ID
API_URL = "https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"

def first_of_next_month():
    today = datetime.now()
    first_next_month = (today.replace(day=1) + relativedelta(months=1)).strftime("%Y-%m-%d")
    return first_next_month

def check_campsite_availability():
    start_date = first_of_next_month()
    url = API_URL.format(campground_id=CAMPSITE_ID)
    params = {"start_date": start_date}
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    campsites = data.get("campsites", {})
    available = False

    for campsite_id, campsite_info in campsites.items():
        availabilities = campsite_info.get("availabilities", {})
        status = campsite_info.get("status", "")
        if availabilities != {} or status.lower() == "available":
            available = True
            break
    return available

def send_sms(message):
    msg = MIMEText(message)
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = f"{YOUR_PHONE_NUMBER}@{SMS_GATEWAY}"
    msg['Subject'] = "Campsite Availability Alert"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)

def main():
    try:
        if check_campsite_availability():
            send_sms(f"Campsite {CAMPSITE_ID} has availability!")
            print("Availability found! SMS sent.")
        else:
            print("No availability found.")
    except Exception as e:
        print(f"Error checking availability: {e}")

if __name__ == "__main__":
    main()