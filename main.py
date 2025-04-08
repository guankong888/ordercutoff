from pyairtable import Table
from datetime import datetime, timedelta
import os

# === Airtable Config ===
AIRTABLE_TOKEN = os.environ["AIRTABLE_TOKEN"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]

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

# === Main Logic ===
def run():
    now = datetime.now()
    current_hour = now.hour
    current_weekday = now.weekday()  # Monday = 0, Sunday = 6

    table_name = get_week_table_name()
    print(f"Checking table: {table_name}")
    table = Table(AIRTABLE_TOKEN, BASE_ID, table_name)

    if current_weekday == 1 and current_hour == 12:
        # Tuesday @ noon: DNA check
        result = fetch_dna_unchecked_ca_only(table)
        print("🔍 Unchecked DNA Orders (CA only):")
        print("\n".join(result) or "None")
    elif current_weekday in [1, 3] and current_hour in [14, 16]:
        # Tuesday or Thursday @ 2:30pm or 4:30pm: MF/FAIRE check
        result = fetch_mf_faire_unchecked(table)
        print("🔍 Unchecked MF/FAIRE Orders (excluding CA):")
        print("\n".join(result) or "None")
    else:
        print("Not a scheduled run time. Nothing to check.")

if __name__ == "__main__":
    run()
