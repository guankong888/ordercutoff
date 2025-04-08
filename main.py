from pyairtable import Table
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
import base64

# === Airtable Config ===
AIRTABLE_TOKEN = "pata6JYRNuyGAi6J2.5d0e7306128fd75264b0c6e78720b7f1372c2ccd315ab591cbf2aeb7816b6262"
BASE_ID = "appJrWoXe5H2YZnmU"

# === Email Config ===
EMAIL_USER = "stefbot50@gmail.com"
EMAIL_TO = "stefbot50@gmail.com"  # <- Replace with the recipient's email
ENCODED_PASS = "cmRwcyBuYXJpIHlobHcgendkbA=="  # base64 of your app password
SMTP_GMAIL_AUTH = base64.b64decode(ENCODED_PASS.encode()).decode()

# === Get This Week's Table Name (Sunday–Saturday) ===
def get_week_table_name():
    today = datetime.today()
    start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end = start + timedelta(days=6)
    return f"{start.strftime('%m/%d')}-{end.strftime('%m/%d/%Y')}"

# === Filtering Logic ===
def fetch_dna_unchecked_ca_only(table: Table):
    records = table.all()
    return [
        fields.get("New Code", "")
        for r in records
        if (fields := r.get("fields", {})).get("New Code", "").startswith("CA")
        and not fields.get("DNA Order", False)
    ]

def fetch_mf_faire_by_states(table: Table, states: list):
    records = table.all()
    return [
        fields.get("New Code", "")
        for r in records
        if (fields := r.get("fields", {})).get("New Code", "").split()[0][:2] in states
        and not fields.get("MF/FAIRE Order", False)
        and not fields.get("New Code", "").startswith("CA")
    ]

# === Email Sending ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, SMTP_GMAIL_AUTH)
        server.send_message(msg)

# === Scheduler State Check ===
def get_schedule_status():
    now = datetime.now()
    weekday = now.weekday()  # Monday = 0
    hour = now.hour
    minute = now.minute
    return {
        "CA_DNA": (weekday == 1 and hour == 12),
        "MF_FAIRE_UT_NV_AZ": (weekday == 1 and (hour, minute) in [(14, 30), (16, 30)]),
        "MF_FAIRE_FL_TX": (weekday == 3 and (hour, minute) in [(14, 30), (16, 30)]),
    }

# === Main Execution ===
def run():
    force_run = os.environ.get("FORCE_RUN", "false").lower() == "true"
    table_name = get_week_table_name()
    print(f"Checking table: {table_name}")
    table = Table(AIRTABLE_TOKEN, BASE_ID, table_name)
    status = get_schedule_status()
    ran_anything = False

    if force_run or status["CA_DNA"]:
        result = fetch_dna_unchecked_ca_only(table)
        subject = "DNA Check – CA Orders Unchecked"
        body = "\n".join(result) if result else "✅ All CA DNA Orders Checked!"
        send_email(subject, body)
        print(body)
        ran_anything = True

    if force_run or status["MF_FAIRE_UT_NV_AZ"]:
        result = fetch_mf_faire_by_states(table, ["UT", "NV", "AZ"])
        subject = "MF/FAIRE Check – Unchecked UT/NV/AZ Orders"
        body = "\n".join(result) if result else "✅ All UT/NV/AZ Orders Checked!"
        send_email(subject, body)
        print(body)
        ran_anything = True

    if force_run or status["MF_FAIRE_FL_TX"]:
        result = fetch_mf_faire_by_states(table, ["FL", "TX"])
        subject = "MF/FAIRE Check – Unchecked FL/TX Orders"
        body = "\n".join(result) if result else "✅ All FL/TX Orders Checked!"
        send_email(subject, body)
        print(body)
        ran_anything = True

    if not ran_anything:
        print("Not a scheduled run time. Nothing to check.")

if __name__ == "__main__":
    run()
