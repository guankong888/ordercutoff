from pyairtable import Table
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import base64

# === Airtable Config ===
AIRTABLE_TOKEN = "pata6JYRNuyGAi6J2.5d0e7306128fd75264b0c6e78720b7f1372c2ccd315ab591cbf2aeb7816b6262"
BASE_ID = "appJrWoXe5H2YZnmU"

# === Email Config ===
EMAIL_USER = "stefbot50@gmail.com"
EMAIL_TO = "stefbot50@gmail.com"
ENCODED_PASS = "cmRwcyBuYXJpIHlobHcgendkbA=="  # Base64 of: rdps nari yhlw zwdl
SMTP_GMAIL_AUTH = base64.b64decode(ENCODED_PASS.encode()).decode()

# === Get This Week's Table Name (Sunday–Saturday) ===
def get_week_table_name():
    today = datetime.today()
    start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end = start + timedelta(days=6)
    return f"{start.strftime('%m/%d')}-{end.strftime('%m/%d/%Y')}"

# === Filter Logic ===
def fetch_mf_faire_unchecked(table: Table):
    records = table.all()
    return [
        r.get("fields", {}).get("New Code", "")
        for r in records
        if not r.get("fields", {}).get("MF/FAIRE Order", False)
        and not r.get("fields", {}).get("New Code", "").startswith("CA")
    ]

def fetch_dna_unchecked_ca_only(table: Table):
    records = table.all()
    return [
        r.get("fields", {}).get("New Code", "")
        for r in records
        if r.get("fields", {}).get("New Code", "").startswith("CA")
        and not r.get("fields", {}).get("DNA Order", False)
    ]

# === Email Sending ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, SMTP_GMAIL_AUTH)
        server.send_message(msg)

# === Main Logic ===
def run():
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    force_run = True  # Set to False to re-enable schedule-only

    table_name = get_week_table_name()
    print(f"Checking table: {table_name}")
    table = Table(AIRTABLE_TOKEN, BASE_ID, table_name)

    if force_run or (weekday == 1 and hour == 12):
        result = fetch_dna_unchecked_ca_only(table)
        subject = "DNA Check – CA Orders Unchecked"
        body = "\n".join(result) or "✅ All CA DNA Orders Checked!"
        send_email(subject, body)
        print(body)

    if force_run or (weekday in [1, 3] and hour in [14, 16]):
        result = fetch_mf_faire_unchecked(table)
        subject = "MF/FAIRE Check – Unchecked Orders (Non-CA)"
        body = "\n".join(result) or "✅ All MF/FAIRE Orders Checked!"
        send_email(subject, body)
        print(body)

if __name__ == "__main__":
    run()
