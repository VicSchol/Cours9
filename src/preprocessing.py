# %% --------------------------- IMPORTS ---------------------------
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import easyocr
from tqdm import tqdm
import numpy as np

# %% --------------------------- CONFIG ---------------------------
BASE_URL = "https://public.opendatasoft.com/api/records/1.0/search/"
DATASET = "evenements-publics-openagenda"
DATE_LIMIT = (datetime.now() - timedelta(days=365)).isoformat()
OUTPUT_FILENAME = "evenements_lyon_prets.feather"

PARAMS = {
    "dataset": DATASET,
    "q": "*",
    "rows": 300,
    "start": 0,
    "refine.location_city": "Lyon",
    "refine.lang": "fr",
    "facet": "date_start",
    "refine.date_start": f"[{DATE_LIMIT} TO *]"
}

# %% --------------------------- FETCH OPENDATA ---------------------------
def fetch_all_events(base_url, params):
    all_records = []
    response = requests.get(base_url, params=params).json()
    total_count = response.get("nhits", 0)
    print(f"Total d'événements trouvés : {total_count}")

    while params["start"] < total_count and params["start"] < 10000:
        print(f"Récupération à partir de {params['start']}...")
        response = requests.get(base_url, params=params).json()
        records = response.get("records", [])
        if not records:
            break
        all_records.extend(records)
        params["start"] += params["rows"]

    return [rec["fields"] for rec in all_records]

# ------------------------------------------------------
# FONCTIONS UTILISÉES PAR LES TESTS (NE DOIVENT PAS EXÉCUTER DE CODE)
# ------------------------------------------------------

def build_dates(row):
    parts = []
    if isinstance(row.get("firstdate_begin"), pd.Timestamp):
        parts.append("Première date : " + row["firstdate_begin"].strftime("%d/%m/%Y"))
    if isinstance(row.get("firstdate_end"), pd.Timestamp):
        parts.append("Fin première période : " + row["firstdate_end"].strftime("%d/%m/%Y"))
    if isinstance(row.get("lastdate_begin"), pd.Timestamp):
        parts.append("Dernière date : " + row["lastdate_begin"].strftime("%d/%m/%Y"))
    if isinstance(row.get("lastdate_end"), pd.Timestamp):
        parts.append("Fin dernière période : " + row["lastdate_end"].strftime("%d/%m/%Y"))
    if row.get("timings"):
        parts.append(f"Horaires : {row['timings']}")
    return " | ".join(parts)

def split_coords(val):
    try:
        lat, lon = val.split(',')
        return float(lat), float(lon)
    except:
        return None, None

def convert_to_text(val):
    """Convertit différentes valeurs en texte lisible pour vectorisation."""
    if val is None:
        return ""
    elif isinstance(val, (list, tuple, np.ndarray)):
        return ", ".join([str(v) for v in val])
    elif isinstance(val, dict):
        return " ".join([f"{k}: {v}" for k, v in val.items()])
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, pd.Timestamp):
        return val.strftime("%d/%m/%Y %H:%M:%S")
    elif isinstance(val, str):
        return val
    return str(val)

# OCR (mockée dans les tests)
reader = easyocr.Reader(['fr'], gpu=False)

def ocr_image(url):
    try:
        if not url or not isinstance(url, str):
            return ""
        if url.startswith("http"):
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(url)
        result = reader.readtext(img, detail=0)
        return " ".join(result)
    except:
        return ""

# ------------------------------------------------------
# TOUT LE CODE EXÉCUTIF ICI UNIQUEMENT
# ------------------------------------------------------
if __name__ == "__main__":

    # FETCH OPENDATA
    df_od = pd.DataFrame(fetch_all_events(BASE_URL, PARAMS))
    print(f"Nombre d'événements OpenData récupérés : {len(df_od)}")

    # RENAME
    df_od = df_od.rename(columns={
        "uid": "event_id",
        "title_fr": "title",
        "description_fr": "description",
        "longdescription_fr": "long_description",
        "date_start": "start_date",
        "location_lat": "latitude",
        "location_lon": "longitude"
    })

    # DATE CLEANING
    date_cols = [col for col in df_od.columns if 'date' in col.lower()]
    for col in date_cols:
        df_od[col] = pd.to_datetime(df_od[col], errors='coerce')

    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    if 'firstdate_begin' in df_od.columns:
        df_od = df_od[df_od['firstdate_begin'] >= one_year_ago]

    df_od['dates_text'] = df_od.apply(build_dates, axis=1)

    # COORDINATES
    if 'location_coordinates' in df_od.columns:
        df_od['location_coordinates'] = df_od['location_coordinates'].fillna('')
        df_od['latitude'], df_od['longitude'] = zip(*df_od['location_coordinates'].apply(split_coords))

    def format_coordinates(row):
        lat = row.get('latitude')
        lon = row.get('longitude')
        if pd.notnull(lat) and pd.notnull(lon):
            return f"Coordonnées : {lat:.5f}, {lon:.5f}"
        return ""

    df_od['geo_text'] = df_od.apply(format_coordinates, axis=1)
    df_od.drop(columns=['latitude', 'longitude'], inplace=True)

    # REMOVE UNUSED COLUMNS
    cols_to_keep = [
        "event_id", "title", "slug",
        "description", "long_description", "keywords_fr", "conditions_fr",
        "location_name", "location_address", "location_city", "location_postalcode",
        "location_region", "location_access_fr", "location_description_fr",
        "firstdate_begin", "firstdate_end",
        "lastdate_begin", "lastdate_end",
        "dates_text", "timings",
        "age_min", "age_max",
        "accessibility", "accessibility_label_fr",
        "canonicalurl", "location_website", "onlineaccesslink",
        "image",
        "location_coordinates",
        "geo_text"
    ]

    df_od = df_od[[col for col in cols_to_keep if col in df_od.columns]].copy()

    # TEXT CONVERSION
    for col in df_od.columns:
        df_od[col] = df_od[col].apply(convert_to_text)

    # OCR
    valid_urls = [u for u in df_od['image'].dropna().unique() if isinstance(u, str) and len(u) > 5]

    ocr_map = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(ocr_image, url): url for url in valid_urls}
        for future in tqdm(as_completed(futures), total=len(futures), ncols=90, desc="OCR en cours"):
            ocr_map[futures[future]] = future.result()

    df_od['ocr_text'] = df_od['image'].map(lambda x: ocr_map.get(x, ""))

    # TEXT FINAL
    df_od['age_text'] = df_od.apply(
        lambda row: f"Âge : {row['age_min']} à {row['age_max']}"
        if row.get('age_min') and row.get('age_max')
        else (f"Âge : {row.get('age_min')}" if row.get('age_min')
              else (f"Âge : {row.get('age_max')}" if row.get('age_max') else "")),
        axis=1
    )

    cols_vectorisation = ['title', 'description', 'long_description', 'ocr_text', 'dates_text', 'geo_text', 'age_text']
    cols_vectorisation = [col for col in cols_vectorisation if col in df_od.columns]

    df_od['vectorise_text'] = df_od[cols_vectorisation].agg(" ".join, axis=1)

    # EXPORT
    try:
        df_od.to_feather(OUTPUT_FILENAME)
        print(f"\n✅ EXPORT OK : {OUTPUT_FILENAME}")
        print(f"Nombre total d'événements : {len(df_od)}")
    except Exception as e:
        print(f"⚠️ Erreur export : {e}")
