#!/usr/bin/env python3
"""Validate everything in data/. Usage: python3 tests/test_data.py"""
import collections
import csv
import json
import pathlib
import re
import sqlite3

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
ARABIC = re.compile("[؀-ۿ]")


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


governorates, cities, centers, localities = load("governorates"), load("cities"), load("centers"), load("localities")
everything = {"governorates": governorates, "cities": cities, "centers": centers, "localities": localities}

# Coverage
assert {g["name_en"] for g in governorates} >= {"Minya", "Sohag", "Kafr El Sheikh"}
assert {c["type"] for c in centers} == {"qism", "markaz", "new_city", "police_administration", "zemam_out", "other"}
assert {r["type"] for r in localities} == {"village", "city", "neighborhood", "other"}
assert next(r for r in localities if r["code"] == "EG010101")["name_ar"] == "التبين البحرية"
assert (len(governorates), len(centers), len(localities)) == (27, 418, 5773)
assert sum(c["source"] == "update_2023" for c in centers) == 31
assert {"El Qurna", "Abu El Numrus", "Banha 1", "Banha 2"} <= {c["name_en"] for c in centers}
codes = {c["code"]: c for c in centers}
for center in centers:
    if center["replaces_code"]:
        assert codes[center["replaces_code"]]["status"] == "split", center["code"]
assert {c["code"] for c in centers if c["status"] == "split"} == {c["replaces_code"] for c in centers if c["replaces_code"]}
assert sum(c["source"] == "base_2017" for c in centers) == 365 and sum(r["source"] == "base_2017" for r in localities) == 5716
assert sum(c["type"] == "zemam_out" for c in centers) == 14
assert not {r["center_id"] for r in localities} & {c["id"] for c in centers if c["type"] == "zemam_out"}
assert {"New Administrative Capital", "New Alamein", "New Mansoura", "New Galala"} <= {c["name_en"] for c in centers}
assert sum(c["source"] == "added" for c in centers) == 22
assert {"Mohandessin", "Smouha", "Madinaty", "Gheit El Enab"} <= {r["name_en"] for r in localities}
assert next(r for r in localities if r["code"] == "EG140101")["governorate_code"] == "EG14"

# Cities: one row per city, including those split across several qisms
assert len(cities) == 259
center_codes = {c["code"] for c in centers}
assert all(code in center_codes for city in cities for code in city["center_codes"].split(";"))
assert sum(c["is_capital"] for c in cities) == 27
assert len({c["governorate_code"] for c in cities if c["is_capital"]}) == 27
assert len({(c["governorate_code"], c["name_en"]) for c in cities}) == len(cities)
city_names = {c["name_en"]: c for c in cities}
assert {"Cairo", "Tanta", "Aswan", "Damietta", "Mansoura", "Hurghada", "Mallawi", "New Alamein"} <= set(city_names)
assert city_names["Tanta"]["center_codes"] == "EG1601;EG1602" and city_names["Tanta"]["is_capital"] == 1

# Corrections to the sources
moved = {"EG2704", "EG2705"}
assert all(c["governorate_code"] == "EG29" for c in centers if c["code"] in moved)
assert all(r["governorate_code"] == "EG29" for r in localities if r["center_code"] in moved)
assert not [c["name_en"] for c in centers if re.search(r"Markz|Kesm|Paris Paris|^Alamn$|, al-|\b[A-Z] L\b|[a-z][A-Z]", c["name_en"])]

# Keys: integers, unique, and every parent exists
for name, rows in everything.items():
    assert all(type(r["id"]) is int for r in rows), name
    assert len({r["id"] for r in rows}) == len(rows), name
    assert len({r["code"] for r in rows}) == len(rows), name
governorate_ids = {g["id"] for g in governorates}
center_ids = {c["id"]: c for c in centers}
assert all(c["governorate_id"] in governorate_ids and (c["code"].startswith(c["governorate_code"]) or c["code"] in moved) for c in centers)
for row in localities:
    assert center_ids[row["center_id"]]["governorate_id"] == row["governorate_id"]
    assert row["code"].startswith(row["center_code"])
    assert row["center_code"].startswith(row["governorate_code"]) or row["center_code"] in moved

# Arabic names: no stray characters, no embedded notes
for name, rows in everything.items():
    for row in rows:
        value = row["name_ar"]
        assert ARABIC.search(value), value
        assert value == value.strip() and "\xa0" not in value and "  " not in value, repr(value)
        assert not re.search(r"[_*?]", value), value
        assert "تشمل" not in value and "سابقا" not in value, value

