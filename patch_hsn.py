import json

path = "app/core/hsn_rates.json"
try:
    with open(path, "r") as f:
        data = json.load(f)
except Exception as e:
    data = {}

# Updates based on User Feedback and 56th Council Meeting
updates = {
    "8415": {
        "rate": "18%",
        "description": "Air conditioning machines. Reduced from 28% to 18% (Effective 2026).",
        "legal_ref": "Notification No. 1/2017-Central Tax (Rate)",
        "type": "GOODS"
    },
    "8701": {
        "rate": "5% or 18%",
        "description": "SPLIT CATEGORY: Agricultural Tractors (<1800cc) are 5%. Road Tractors/others (>1800cc) are 18%. Auditor MUST check invoice description.",
        "legal_ref": "Notification No. 1/2017-Central Tax (Rate)",
         "type": "GOODS"
    },
    "3305": {
        "rate": "5%",
        "description": "Preparations for use on the hair (Shampoos, Oils). Reduced from 18% to 5%.",
        "legal_ref": "Notification No. 1/2017-Central Tax (Rate)",
         "type": "GOODS"
    }
}

for k, v in updates.items():
    data[k] = v

with open(path, "w") as f:
    json.dump(data, f, indent=4)
print("Updated hsn_rates.json")
