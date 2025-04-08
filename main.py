from pyairtable import Table
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
import base64
from collections import defaultdict

# === Airtable Config ===
AIRTABLE_TOKEN = "pata6JYRNuyGAi6J2.5d0e7306128fd75264b0c6e78720b7f1372c2ccd315ab591cbf2aeb7816b6262"
BASE_ID = "appJrWoXe5H2YZnmU"

# === Email Config ===
EMAIL_USER = "stefbot50@gmail.com"
EMAIL_TO = "stefbot50@gmail.com"
ENCODED_PASS = "cmRwcyBuYXJpIHlobHcgendkbA=="  # base64 for: rdps nari yhlw zwdl
SMTP_GMAIL_AUTH = base64.b64decode(ENCODED_PASS.encode()).decode()

# === Get This Week's Table Name ===
def get_week_table_name():
    today = datetime.today()
    start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end = start + timedelta(days=6)
    return f"{start.strftime('%m/%d')}-{end.strftime('%m/%d/%Y')}"

# === Filter Logic ===
def fetch_mf_faire_unchecked(table: Table):
    records = table.all()
    grouped = defaultdict(list)
    for r in records:
        fields = r.get("fields", {})
        code = fields.get("New Code", "")
        if not fields.get("MF/FAIRE Order", False) and not code.startswith("CA"):
            prefix = code[:2]
            if prefix in ["UT", "NV", "AZ", "TX", "FL"]:
                grouped[prefix].append(code)
    return grouped

def fetch_dna_unchecked_ca_only(table: Table):
    records = table.all()
    grouped = defaultdict(list)
    for r in records:
        fields = r.get("fields", {})
        code = fields.get("New Code", "")
        if code.startswith("CA") and not fields.get("DNA Order", False):
            grouped["CA"].append(code)
    return grouped

# === Format Grouped Email Body ===
def format_grouped_email(grouped_data):
    if not grouped_data:
        return "✅ All Orders Checked!"
    lines = []
    for state in sorted(grouped_data.keys()):
        lines.append(f"{state}:")
        lines.extend([f"- {code}" for code in grouped_data[state]])
        lines.append("")  # Empty line between groups
    return "\n".join(lines)

# === Email Sending ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, SMTP_GMAIL_AUTH)
        server.send_message(msg)

# === Main Logic ===
def run():
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()  # Monday = 0, Sunday = 6
    force_run = os.environ.get("FORCE_RUN", "false").lower() == "true"

    table_name = get_week_table_name()
    print(f"Checking table: {table_name}")
    table = Table(AIRTABLE_TOKEN, BASE_ID, table_name)

    ran_any = False

    # === CA DNA Orders – Tuesday at 12:00 PM ===
    if force_run or (weekday == 1 and hour == 12):
        result = fetch_dna_unchecked_ca_only(table)
        if result:
            body = "\n".join(result)
            send_email("DNA Check – CA Orders Unchecked", body)
            print(body)
            ran_any = True

    # === UT/NV/AZ MF/FAIRE Orders – Tuesday at 2:30 PM & 4:30 PM ===
    if force_run or (weekday == 1 and hour in [14, 16]):
        grouped_all = fetch_mf_faire_unchecked(table)
        filtered = {state: codes for state, codes in grouped_all.items() if state in ["UT", "NV", "AZ"]}
        if filtered:
            body = format_grouped_email(filtered)
            send_email("MF/FAIRE Check – UT/NV/AZ Orders", body)
            print(body)
            ran_any = True

    # === FL/TX MF/FAIRE Orders – Thursday at 2:30 PM & 4:30 PM ===
    if force_run or (weekday == 3 and hour in [14, 16]):
        grouped_all = fetch_mf_faire_unchecked(table)
        filtered = {state: codes for state, codes in grouped_all.items() if state in ["FL", "TX"]}
        if filtered:
            body = format_grouped_email(filtered)
            send_email("MF/FAIRE Check – FL/TX Orders", body)
            print(body)
            ran_any = True

    if not ran_any:
        print("Not a scheduled run time. Nothing to check.")
