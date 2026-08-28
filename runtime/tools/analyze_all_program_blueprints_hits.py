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
            if k == 'program_blueprints' and isinstance(v, list):
                hits.append((new_path, v, parent))
            walk(v, new_path, obj)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", parent)

walk(data)

print(f"program_blueprints occurrences: {len(hits)}")
for i,(path,value,parent) in enumerate(hits,1):
    total = len(value)
    success_count = sum(1 for p in value if isinstance(p, dict) and p.get('generation_success')=='TRUE')
    attempted_count = sum(1 for p in value if isinstance(p, dict) and p.get('generation_attempted')=='TRUE')
    unique_ids = len({p.get('program_id') for p in value if isinstance(p, dict)})
    print(f"HIT {i}: PATH={path} COUNT={total} unique_ids={unique_ids} generation_attempted={attempted_count} generation_success={success_count}")
    if total==15 or success_count>0:
        print('  Parent keys=', list(parent.keys()) if isinstance(parent, dict) else type(parent))
        print('  Sample program_ids:')
        for j,p in enumerate(value[:12]):
            if isinstance(p, dict):
                print(f"    [{j}] {p.get('program_id')} gen_success={p.get('generation_success')} gen_attempted={p.get('generation_attempted')}")
            else:
                print(f"    [{j}] {p}")
