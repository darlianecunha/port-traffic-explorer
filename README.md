# European Port Traffic Explorer

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21144422.svg)](https://doi.org/10.5281/zenodo.21144422)


Interactive explorer of **annual vessel arrivals at 15 major European ports**, by ship type
and size class, built on official **Eurostat** maritime statistics (dataset `mar_tf_qm`,
"Vessels arriving in the main ports by type and size of vessels", quarterly at source,
aggregated to calendar years). No backend, no API key, no build step: one HTML file,
one JSON file, Chart.js from CDN.

## What you can do

- **Automatic highlights**: fastest-growing and steepest-declining port vs 2019, most
  container-dependent port and largest average vessel, computed live from the data
- **Animated map view** (`map.html`): pick a metric (arrivals, growth vs 2019 with
  diverging colours, container share, average vessel size) and press play to watch the
  geography change year by year on a Natural Earth basemap; click a bubble for the
  port's card
- **Change vs 2019**: recovery chart comparing the reference year with the pre-pandemic
  baseline for all ports
- **Select any combination of ports** (chips, map bubbles or ranking-table rows), or hit
  **All ports** to compare the full set at once
- **Annual time series 2019 → present**: arrivals per calendar year and port, filterable by
  ship type (container, liquid bulk, dry bulk, cruise, general cargo…); a year is shown only
  once the port has reported all four quarters
- **Fleet mix**: share of arrivals by ship type in the reference calendar year
- **Size profile**: who receives the mega-ships — arrivals or gross tonnage by GT class
- **Ranking table**: arrivals, GT, average vessel size and cargo-type shares for all 15 ports

Ports included: Rotterdam, Antwerp-Bruges, Hamburg, Bremerhaven, Valencia, Algeciras,
Barcelona, Piraeus, Marseille, HAROPA (Le Havre-Rouen), Genova, Gioia Tauro, Sines,
Constanta, Gdansk. Adding a port is one line in `build_data.py`.

## Files

| File | Purpose |
|---|---|
| `index.html` | The charts page (single file) |
| `map.html` | The animated map view (single file) |
| `data.json` | Aggregated indicators consumed by both pages |
| `build_data.py` | Downloads fresh data from the Eurostat API and rebuilds `data.json` |
| `europe_map.json` | Lightweight SVG basemap + port coordinates for the bubble map |
| `make_map.py` | Regenerates the basemap (Natural Earth, public domain); run only if the port list changes |

## Updating the data

```bash
python3 build_data.py     # fetches the latest quarters from the Eurostat API (~1 min)
```

New quarters are picked up automatically. To change the port list, edit the `PORTS` dict.

## Running / deploying

```bash
python3 -m http.server    # local preview at http://localhost:8000
vercel --prod             # or import the repo at vercel.com (framework: Other)
```

GitHub Pages also works: Settings → Pages → deploy from branch.

## Method notes

- Arrivals are based on **inward declarations** at main ports, covering vessels of 100 GT
  and above (Eurostat maritime transport methodology, Directive 2009/42/EC).
- All annual figures use **closed calendar years** (sum of the four quarters). The reference
  year for fleet mix, size profile and ranking is the latest year fully reported by every
  port (currently 2024), detected automatically at build time. This matches the calendar-year
  convention of the Brazilian (ANTAQ) data used in the companion project.
- Antwerp and Le Havre report under their post-merger entities: **Antwerp-Bruges** (from 2022)
  and **HAROPA, Le Havre-Rouen** (from 2022); their series start in 2022.
- GT size classes are grouped into six readable bands (`<1k` to `>200k` GT).

## Author

**Darliane Ribeiro Cunha, PhD**.
Research: maritime decarbonisation, port sustainability analytics, SDG implementation.

Related projects: [SDG Port Hub](https://sdgporthub.com) ·
[CO₂ Liquid Bulk Calculator](https://co2-liquid-bulk-calculator.vercel.app)

## Licence

Data: © Eurostat, free reuse with attribution. Analysis and site: CC-BY 4.0.
