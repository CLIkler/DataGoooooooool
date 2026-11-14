import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "historico" / "api_squads_cache.json"

squads = json.loads(CACHE.read_text(encoding="utf-8"))

for team, players in squads.items():
    print(f"\n=================== {team.upper()} ({len(players)} futbolistas) ===================")
    pos_map = {}
    for p in players:
        pos = p.get("position", "Unknown")
        pos_map.setdefault(pos, []).append(f"#{p.get('number', '-')} {p.get('name')} ({p.get('age')}a)")
    for pos, plist in pos_map.items():
        print(f"  {pos}: {', '.join(plist[:6])}")
