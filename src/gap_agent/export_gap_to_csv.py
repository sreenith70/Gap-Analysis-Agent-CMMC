import json
import csv
from pathlib import Path

INPUT_PATH = Path("outputs/gap_report.json")
OUTPUT_PATH = Path("outputs/gap_report.csv")

def export_to_csv():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"JSON input not found at: {INPUT_PATH}")
    
    with open(INPUT_PATH, "r", encoding="utf-8") as infile:
        gap_data = json.load(infile)

    keys = ["control_id", "status", "confidence_score", "explanation", "matched_text"]
    
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=keys)
        writer.writeheader()
        for row in gap_data:
            writer.writerow({k: row.get(k, "") for k in keys})

    print(f"Exported gap report to: {OUTPUT_PATH.resolve()}")

if __name__ == "__main__":
    export_to_csv()
