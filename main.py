import os
import json

def validate_policy():
    path = os.path.join("data", "sample_policy.txt")
    if not os.path.exists(path):
        raise FileNotFoundError("❌ sample_policy.txt not found in data/")
    
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            raise ValueError("❌ sample_policy.txt is empty.")
    print("✅ Policy file loaded successfully.")

def validate_controls():
    path = os.path.join("controls", "sample_controls.json")
    if not os.path.exists(path):
        raise FileNotFoundError("❌ sample_controls.json not found in controls/")
    
    with open(path, "r", encoding="utf-8") as f:
        controls = json.load(f)
        if not isinstance(controls, list) or not controls:
            raise ValueError("❌ sample_controls.json must be a non-empty list.")
        
        required_keys = {"control_id", "description", "level"}
        for control in controls:
            if not required_keys.issubset(control.keys()):
                raise ValueError(f"❌ Invalid control entry: {control}")
    print("✅ Controls file validated successfully.")

if __name__ == "__main__":
    validate_policy()
    validate_controls()
    print("🎯 All files are ready for Phase 2.")