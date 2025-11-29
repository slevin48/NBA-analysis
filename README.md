# NBA-analysis

Analyze NBA games, teams and players🏀

## Daily game report

This project generates a single-page scoreboard suitable for GitHub Pages deployment. It pulls the latest game summaries from the `nba_api` live scoreboard and writes them to `index.html`.

### Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate the report (defaults to today's games based on the NBA live feed):
   ```bash
   python scripts/generate_index.py
   ```

3. Commit and push `index.html` to publish via GitHub Pages.

### Data source

Game details come from the [nba_api](https://github.com/swar/nba_api) live scoreboard endpoint and include status text, team records, scores, and leading performers.
