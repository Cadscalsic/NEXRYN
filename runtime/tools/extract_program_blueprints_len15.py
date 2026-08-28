import json
from pathlib import Path

p = Path("runtime/artifacts/runtime_diagnostic_report.json")

def load_json(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

data = load_json(p)

results = []

def walk(obj, path='$', parent=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}"
            if k == 'program_blueprints' and isinstance(v, list) and len(v)==15:
                results.append((new_path, v, parent))
            walk(v, new_path, obj)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", parent)

walk(data)

print(f"program_blueprints arrays with length 15: {len(results)}")
for i,(path,value,parent) in enumerate(results,1):
    print(f"HIT {i}: PATH={path} COUNT=15")
    if isinstance(parent, dict):
        print("  parent_keys=", list(parent.keys()))
        for meta in ['run_id','execution_id','execution_plan_id','report_id','timestamp','section','generated_programs','Generated Programs']:
            if meta in parent:
                print(f"  parent.{meta} = {parent[meta]}")
    # print program_ids
    for j,entry in enumerate(value):
        pid = entry.get('program_id') if isinstance(entry, dict) else None
        cname = entry.get('concept_name') if isinstance(entry, dict) else None
        print(f"  [{j}] {pid} ({cname})")
