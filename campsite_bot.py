import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from dateutil.relativedelta import relativedelta
import traceback
from urllib.parse import urlencode

# Config
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
SMS_GATEWAY = "tmomail.net"  # T-Mobile SMS gateway

# Send error notifications to same Gmail address
ERROR_NOTIFICATION_EMAIL = GMAIL_ADDRESS

# Campsite API info
CAMPSITE_ID = "232463"  # Example campground ID
API_URL = "https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"

def validate_env_vars():
    missing = []
    for var in ["GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "PHONE_NUMBER"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

def get_valid_start_date():
    """Try first of this and next month; return the first one accepted by the API."""
    today = datetime.now()
    for offset in range(2):
        start_date = (today.replace(day=1) + relativedelta(months=offset)).strftime("%Y-%m-%dT00:00:00.000Z")
        url = API_URL.format(campground_id=CAMPSITE_ID)
        params = {"start_date": start_date}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            url_with_params = f"{url}?{urlencode(params)}"
            response = requests.get(url_with_params, headers=headers)
            if response.ok:
                return start_date
            else:
                print(f"Tried {start_date}, got {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error trying date {start_date}: {e}")
    raise Exception("No valid start date found (this month or next)")

def check_campsite_availability():
    start_date = get_valid_start_date()
    url = API_URL.format(campground_id=CAMPSITE_ID)
    params = {"start_date": start_date}
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, params=params, headers=headers)
    if not response.ok:
        print(f"API request failed: status={response.status_code} body={response.text}")
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
    msg['To'] = f"{PHONE_NUMBER}@{SMS_GATEWAY}"
    msg['Subject'] = "Campsite Availability Alert"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        raise

def send_error_email(subject, body):
    msg = MIMEText(body)
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = ERROR_NOTIFICATION_EMAIL
    msg['Subject'] = subject

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send error notification email: {e}")

def main():
    try:
        validate_env_vars()
        if check_campsite_availability():
            send_sms(f"Campsite {CAMPSITE_ID} has availability!")
            print("Availability found! SMS sent.")
        else:
            print("No availability found.")
    except Exception:
        error_trace = traceback.format_exc()
        print(f"Error occurred:\n{error_trace}")
        send_error_email("Campsite Checker Error", error_trace)

if __name__ == "__main__":
    main()