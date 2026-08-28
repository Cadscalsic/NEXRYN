import json
from pathlib import Path

p = Path("runtime/artifacts/runtime_diagnostic_report.json")

with p.open("r", encoding="utf-8") as f:
    data = json.load(f)

hits = []

def walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}"
            if k == "program_blueprints":
                hits.append((new_path, v))
            walk(v, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(data)

print(f"program_blueprints occurrences: {len(hits)}")

for n, (path, value) in enumerate(hits, 1):
    print("\n" + "=" * 100)
    print(f"HIT {n}")
    print("PATH:", path)
    print("TYPE:", type(value).__name__)
    try:
        print("COUNT:", len(value))
    except TypeError:
        print("COUNT: N/A")
    s = json.dumps(value, ensure_ascii=False, indent=2)
    print(s[:50000])
