#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_map.py
Generates europe_map.json: a lightweight SVG basemap of Europe (country
outlines, public-domain Natural Earth data) plus the projection constants and
port coordinates used by index.html to draw the clickable bubble map.
Run once (or whenever the port list changes).
"""
from __future__ import annotations
import json
import math
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Natural Earth 50m (traçado fino). Cache local opcional em /tmp/ne50m.geojson.
GEOJSON_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
               "master/geojson/ne_50m_admin_0_countries.geojson")
LOCAL_CACHE = Path("/tmp/ne50m.geojson")

COUNTRIES = {
    "Portugal", "Spain", "France", "Italy", "Greece", "Netherlands", "Belgium",
    "Germany", "Poland", "Romania", "United Kingdom", "Ireland", "Norway",
    "Sweden", "Denmark", "Finland", "Estonia", "Latvia", "Lithuania",
    "Switzerland", "Austria", "Czechia", "Slovakia", "Hungary",
    "Slovenia", "Croatia", "Bosnia and Herzegovina", "Serbia", "Montenegro",
    "Albania", "North Macedonia", "Bulgaria", "Moldova", "Ukraine", "Belarus",
    "Luxembourg", "Turkey", "Morocco", "Algeria", "Tunisia", "Malta", "Cyprus",
    "Kosovo",
}

# lon/lat dos portos do explorer
PORTS_LL = {
    "NL_0NLRTM": (4.40, 51.95),    # Rotterdam
    "BE_0BE003": (4.30, 51.30),    # Antwerp-Bruges
    "DE_1DEHAM": (9.97, 53.54),    # Hamburg
    "DE_1DEBRV": (8.55, 53.55),    # Bremerhaven
    "ES_2ESVLC": (-0.32, 39.45),   # Valencia
    "ES_2ESALG": (-5.43, 36.13),   # Algeciras
    "ES_2ESBCN": (2.16, 41.35),    # Barcelona
    "EL_0GRPIR": (23.62, 37.94),   # Piraeus
    "FR_2FRMRS": (5.35, 43.30),    # Marseille
    "FR_1FR001": (0.11, 49.48),    # HAROPA (Le Havre)
    "IT_0ITGOA": (8.92, 44.40),    # Genova
    "IT_0ITGIT": (15.90, 38.45),   # Gioia Tauro
    "PT_0PTSIE": (-8.86, 37.95),   # Sines
    "RO_0ROCND": (28.65, 44.17),   # Constanta
    "PL_0PLGDN": (18.66, 54.40),   # Gdansk
}

# Janela geográfica e projeção equiretangular com correção de latitude média
LON0, LON1 = -11.5, 31.0
LAT0, LAT1 = 34.0, 60.5
KX = math.cos(math.radians(48))   # compressão E-W na latitude média
W = 900.0
S = W / ((LON1 - LON0) * KX)
H = (LAT1 - LAT0) * S


def project(lon, lat):
    x = (lon - LON0) * KX * S
    y = (LAT1 - lat) * S
    return round(x, 1), round(y, 1)


def ring_to_path(ring):
    pts = [project(lon, lat) for lon, lat in ring]
    # simplifica: descarta pontos a menos de 1.2 px do anterior
    keep = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - keep[-1][0]) + abs(p[1] - keep[-1][1]) >= 1.2:
            keep.append(p)
    if len(keep) < 3:
        return ""
    d = f"M{keep[0][0]} {keep[0][1]}"
    for x, y in keep[1:]:
        d += f"L{x} {y}"
    return d + "Z"


def main():
    if LOCAL_CACHE.exists():
        print("Usando cache local:", LOCAL_CACHE)
        geo = json.load(open(LOCAL_CACHE, encoding="utf-8"))
    else:
        print("Baixando contorno dos países (Natural Earth 50m, domínio público)...")
        geo = json.load(urllib.request.urlopen(GEOJSON_URL, timeout=120))
    paths = []
    for f in geo["features"]:
        props = f["properties"]
        nome = props.get("ADMIN") or props.get("name")
        if nome not in COUNTRIES:
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly[:1]:   # só o anel externo
                # pula polígonos totalmente fora da janela
                if not any(LON0 - 3 < lon < LON1 + 3 and LAT0 - 3 < lat < LAT1 + 3
                           for lon, lat in ring):
                    continue
                d = ring_to_path(ring)
                if d:
                    paths.append(d)

    ports_xy = {code: project(lon, lat) for code, (lon, lat) in PORTS_LL.items()}
    payload = {
        "viewBox": f"0 0 {round(W)} {round(H)}",
        "paths": paths,
        "ports_xy": ports_xy,
        "attribution": "Basemap: Natural Earth (public domain)",
    }
    out = HERE / "europe_map.json"
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"europe_map.json: {len(paths)} polígonos, "
          f"{out.stat().st_size / 1024:.0f} KB, viewBox {payload['viewBox']}")


if __name__ == "__main__":
    main()
