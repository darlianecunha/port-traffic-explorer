# European Port Traffic Explorer

Interactive explorer of **quarterly vessel arrivals at 15 major European ports**, by ship type
and size class, built on official **Eurostat** maritime statistics (dataset `mar_tf_qm`,
"Vessels arriving in the main ports by type and size of vessels"). No backend, no API key,
no build step: one HTML file, one JSON file, Chart.js from CDN.

## What you can do

- **Select any combination of ports** (chips or ranking-table rows), or hit **All ports**
  to compare the full set at once
- **Time series 2019 → present**: quarterly arrivals per port, filterable by ship type
  (container, liquid bulk, dry bulk, cruise, general cargo…)
- **Fleet mix**: share of arrivals by ship type in each port's last four reported quarters
- **Size profile**: who receives the mega-ships — arrivals or gross tonnage by GT class
- **Ranking table**: arrivals, GT, average vessel size and cargo-type shares for all 15 ports

Ports included: Rotterdam, Antwerpen, Hamburg, Bremerhaven, Valencia, Algeciras, Barcelona,
Piraeus, Marseille, Le Havre, Genova, Gioia Tauro, Sines, Constanta, Gdansk.
Adding a port is one line in `build_data.py`.

## Brazil layer (planned)

When the Brazilian ANTAQ portal returns, this explorer will show Brazilian ports (Santos,
Itaqui, Paranaguá, Itaguaí and the rest of the top 20) side by side with the European ones,
on the same quarterly grid, connected to the *Brazil Vessel Call Intelligence* platform.

## Files

| File | Purpose |
|---|---|
| `index.html` | The interactive site (single file) |
| `data.json` | Aggregated indicators consumed by the page |
| `build_data.py` | Downloads fresh data from the Eurostat API and rebuilds `data.json` |

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
- "Last four reported quarters" uses each port's most recent quarters with data, so the
  exact window may differ slightly between ports.
- GT size classes are grouped into six readable bands (`<1k` to `>200k` GT).

## Author

**Darliane Ribeiro Cunha, PhD** — Professor, Federal University of Maranhão (UFMA).
Research: maritime decarbonisation, port sustainability analytics, SDG implementation.

Related projects: [SDG Port Hub](https://sdgporthub.com) ·
[CO₂ Liquid Bulk Calculator](https://co2-liquid-bulk-calculator.vercel.app)

## Licence

Data: © Eurostat, free reuse with attribution. Analysis and site: CC-BY 4.0.
