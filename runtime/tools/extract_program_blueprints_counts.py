import json
from pathlib import Path

p = Path("runtime/artifacts/runtime_diagnostic_report.json")

def load_json(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

data = load_json(p)

hits = []

def walk(obj, path='$', parent=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}"
            if k == 'program_blueprints':
                hits.append((new_path, v, parent))
            walk(v, new_path, obj)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", parent)

walk(data)

print(f"program_blueprints occurrences: {len(hits)}")
for i, (path, value, parent) in enumerate(hits, 1):
    t = type(value).__name__
    cnt = len(value) if isinstance(value, list) else 'N/A'
    print(f"HIT {i}: PATH={path} TYPE={t} COUNT={cnt}")
    if isinstance(parent, dict):
        # print parent keys and some likely metadata
        keys = list(parent.keys())
        print(f"  parent_keys={keys}")
        # print obvious metadata if present
        for meta in ['run_id','execution_id','execution_plan_id','report_id','timestamp','section','generation_status','Generated Programs','generation_success']:
            if meta in parent:
                print(f"  parent.{meta} = {parent[meta]}")
    if isinstance(value, list) and len(value)==15:
        print("  --> Candidate current-run array found; printing brief sample entries")
        import itertools
        for j, entry in enumerate(itertools.islice(value, 0, 15)):
            pid = entry.get('program_id') if isinstance(entry, dict) else None
            cname = entry.get('concept_name') if isinstance(entry, dict) else None
            print(f"    [{j}] program_id={pid} concept_name={cname}")

