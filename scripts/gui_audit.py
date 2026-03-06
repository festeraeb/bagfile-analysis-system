"""Audit every GUI file: find all command=self.X bindings and check the method exists."""
import re
from pathlib import Path

REPO = Path(r"C:\Users\thomf\programming\Bagrecovery")

GUI_FILES = [
    "bag_processor/bag_wreck_gui.py",
    "bag_processor/comprehensive_bag_gui.py",
    "bag_processor/enhanced_bag_gui.py",
    "bag_processor/bag_analyzer_gui.py",
    "recovered/bag_analyzer_gui.py",
    "recovered/pdf_breaker_gui.py",
    "recovered/swayze_gui.py",
    "recovered/workflow_gui.py",
    "recovered/wreck_review_gui.py",
]
for p in REPO.glob("*.py"):
    rel = str(p.relative_to(REPO))
    if "gui" in p.name.lower() and rel not in GUI_FILES:
        GUI_FILES.append(rel)
for p in REPO.glob("bag_processor/*.py"):
    rel = str(p.relative_to(REPO))
    if "gui" in p.name.lower() and rel not in GUI_FILES:
        GUI_FILES.append(rel)

CMD_PAT = re.compile(r'command\s*=\s*self\.(\w+(?:\.\w+)*)')
BIND_PAT = re.compile(r'\.bind\s*\([^,]+,\s*self\.(\w+(?:\.\w+)*)')
DEF_PAT  = re.compile(r'^\s{4}def (\w+)\s*\(', re.MULTILINE)

results = {}
seen_names = set()
for rel_path in GUI_FILES:
    full = REPO / rel_path
    if not full.exists(): continue
    if full.name in seen_names: continue
    seen_names.add(full.name)
    src = full.read_text(encoding="utf-8", errors="ignore")
    methods = set(DEF_PAT.findall(src))
    cmds = {}; binds = {}
    for i, line in enumerate(src.splitlines(), 1):
        for m in CMD_PAT.finditer(line):
            n = m.group(1)
            if '.' not in n: cmds.setdefault(n, []).append(i)
        for m in BIND_PAT.finditer(line):
            n = m.group(1)
            if '.' not in n: binds.setdefault(n, []).append(i)
    missing_cmds  = {k: v for k, v in cmds.items()  if k not in methods}
    missing_binds = {k: v for k, v in binds.items() if k not in methods}
    results[full.name] = {
        "path": str(full.relative_to(REPO)),
        "missing_commands": missing_cmds,
        "missing_binds": missing_binds,
        "ok_count": len([k for k in cmds if k in methods]) + len([k for k in binds if k in methods]),
        "total": len(cmds) + len(binds),
    }

print("\n" + "="*70)
print("  GUI BUTTON / COMMAND WIRING AUDIT")
print("="*70)
all_ok = True
for fname, r in sorted(results.items()):
    missing = {**r["missing_commands"], **r["missing_binds"]}
    status = "CLEAN" if not missing else f"{len(missing)} BROKEN"
    print(f"\n  {fname}  [{status}]  {r['ok_count']}/{r['total']} OK")
    for name, lns in sorted(missing.items()):
        all_ok = False
        print(f"    BROKEN: self.{name}()  @ lines {lns}")
print(f"\n  OVERALL: {'ALL CLEAN' if all_ok else 'BROKEN WIRING'}\n")
