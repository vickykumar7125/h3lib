import json
from pathlib import Path

r = json.loads(Path(r"d:\OfficeWork\h3-lib\scripts\h3_notebooks_analysis.json").read_text(encoding="utf-8"))
for nb in r["notebooks"]:
    print("=" * 70)
    print(nb["path"])
    print("titles:")
    for t in nb["titles"][:40]:
        print(" ", t)
    print("apis:", nb["all_h3_apis"])
    print("imports:", [i[0] for i in nb["top_imports"][:15]])
print("AGGREGATE", r["aggregate_h3_apis"][:40])
