#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data.py
Downloads quarterly vessel-traffic statistics for major European ports from the
Eurostat API (dataset mar_tf_qm: "Vessels arriving in the main ports by type
and size of vessels") and aggregates them into data.json for the static site.

No API key required. Re-run any time to refresh (new quarters appear
automatically). Add or remove ports in the PORTS dict below.
"""
from __future__ import annotations
import json
import time as _time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
       "mar_tf_qm?format=JSON&lang=EN&sinceTimePeriod=2019-Q1&rep_mar={port}")

PORTS = {
    "NL_0NLRTM": {"name": "Rotterdam", "country": "NL"},
    "BE_0BE003": {"name": "Antwerp-Bruges", "country": "BE"},
    "DE_1DEHAM": {"name": "Hamburg", "country": "DE"},
    "DE_1DEBRV": {"name": "Bremerhaven", "country": "DE"},
    "ES_2ESVLC": {"name": "Valencia", "country": "ES"},
    "ES_2ESALG": {"name": "Algeciras", "country": "ES"},
    "ES_2ESBCN": {"name": "Barcelona", "country": "ES"},
    "EL_0GRPIR": {"name": "Piraeus", "country": "GR"},
    "FR_2FRMRS": {"name": "Marseille", "country": "FR"},
    "FR_1FR001": {"name": "HAROPA (Le Havre-Rouen)", "country": "FR"},
    "IT_0ITGOA": {"name": "Genova", "country": "IT"},
    "IT_0ITGIT": {"name": "Gioia Tauro", "country": "IT"},
    "PT_0PTSIE": {"name": "Sines", "country": "PT"},
    "RO_0ROCND": {"name": "Constanta", "country": "RO"},
    "PL_0PLGDN": {"name": "Gdansk", "country": "PL"},
}

# Agrupamento de classes de GT em 6 faixas legiveis
SIZE_GROUPS = [
    ("<1k GT", ["GT_LT100", "GT100-499", "GT500-999"]),
    ("1-10k GT", ["GT1000-1999", "GT2000-2999", "GT3000-3999", "GT4000-4999",
                   "GT5000-5999", "GT6000-6999", "GT7000-7999", "GT8000-8999",
                   "GT9000-9999"]),
    ("10-50k GT", ["GT10000-19999", "GT20000-29999", "GT30000-39999",
                    "GT40000-49999"]),
    ("50-100k GT", ["GT50000-79999", "GT80000-99999"]),
    ("100-200k GT", ["GT100000-149999", "GT150000-199999"]),
    (">200k GT", ["GT200000-249999", "GT250000-299999", "GT_GE300000"]),
]


def fetch(port_code):
    url = API.format(port=port_code)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  retry {port_code}: {e}")
            _time.sleep(3)


def unpack(js):
    """JSON-stat -> dict[(dim tuple)] = value, plus category orders."""
    dims = js["id"]
    sizes = js["size"]
    cats = {d: list(js["dimension"][d]["category"]["index"].keys()) for d in dims}
    out = {}
    for flat, val in js["value"].items():
        idx = int(flat)
        coords = []
        for s in reversed(sizes):
            coords.append(idx % s)
            idx //= s
        coords = coords[::-1]
        key = tuple(cats[d][c] for d, c in zip(dims, coords))
        out[key] = val
    return dims, cats, out


def main():
    # 1a passada: baixa tudo e guarda cru, por porto
    raw = {}
    vessel_labels = {}
    all_quarters = set()
    for code, info in PORTS.items():
        print("Fetching", info["name"], "...")
        js = fetch(code)
        dims, cats, val = unpack(js)
        vessel_labels.update(js["dimension"]["vessel"]["category"]["label"])
        all_quarters.update(cats["time"])
        raw[code] = {"cats": cats, "val": val}
        _time.sleep(1)   # gentileza com a API

    quarters = sorted(all_quarters)

    def get(code, tonnage, vessel, unit, t):
        return raw[code]["val"].get(("Q", tonnage, vessel, unit, code, t))

    # 2a passada: series alinhadas a grade comum de trimestres
    series = {}
    for code in PORTS:
        series[code] = {}
        for v in raw[code]["cats"]["vessel"]:
            row = [get(code, "TOTAL", v, "NR", t) for t in quarters]
            if any(x is not None for x in row):
                series[code][v] = row

    # Ano de referencia: ultimo ano-calendario com os 4 trimestres reportados
    # em TODOS os portos (mesma convencao que sera usada no Brasil/ANTAQ)
    years = sorted({t[:4] for t in quarters})
    ref_year = None
    for y in years:
        qs = [f"{y}-Q{i}" for i in (1, 2, 3, 4)]
        if all(q in quarters for q in qs) and all(
                all(get(c, "TOTAL", "TOTAL", "NR", q) is not None for q in qs)
                for c in PORTS):
            ref_year = y
    if ref_year is None:
        raise SystemExit("Nenhum ano-calendario completo para todos os portos.")
    ref_qs = [f"{ref_year}-Q{i}" for i in (1, 2, 3, 4)]
    print("Ano de referencia (fechado):", ref_year)

    # Agregados do ano de referencia
    size_year = {}
    totals_year = {}
    for code in PORTS:
        size_year[code] = {}
        for label, group in SIZE_GROUPS:
            nr = sum(get(code, g, "TOTAL", "NR", t) or 0
                     for g in group for t in ref_qs)
            gt = sum(get(code, g, "TOTAL", "THS_GT", t) or 0
                     for g in group for t in ref_qs)
            size_year[code][label] = {"nr": int(nr), "gt": round(gt, 1)}
        totals_year[code] = {
            "nr": int(sum(get(code, "TOTAL", "TOTAL", "NR", t) or 0 for t in ref_qs)),
            "gt": round(sum(get(code, "TOTAL", "TOTAL", "THS_GT", t) or 0
                            for t in ref_qs), 1),
        }

    payload = {
        "meta": {
            "source": "Eurostat, mar_tf_qm (Vessels arriving in the main ports "
                      "by type and size), quarterly",
            "api": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/",
            "generated": __import__("datetime").date.today().isoformat(),
            "note_brazil": "Brazilian comparison layer will be added when the "
                           "ANTAQ portal returns.",
        },
        "quarters": quarters,
        "ref_year": ref_year,
        "ports": [{"code": c, **PORTS[c]} for c in PORTS],
        "vessel_labels": vessel_labels,
        "size_groups": [g[0] for g in SIZE_GROUPS],
        "series": series,
        "size_year": size_year,
        "totals_year": totals_year,
    }
    (HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False),
                                    encoding="utf-8")
    kb = (HERE / "data.json").stat().st_size / 1024
    print(f"\ndata.json written: {len(PORTS)} ports, {len(quarters)} quarters, "
          f"ref year {ref_year}, {kb:.0f} KB")


if __name__ == "__main__":
    main()
