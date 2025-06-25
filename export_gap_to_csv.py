# export_gap_to_csv.py
import json
import csv
import os
from pathlib import Path
from datetime import datetime

def export_gap_report_to_csv():
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = Path(f"outputs/gap_report_{timestamp}.csv")
    input_path = Path("outputs/gap_report.json")
    
    try:
        # Validate input file exists
        if not input_path.exists():
            raise FileNotFoundError(f"ERROR: Input file not found: {input_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load JSON
        print(f"INFO: Loading JSON report from: {input_path}")
        with input_path.open("r", encoding="utf-8") as f:
            report = json.load(f)
        
        results = report.get("results", [])
        if not isinstance(results, list) or not results:
            raise ValueError("ERROR: No valid 'results' found in the JSON report.")
        
        # Define headers
        headers = ["control_id", "status", "confidence_score", "matched_text", "explanation"]
        
        # Write CSV
        print(f"INFO: Writing CSV to: {output_path}")
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in results:
                writer.writerow({
                    "control_id": row.get("control_id", "Unknown"),
                    "status": row.get("status", "Unknown"),
                    "confidence_score": row.get("confidence_score", 0.0),
                    "matched_text": row.get("matched_text", "N/A"),
                    "explanation": row.get("explanation", "N/A")
                })
        
        print(f"SUCCESS: Export complete: {output_path.resolve()}")
        print(f"INFO: Total records written: {len(results)}")
        
        # Optional metadata display
        metadata = report.get("metadata", {})
        summary = metadata.get("summary", {})
        if summary:
            print(f"SUMMARY: Fully Met: {summary.get('fully_met', 0)}, "
                  f"Partially Met: {summary.get('partially_met', 0)}, "
                  f"Not Met: {summary.get('not_met', 0)}")
        
        if "generated_at" in metadata:
            print(f"INFO: Report generated at: {metadata['generated_at']}")
        
        # Optional: Auto-open CSV (on Windows) - with better error handling
        if os.name == "nt":  # Windows
            try:
                print("INFO: Attempting to open CSV file...")
                os.startfile(str(output_path.resolve()))
            except Exception as open_error:
                print(f"WARNING: Could not auto-open CSV file: {open_error}")
                print(f"INFO: You can manually open: {output_path.resolve()}")
        else:
            print(f"INFO: CSV saved to: {output_path.resolve()}")
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format: {e}")
    except ValueError as e:
        print(f"ERROR: {e}")
    except PermissionError as e:
        print(f"ERROR: Permission denied - cannot write to: {output_path}. Error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")

if __name__ == "__main__":
    export_gap_report_to_csv()