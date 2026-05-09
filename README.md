# UFC Elo Engine

A common question in the MMA world: who is the greatest UFC fighter of all time? This project answers that by applying an Elo ranking system — the same math used in chess — to every UFC fight in history.

A web scraper pulls all results from [ufcstats.com](http://ufcstats.com), and an Elo engine processes them chronologically to produce ranked fighter lists. The engine uses a dynamic K-factor: KO and submission finishes carry more weight (K=46) than decisions (K=40), better reflecting the significance of a finish.

## Project Structure

```
backend/
  engine/        — Elo calculation scripts
  scraper/       — Web scraper for ufcstats.com
  api/           — FastAPI backend (rankings, search, fighter profiles)
data/
  raw/           — Input fight data (ufcfights.csv, updated by scraper)
  output/        — Ranked Elo CSVs produced by the engine
frontend/        — React + Vite web app
notebooks/       — Jupyter analysis notebook
docs/            — Documentation
```

## Running the Project

**Set up a virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip3 install pandas numpy requests beautifulsoup4 tqdm
```

**Scrape fresh fight data:**
```bash
python3 backend/scraper/ufcstatswebscraper.py
```

**Run the Elo engine:**
```bash
python3 backend/engine/engine.py
```

Outputs:
- `data/output/k_factor_adjust_current.csv` — all fighters ranked by current Elo
- `data/output/k_adjust_fighter_peak_elo.csv` — all fighters ranked by peak Elo

## How the Elo System Works

- Every fighter starts at 1000
- Expected score: `1 / (1 + 10^((opponent_elo - your_elo) / 400))`
- Rating update: `K × (actual_score - expected_score)`
- KO/submission wins: K=46 &nbsp;|&nbsp; Decision wins: K=40 &nbsp;|&nbsp; Draws: K/2 with 0.5 score &nbsp;|&nbsp; No contests: no change

## Contributors

- [Javier Rodillas](https://github.com/RodillasJavier)
- [Trevor Hicks](https://github.com/NBAtrev) - Original Developer