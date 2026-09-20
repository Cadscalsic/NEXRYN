import json
from pathlib import Path

p = Path("runtime/artifacts/runtime_diagnostic_report.json")

def load_json(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

data = load_json(p)

# path discovered earlier in extractor
path = ['compressed_report','program_generation_report','program_blueprints']

node = data
try:
    for key in path:
        node = node[key]
except Exception as e:
    print(f'Failed to follow path {path}: {e}')
    raise

if not isinstance(node, list):
    print('Target node is not a list; type=', type(node))
    raise SystemExit(1)

programs = node
print('selected_path=', '.'.join(path))
print('total_count=', len(programs))
ids = [p.get('program_id') if isinstance(p, dict) else None for p in programs]
unique_ids = set(ids)
print('unique_ids=', len(unique_ids))
# duplicates
from collections import Counter
cnt = Counter(ids)
dups = [k for k,v in cnt.items() if v>1]
print('duplicate_ids_count=', len(dups))

# generation_success distribution
success_count = sum(1 for p in programs if isinstance(p, dict) and p.get('generation_success')=='TRUE')
attempted_count = sum(1 for p in programs if isinstance(p, dict) and p.get('generation_attempted')=='TRUE')
print('generation_success_count=', success_count)
print('generation_attempted_count=', attempted_count)

# print sample of entries
for i,p in enumerate(programs[:12]):
    if isinstance(p, dict):
        print(f'[{i}] id={p.get("program_id")} concept={p.get("concept_name")} generation_success={p.get("generation_success")}')
    else:
        print(f'[{i}] {p}')