# One spelling per word across the dataset
variants = collections.defaultdict(set)
for rows in everything.values():
    for row in rows:
        for word in row["name_ar"].split():
            key = word
            for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
                key = key.replace(a, b)
            variants[key].add(word)
assert not [v for v in variants.values() if len(v) > 1], [v for v in variants.values() if len(v) > 1][:5]

# English names: real, printable, and never a copy of the Arabic
for rows in everything.values():
    for row in rows:
        value = row["name_en"]
        assert value and value == value.strip() and value.isascii(), repr(value)
        assert value != row["name_ar"] and (value[0].isupper() or value[0].isdigit()), value
        assert not re.search(r"[`_*]", value), value
assert {r["name_en_source"] for r in localities} == {"word_match", "hand_spelled", "center_name", "curated"}
assert not [r["name_en"] for r in localities if re.search(r"\bNew El\b|\b(First|Second|Third|Fourth)\b.*\bQism\b|Qism (First|Second|Third|Fourth)", r["name_en"])]
assert not [r["name_ar"] for r in localities if re.search("عبن |نحوع|كفراحمد|منشيهال|ثانبه|المثتسمرون", r["name_ar"])]
assert next(r for r in localities if r["name_ar"] == "مدينة الفيوم الجديدة")["name_en"] == "New Faiyum City"
assert next(r for r in localities if r["name_ar"] == "جاردن سيتي")["name_en"] == "Garden City"
assert next(r for r in localities if r["name_ar"] == "قسم ثان")["name_en"] == "Qism 2"
assert next(r for r in localities if r["name_ar"] == "رابعة العدوية")["name_en"] == "Rabaa El Adawiya"
assert not [r["name_en"] for r in localities if "Madinat Tenth" in r["name_en"]]
assert next(r for r in localities if r["name_ar"] == "التقدم")["name_en"] == "El Taqaddum"
assert next(r for r in localities if r["name_ar"] == "مدينة الأقصر")["type"] == "city"
assert not [r["name_en"] for r in localities if re.search(r"\b[Aa]l\b", r["name_en"])]
assert not [f for r in centers + localities for f in ("name_ar_source", "geonames_id", "wikidata_id") if f in r]

# Written word for word: same order and word count as the Arabic, one spelling per Arabic word
spellings = collections.defaultdict(set)
for row in localities:
    if row["name_en_source"] not in ("word_match", "hand_spelled") or re.search(r"(^|\s)و|\d", row["name_ar"]) or " City" in row["name_en"]:
        continue
    if re.search(r"(^|\s)(ال)?(أول|ثان|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر|اول|أولى|اولى|الأولى|ثانية|الثانية|ثانى|الثانى|ثالثة|الثالثة|رابعة|الرابعة|خامسة|الخامسة|سادسة|السادسة|سابعة|السابعة|ثامنة|الثامنة|تاسعة|التاسعة|عاشرة|العاشرة)(\s|$)", row["name_ar"]):
        continue
    english = re.sub(r"\b(El|Bel|Be) ", r"\1_", row["name_en"].replace("Port Said", "Port_Said") if "بورسعيد" in row["name_ar"] else row["name_en"]).split()
    arabic = row["name_ar"].split()
    assert len(english) == len(arabic), (row["name_ar"], row["name_en"])
    for ar_word, en_word in zip(arabic, english):
        key = ar_word
        for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
            key = key.replace(a, b)
        spellings[key].add(en_word)
assert not [v for v in spellings.values() if len(v) > 1], [v for v in spellings.values() if len(v) > 1][:5]
assert not [k for k, v in collections.Counter((r["center_id"], r["name_en"]) for r in localities).items() if v > 1]

# Non-unique names are expected, which is why code is the key
assert len({r["name_ar"] for r in localities}) < len(localities)
assert all(c["label_en"] for c in centers)
labels = collections.Counter((c["governorate_id"], c["label_en"]) for c in centers if c["type"] != "zemam_out")
assert not [k for k, v in labels.items() if v > 1], [k for k, v in labels.items() if v > 1]

# Coordinates fall inside Egypt
for rows in everything.values():
    placed = [r for r in rows if r["latitude"] is not None]
    assert all(21.5 < r["latitude"] < 32 and 24.5 < r["longitude"] < 37.5 for r in placed)
    assert len(placed) == len(rows)
