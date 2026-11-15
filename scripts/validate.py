#!/usr/bin/env python3
"""data/shops.json 검증: 필수 필드, 좌표 범위, id 중복, 근접 중복(약 50m) 검사."""
import json, math, sys
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "data" / "shops.json"
shops = json.loads(path.read_text(encoding="utf-8"))
errors, ids = [], set()
KINDS = {"shop", "stall", "chain", "convenience"}
terms = json.loads((path.parent / "i18n.json").read_text(encoding="utf-8"))["terms"]

for i, s in enumerate(shops):
    nm = s.get('name', '?')
    tag = f"#{i} {nm.get('en') or next(iter(nm.values())) if isinstance(nm, dict) else nm}"
    for f in ("id", "name", "country_code", "lat", "lng"):
        if f not in s:
            errors.append(f"{tag}: '{f}' 없음")
    if s.get("id") in ids:
        errors.append(f"{tag}: id 중복 {s['id']}")
    ids.add(s.get("id"))
    if len(str(s.get("country_code", ""))) != 2:
        errors.append(f"{tag}: country_code 는 2글자(ISO)")
    if not (-90 <= s.get("lat", 0) <= 90 and -180 <= s.get("lng", 0) <= 180):
        errors.append(f"{tag}: 좌표 범위 오류")
    if s.get("kind", "shop") not in KINDS:
        errors.append(f"{tag}: kind 는 {sorted(KINDS)} 중 하나")
    if "style" in s and s["style"] not in terms["style"]:
        errors.append(f"{tag}: style 은 {list(terms['style'])} 중 하나")
    if s.get("status", "open") not in ("open", "seasonal", "paused", "closed"):
        errors.append(f"{tag}: status 는 open/seasonal/paused/closed 중 하나")
    for g in ("kawa", "an"):
        for x in s.get(g, []):
            if x not in terms[g]:
                errors.append(f"{tag}: {g} 값 '{x}' 는 {list(terms[g])} 중 하나")

# 레어 타이틀 태그: 정해진 값만, 태그마다 가게 한 곳만
for tg in ("northmost", "southmost"):
    owners = [s["id"] for s in shops if tg in s.get("tags", [])]
    if len(owners) > 1:
        errors.append(f"태그 '{tg}' 가 여러 가게에 붙어 있음: {owners}")
for s in shops:
    for tg in s.get("tags", []):
        if tg not in ("northmost", "southmost"):
            errors.append(f"{s['id']}: 알 수 없는 태그 '{tg}'")

def dist_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lng"] - a["lng"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))

for i in range(len(shops)):
    for j in range(i + 1, len(shops)):
        try:
            if dist_m(shops[i], shops[j]) < 50:
                errors.append(f"근접 중복 의심: {shops[i]['id']} / {shops[j]['id']}")
        except KeyError:
            pass

if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(shops)}곳")
