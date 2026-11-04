# Egypt Governorates, Cities and Villages Dataset

**Open database of Egypt's administrative divisions in Arabic and English: JSON, CSV, SQL and GeoJSON map polygons.**

**قاعدة بيانات مفتوحة لمحافظات ومراكز ومدن وقرى مصر بالعربية والإنجليزية، مع خرائط وحدود GeoJSON.** [اقرأ بالعربية](#بالعربية)

[![Validate data](https://github.com/Zeyad-Mohamed1/egypt-governorates-cities-villages/actions/workflows/validate.yml/badge.svg)](https://github.com/Zeyad-Mohamed1/egypt-governorates-cities-villages/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/Zeyad-Mohamed1/egypt-governorates-cities-villages)](https://github.com/Zeyad-Mohamed1/egypt-governorates-cities-villages/releases/latest)

> **Not an official source.** This dataset was built by researching, combining and correcting public information. It is not an independent source of truth and is not endorsed by any government body. Verify it before legal, government or other critical use.

| Level | Count | Examples | File |
|---|---:|---|---|
| Governorates (محافظات) | **27** | Cairo, Giza, Alexandria | `governorates` |
| Cities (مدن) | **259** | Tanta, Hurghada, New Alamein | `cities` |
| Centers: markaz, qism and new cities (مراكز وأقسام ومدن جديدة) | **418** | Banha (Markaz), Nasr City 1 (Qism), New Alamein | `centers` |
| Localities: villages, cities and neighborhoods (قرى ومدن وشياخات) | **5,773** | Kafr Matbul, Smouha, Garden City | `localities` |

Use it for address forms, cascading governorate → city → village dropdowns, delivery zones, e-commerce checkout, choropleth maps, analytics, and reverse geocoding.

## Download

| Format | Files |
|---|---|
| **JSON** | [`governorates.json`](data/governorates.json) · [`cities.json`](data/cities.json) · [`centers.json`](data/centers.json) · [`localities.json`](data/localities.json) |
| **Nested JSON** | [`egypt-divisions.json`](data/egypt-divisions.json) (governorate → center → locality) |
| **CSV** (UTF-8 with BOM, for Arabic in Excel) | [`governorates.csv`](data/governorates.csv) · [`cities.csv`](data/cities.csv) · [`centers.csv`](data/centers.csv) · [`localities.csv`](data/localities.csv) |
| **SQL** | [`egypt-divisions.sql`](data/egypt-divisions.sql) |
| **GeoJSON polygons** | [`governorates.geojson`](data/geojson/governorates.geojson) · [`centers.geojson`](data/geojson/centers.geojson) · [`localities.geojson`](data/geojson/localities.geojson) |
| **All files** | [Latest release](https://github.com/Zeyad-Mohamed1/egypt-governorates-cities-villages/releases/latest) |

## Quick start

**JavaScript**

```js
const base = "https://cdn.jsdelivr.net/gh/Zeyad-Mohamed1/egypt-governorates-cities-villages@v1.1.0/data";
const cities = await fetch(`${base}/cities.json`).then((r) => r.json());

const gharbiaCities = cities.filter((c) => c.governorate_code === "EG16");
console.log(gharbiaCities.map((c) => c.name_en));
```

**Map with Leaflet**

```js
const base = "https://cdn.jsdelivr.net/gh/Zeyad-Mohamed1/egypt-governorates-cities-villages@v1.1.0/data/geojson";
const shapes = await fetch(`${base}/governorates.geojson`).then((r) => r.json());
L.geoJSON(shapes).bindTooltip((layer) => layer.feature.properties.name_ar).addTo(map);
```

**Python**

```python
import json

with open("data/localities.json", encoding="utf-8") as f:
    localities = json.load(f)

# Villages in Banha Markaz
villages = [x for x in localities if x["center_code"] == "EG1402" and x["type"] == "village"]
```

**SQL** (tested on SQLite, PostgreSQL and MySQL. On MySQL use `utf8mb4`.)

```sql
SELECT g.name_en AS governorate, c.label_en AS center, l.name_ar, l.name_en
FROM localities l
JOIN centers c ON c.id = l.center_id
JOIN governorates g ON g.id = c.governorate_id
WHERE g.iso_3166_2 = 'EG-GZ' AND l.type = 'village';
```

## Fields

Always use `id` or `code` as the key, because names repeat across centers.

**`governorates`:** `id`, `code`, `iso_3166_2`, `name_ar`, `name_en`, `latitude`, `longitude`, `area_sqkm`

**`cities`:** one row per city, which is the easiest list for an address form. Large cities are divided into several qisms, so Tanta has one row here and two rows in `centers`.

| Field | Meaning |
|---|---|
| `id`, `code` | Unique key |
| `governorate_id`, `governorate_code` | Parent governorate |
| `name_ar`, `name_en`, `name_ar_search` | Names and search key |
| `is_capital` | `1` for the governorate's capital |
| `center_codes` | Centers that make up the city, separated by `;` |
| `location_quality` | `source`, `parent_center` (average of its centers) or `estimated` |
| `latitude`, `longitude` | Center point |

The list is built from city rows, new cities, and a reviewed list of cities divided into qisms. It is not an official list of cities.

**`centers`**

| Field | Meaning |
|---|---|
| `id`, `code` | Unique key |
| `governorate_id`, `governorate_code` | Parent governorate |
| `type` | `qism`, `markaz`, `new_city`, `police_administration`, `zemam_out`, or `other` |
| `name_ar`, `name_en` | Names. `name_en` can repeat, such as Banha for both qism and markaz |
| `label_en` | Display name that tells those apart, such as `Banha (Markaz)` |
| `name_ar_search` | Search key that ignores ة/ه, ى/ي and أ/إ/ا. Not for display |
| `source` | `base_2017`, `update_2023` for units created since 2017, or `added` for new cities |
| `status` | `active`, or `split` when the unit was later divided. Split units keep their 2017 localities |
| `replaces_code` | On a new unit, the older unit it was split from |
| `founded` | Year founded, on added cities |
| `location_quality` | How far to trust the coordinates: `source`, `parent_center` or `estimated` |
| `latitude`, `longitude`, `area_sqkm` | Center point and area. Area is empty on added units |

**`localities`**

| Field | Meaning |
|---|---|
| `id`, `code` | Unique key |
| `center_id`, `center_code`, `governorate_id`, `governorate_code` | Parents |
| `type` | `village`, `city`, `neighborhood`, or `other` |
| `name_ar`, `name_en`, `name_ar_search` | Names and search key |
| `name_en_source` | How the English name was written. [See quality](#english-names) |
| `notes_ar` | Descriptions separated from the name, such as `تشمل دقادوس` |
| `source` | `base_2017`, or `added` for places added to the 2017 structure |
| `location_quality` | `source` or `estimated` |
| `latitude`, `longitude`, `area_sqkm` | Center point and area. Area is empty on added places |

Skip `zemam_out` centers in address forms. These 14 areas lie outside registered land and contain no localities.

## English names

Locality names in `name_en` follow the Arabic name word by word:

- **Same order:** `الشيخ حسين` is `El Sheikh Hussein`, and `ميت العز` is `Mit El Izz`.
- **One spelling per word:** the same Arabic word is spelled the same way across all localities.
- **No Arabic characters:** every `name_en` uses Latin letters only.
- **Same style:** the Arabic article `ال` is `El`, as in `Kafr El Sheikh`.
- **Numbered units use numbers:** `قسم ثان` is `Qism 2`, and `الشياخة الأولى` is `Shiakha 1`.
- **Cities end in `City`:** `مدينة طلخا` is `Talkha City`, and `مدينة طيبة الجديدة` is `New Tiba City`.

Governorates, cities, centers and added places use their common English names, such as `New Alamein`.

| `name_en_source` | Localities | How it was written |
|---|---:|---|
| `word_match` | 4,599 (79.7%) | Every word has a researched spelling |
| `hand_spelled` | 942 (16.3%) | At least one word was spelled by hand from the Arabic. Short vowels are a best judgment, because Arabic does not write them |
| `center_name` | 171 (3.0%) | City named after its center, using the corrected center name |
| `curated` | 61 (1.1%) | Common name chosen by hand for added places |

No English name here has been checked against local usage on the ground, so please report any you know are wrong.

## What's inside

- **Clean Arabic names:** one spelling per word, with notes moved out of names, and stray spaces and symbols removed.
- **A real city list:** 259 cities with their capitals, so Tanta is one choice, not Tanta 1 and Tanta 2.
- **Clear types:** every center and locality has a `type`, so villages and neighborhoods can be told apart.
- **Current governorates:** Esna and Armant are under Luxor, including on the map.
- **Newer places:** 22 new cities, such as the New Administrative Capital and New Alamein, and 31 units created since 2017.
- **Well-known areas:** 35 areas such as Mohandessin, Smouha and Madinaty.
- **Coordinates everywhere:** every row has a location, with approximate ones flagged.
- **Tested data:** [checks](tests/test_data.py) run on every change, including loading the SQL into PostgreSQL and MySQL.

## Limits

- **Locality names and all boundaries date from 2017.** Center names also reflect lists from January 2023. Cairo and Alexandria could not be compared with those lists, and later changes are not covered.
- **Units added since 2017 have no polygons or localities.** Split units such as Banha (Qism) keep the 2017 localities. New cities have one locality each.
- **Some coordinates are estimates.** `parent_center` means the point of the unit it was split from. `estimated` covers 8 centers and 5 localities, including these:
  - **New Rashid:** on the coast west of Rashid, from a published description.
  - **New Nag Hammadi:** where the desert road crosses the Aswan road.
  - **New Beni Mazar:** on the Western Desert Road, west of El Bahnasa. Reports disagree on this site.
  - **6th of October 3:** the police station location.
  - **New East Oweinat:** the location of the East Oweinat project.
- **Boundaries can disagree with governorates.** Six new cities fall outside their listed governorate on the 2017 maps: Salam Misr, New Obour, West Qena, Capital Gardens, New Nag Hammadi and New Girga.
- **Added areas are placed by map point.** A point near a boundary can land in the neighboring center. Smart Village and Hadayek El Ahram fall on unregistered land, so they use the nearest center.
- **Qena and Luxor shapes** still show inner lines. Unregistered desert stays with Qena, so Luxor's area here is below its official size.
- **Locality `type` is inferred** from the parent center and the name, so it is not an official classification.

Corrections are welcome. Please [open an issue](https://github.com/Zeyad-Mohamed1/egypt-governorates-cities-villages/issues), especially for English names and new cities.

## FAQ

**Is this an official source?** No. It was built through research and is not an independent source of truth.

**How many governorates does Egypt have?** 27, listed in `governorates` with ISO 3166-2 codes.

**Where can I get Egypt governorate boundaries as GeoJSON?** In [`data/geojson`](data/geojson), at governorate, center and locality level. Join on `code`.

**Does it include the New Administrative Capital and New Alamein?** Yes, with 20 other new cities, marked `source: added`. Some locations are estimates.

**Where can I get a list of Egyptian cities and villages in Arabic and English?** `cities` lists 259 cities, and `localities` lists 5,773 villages, cities and neighborhoods with their center and governorate.

**What is the difference between a markaz and a qism?** A markaz (مركز) is usually a rural center made up of villages. A qism (قسم) is an urban district made up of neighborhoods (شياخات).

**Can I use it commercially?** The maintainer adds no restrictions. See [Credits](#credits) for what the underlying data requires.

## بالعربية

> **ليست مصدرًا رسميًا.** بُنيت هذه البيانات بالبحث في معلومات عامة وجمعها وتصحيحها، وهي ليست مصدرًا مستقلًا للحقيقة ولا تعتمدها أي جهة حكومية. تحقق منها قبل أي استخدام قانوني أو حكومي.

**قاعدة بيانات مفتوحة للتقسيم الإداري في مصر:** 27 محافظة و259 مدينة و418 مركزًا وقسمًا ومدينة جديدة و5,773 قرية ومدينة وشياخة، بالعربية والإنجليزية، وبصيغ JSON وCSV وSQL، مع حدود الخرائط بصيغة GeoJSON.

مناسبة لنماذج العناوين، وقوائم المحافظة ثم المدينة ثم القرية، ومناطق التوصيل، والمتاجر الإلكترونية، والخرائط.

**المحتوى:**

- أسماء إنجليزية تتبع الاسم العربي كلمة بكلمة وبالترتيب نفسه، بحروف لاتينية فقط.
- إملاء عربي موحد مع حقل `name_ar_search` للبحث، ونقل الملاحظات من الأسماء إلى `notes_ar`.
- معرفات رقمية فريدة، لأن الأسماء تتكرر بين المراكز، مثل «العزب» و«النهضة».
- 22 مدينة جديدة، منها العاصمة الإدارية الجديدة والعلمين الجديدة والمنصورة الجديدة.
- 31 وحدة استُحدثت بعد 2017، مثل أول وثان بنها ومركز القرنة، و35 منطقة معروفة مثل المهندسين وسموحة ومدينتي.
- قائمة مدن مستقلة، فمدينة طنطا صف واحد بدل قسم أول وقسم ثان.
- إسنا وأرمنت ضمن محافظة الأقصر، وإحداثيات لكل صف.

**تنبيهات مهمة:**

- القرى والحدود من بيانات عام 2017، والوحدات الجديدة بلا حدود خرائط أو قرى تابعة.
- بعض الإحداثيات تقديرية، وتوضحها قيمة الحقل `location_quality`، مثل رشيد الجديدة وبني مزار الجديدة ونجع حمادي الجديدة.
- الأسماء الإنجليزية مكتوبة من العربية كلمة بكلمة ولم تُراجع ميدانيًا، و16% منها مكتوبة يدويًا بأفضل تقدير للحركات، وهي الصفوف التي قيمتها `hand_spelled`.

## Credits

This repository has no license file, and the maintainer adds no restrictions of their own. The underlying data has its own terms, and this dataset changes it by cleaning, correcting, matching and adding records:

- **Boundaries and base structure:** [Egypt Subnational Administrative Boundaries](https://data.humdata.org/dataset/cod-ab-egy), CAPMAS and OCHA, via HDX, under [CC BY-IGO](https://docs.humdata.org/about/data-licenses).
- **Name and place data:** [GeoNames](https://www.geonames.org/), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Map positions used for some estimates:** © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, under ODbL.
- **Arabic word spacing:** [mo7amed-said-223/egypt-cities](https://github.com/mo7amed-said-223/egypt-cities), which states no license.
- **Also researched:** Wikidata and Wikipedia.

If you redistribute this data, keep these credits. This project is independent and is not endorsed by any of these organizations or by the Government of Egypt.
