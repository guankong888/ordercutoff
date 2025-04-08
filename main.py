from pyairtable import Table
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText

# === Airtable Config ===
AIRTABLE_TOKEN = os.environ["AIRTABLE_TOKEN"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]

# === Email Config ===
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = "zwzfdtvucxjnbkwp"
EMAIL_TO = os.environ["EMAIL_TO"]

# === Get This Week's Table Name (Sunday–Saturday) ===
def get_week_table_name():
    today = datetime.today()
    start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end = start + timedelta(days=6)
    return f"{start.strftime('%m/%d')}-{end.strftime('%m/%d/%Y')}"

# === Filter Logic ===
def fetch_mf_faire_unchecked(table: Table):
    records = table.all()
    unchecked = []
    for r in records:
        fields = r.get("fields", {})
        new_code = fields.get("New Code", "")
        if not fields.get("MF/FAIRE Order", False) and not new_code.startswith("CA"):
            unchecked.append(new_code)
    return unchecked

def fetch_dna_unchecked_ca_only(table: Table):
    records = table.all()
    unchecked = []
    for r in records:
        fields = r.get("fields", {})
        new_code = fields.get("New Code", "")
        if new_code.startswith("CA") and not fields.get("DNA Order", False):
            unchecked.append(new_code)
    return unchecked

# === Email Sending ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# === Main Logic ===
def run():
    now = datetime.now()
    current_hour = now.hour
    current_weekday = now.weekday()  # Monday = 0, Sunday = 6
    force_run = os.environ.get("FORCE_RUN", "false").lower() == "true"

    table_name = get_week_table_name()
    print(f"Checking table: {table_name}")
    table = Table(AIRTABLE_TOKEN, BASE_ID, table_name)

    ran_anything = False

    if force_run or (current_weekday == 1 and current_hour == 12):
        result = fetch_dna_unchecked_ca_only(table)
        subject = "DNA Check – CA Orders Unchecked"
        body = "\n".join(result) or "✅ All CA DNA Orders Checked!"
        send_email(subject, body)
        print(body)
        ran_anything = True

    if force_run or (current_weekday in [1, 3] and current_hour in [14, 16]):
        result = fetch_mf_faire_unchecked(table)
        subject = "MF/FAIRE Check – Unchecked Orders (Non-CA)"
        body = "\n".join(result) or "✅ All MF/FAIRE Orders Checked!"
        send_email(subject, body)
        print(body)
        ran_anything = True

    if not ran_anything:
        print("Not a scheduled run time. Nothing to check.")

if __name__ == "__main__":
    run()