assert {r["location_quality"] for r in centers + localities} == {"source", "parent_center", "estimated"}
assert {"New Rashid", "New Beni Mazar", "New Nag Hammadi", "6th of October 3"} <= {c["name_en"] for c in centers if c["location_quality"] == "estimated"}
assert all(c["source"] != "base_2017" for c in centers if c["location_quality"] != "source")
assert all(c["location_quality"] == "parent_center" for c in centers if c["replaces_code"])

# Every format carries the same records
for name, rows in everything.items():
    with open(DATA / f"{name}.csv", encoding="utf-8-sig", newline="") as handle:
        table = list(csv.DictReader(handle))
    assert [int(r["id"]) for r in table] == [r["id"] for r in rows], name
    assert [r["name_ar"] for r in table] == [r["name_ar"] for r in rows], name

nested = load("egypt-divisions")
assert len(nested) == 27
assert sum(len(g["centers"]) for g in nested) == 418
assert sum(len(c["localities"]) for g in nested for c in g["centers"]) == 5773
assert any(c["code"] == "EG2705" for g in nested if g["code"] == "EG29" for c in g["centers"])


# Map polygons
def in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i, point in enumerate(ring):
        if (point[1] > y) != (ring[j][1] > y) and x < (ring[j][0] - point[0]) * (y - point[1]) / (ring[j][1] - point[1]) + point[0]:
            inside = not inside
        j = i
    return inside


def in_shape(lat, lon, geometry):
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return any(in_ring(lon, lat, p[0]) and not any(in_ring(lon, lat, h) for h in p[1:]) for p in polygons)


shapes = {}
for name, rows, expected in (("governorates", governorates, 27), ("centers", centers, 365), ("localities", localities, 5716)):
    collection = json.loads((DATA / "geojson" / f"{name}.geojson").read_text(encoding="utf-8"))
    features = collection["features"]
    assert collection["type"] == "FeatureCollection" and len(features) == expected, name
    known = {r["code"]: r for r in rows}
    for feature in features:
        row = known[feature["properties"]["code"]]
        assert feature["properties"]["name_ar"] == row["name_ar"] and feature["properties"]["id"] == row["id"]
        assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon") and feature["geometry"]["coordinates"]
    shapes[name] = {f["properties"]["code"]: f["geometry"] for f in features}
    assert len(shapes[name]) == expected, name
assert in_shape(25.2935, 32.5565, shapes["governorates"]["EG29"]), "Esna must fall inside Luxor"
assert not in_shape(25.2935, 32.5565, shapes["governorates"]["EG27"]), "Esna must not fall inside Qena"
assert in_shape(30.0444, 31.2357, shapes["governorates"]["EG01"]), "central Cairo must fall inside Cairo"

# Added areas sit inside the center they were assigned to, unless moved off unregistered land
for row in (r for r in localities if r["code"][6:7] == "P"):
    assert row["latitude"] is not None and row["center_code"] in shapes["centers"]
inside = sum(in_shape(r["latitude"], r["longitude"], shapes["centers"][r["center_code"]]) for r in localities if r["code"][6:7] == "P")
assert inside >= 32, inside

db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")
db.executescript((DATA / "egypt-divisions.sql").read_text(encoding="utf-8"))
for name, rows in everything.items():
    assert db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] == len(rows), name
found = db.execute(
    "SELECT g.name_en FROM localities l JOIN centers c ON c.id = l.center_id "
    "JOIN governorates g ON g.id = c.governorate_id WHERE l.code = 'EG010101'"
).fetchone()
assert found == ("Cairo",)

# Files stay within what jsDelivr serves: 50 MB per package and 20 MB per file
root = DATA.parent
tracked = [p for p in root.rglob("*") if p.is_file() and not {".git", ".cache", "__pycache__", "sources", "scripts"} & set(p.parts)]
assert sum(p.stat().st_size for p in tracked) < 45_000_000
assert all(p.stat().st_size < 20_000_000 for p in tracked)

# Published counts match the data
readme_text = (root / "README.md").read_text(encoding="utf-8")
for count in (f"{len(cities)}", f"{len(centers)}", f"{len(localities):,}"):
    assert f"**{count}**" in readme_text, count
for source, total in collections.Counter(r["name_en_source"] for r in localities).items():
    assert f"| `{source}` | {total:,} (" in readme_text, source

# Every local link in the README resolves
readme = (root / "README.md").read_text(encoding="utf-8")
for target in re.findall(r"\]\((?!https?:|#)([^)#]+)\)", readme):
    assert (root / target).exists(), target
for path in re.findall(r"@v[\d.]+/data/(?:geojson/)?", readme):
    assert path
print("all checks passed")
