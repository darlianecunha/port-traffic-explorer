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
    "BE_0BEANR": {"name": "Antwerpen", "country": "BE"},
    "DE_1DEHAM": {"name": "Hamburg", "country": "DE"},
    "DE_1DEBRV": {"name": "Bremerhaven", "country": "DE"},
    "ES_2ESVLC": {"name": "Valencia", "country": "ES"},
    "ES_2ESALG": {"name": "Algeciras", "country": "ES"},
    "ES_2ESBCN": {"name": "Barcelona", "country": "ES"},
    "EL_0GRPIR": {"name": "Piraeus", "country": "GR"},
    "FR_2FRMRS": {"name": "Marseille", "country": "FR"},
    "FR_1FRLEH": {"name": "Le Havre", "country": "FR"},
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
    all_quarters = set()
    vessel_labels = {}
    series = {}
    size_latest = {}
    totals_latest = {}

    for code, info in PORTS.items():
        print("Fetching", info["name"], "...")
        js = fetch(code)
        dims, cats, val = unpack(js)
        vessel_labels.update(js["dimension"]["vessel"]["category"]["label"])
        quarters = cats["time"]
        all_quarters.update(quarters)

        def get(tonnage, vessel, unit, t):
            return val.get(("Q", tonnage, vessel, unit, code, t))

        # series por tipo (tonnage TOTAL, unidade NR)
        series[code] = {}
        for v in cats["vessel"]:
            row = [get("TOTAL", v, "NR", t) for t in quarters]
            if any(x is not None for x in row):
                series[code][v] = row

        # perfil de tamanho: soma dos ultimos 4 trimestres com dado (vessel TOTAL)
        with_data = [t for t in quarters
                     if get("TOTAL", "TOTAL", "NR", t) is not None]
        last4 = with_data[-4:]
        size_latest[code] = {}
        for label, group in SIZE_GROUPS:
            nr = sum(get(g, "TOTAL", "NR", t) or 0 for g in group for t in last4)
            gt = sum(get(g, "TOTAL", "THS_GT", t) or 0 for g in group for t in last4)
            size_latest[code][label] = {"nr": int(nr), "gt": round(gt, 1)}
        totals_latest[code] = {
            "nr": int(sum(get("TOTAL", "TOTAL", "NR", t) or 0 for t in last4)),
            "gt": round(sum(get("TOTAL", "TOTAL", "THS_GT", t) or 0 for t in last4), 1),
            "window": f"{last4[0]} to {last4[-1]}" if last4 else None,
        }
        _time.sleep(1)   # gentileza com a API

    quarters = sorted(all_quarters)
    # normaliza series para a grade comum de trimestres
    for code in series:
        js_q = None  # cada porto ja esta na mesma grade (sinceTimePeriod)
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
        "ports": [{"code": c, **PORTS[c]} for c in PORTS],
        "vessel_labels": vessel_labels,
        "size_groups": [g[0] for g in SIZE_GROUPS],
        "series": series,
        "size_latest": size_latest,
        "totals_latest": totals_latest,
    }
    (HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False),
                                    encoding="utf-8")
    kb = (HERE / "data.json").stat().st_size / 1024
    print(f"\ndata.json written: {len(PORTS)} ports, {len(quarters)} quarters, "
          f"{kb:.0f} KB")


if __name__ == "__main__":
    main()
