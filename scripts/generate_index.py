from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from nba_api.live.nba.endpoints import scoreboard


def _format_leader(raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not raw or raw.get("personId", 0) == 0:
        return None

    return {
        "name": raw.get("name", ""),
        "points": raw.get("points", 0),
        "rebounds": raw.get("rebounds", 0),
        "assists": raw.get("assists", 0),
    }


def fetch_games(game_date: Optional[str] = None) -> tuple[str, List[Dict[str, Any]]]:
    board = scoreboard.ScoreBoard(game_date=game_date) if game_date else scoreboard.ScoreBoard()
    board_dict = board.get_dict()["scoreboard"]

    summaries: List[Dict[str, Any]] = []
    for game in board.games.get_dict():
        home = game["homeTeam"]
        away = game["awayTeam"]

        summaries.append(
            {
                "id": game["gameId"],
                "status_text": game.get("gameStatusText", ""),
                "status": game.get("gameStatus", 0),
                "clock": game.get("gameClock"),
                "period": game.get("period"),
                "start_time": game.get("gameEt"),
                "home": {
                    "city": home.get("teamCity", ""),
                    "name": home.get("teamName", ""),
                    "tricode": home.get("teamTricode", ""),
                    "wins": home.get("wins", 0),
                    "losses": home.get("losses", 0),
                    "score": home.get("score", 0),
                },
                "away": {
                    "city": away.get("teamCity", ""),
                    "name": away.get("teamName", ""),
                    "tricode": away.get("teamTricode", ""),
                    "wins": away.get("wins", 0),
                    "losses": away.get("losses", 0),
                    "score": away.get("score", 0),
                },
                "leaders": {
                    "home": _format_leader(game.get("gameLeaders", {}).get("homeLeaders")),
                    "away": _format_leader(game.get("gameLeaders", {}).get("awayLeaders")),
                },
            }
        )

    return board_dict["gameDate"], summaries


def _leader_line(label: str, leader: Dict[str, Any]) -> str:
    return (
        f"<p class='leader'><span class='leader-label'>{escape(label)}:</span> "
        f"{escape(leader['name'])} — {leader['points']} PTS, {leader['rebounds']} REB, {leader['assists']} AST</p>"
    )


def render_html(game_date: str, games: List[Dict[str, Any]]) -> str:
    updated_at = datetime.now(UTC).strftime("%B %d, %Y %H:%M UTC")

    cards: List[str] = []
    for game in games:
        home = game["home"]
        away = game["away"]

        status_extra = ""
        if game["status"] == 1 and game["start_time"]:
            status_extra = f"Tip-off: {escape(game['start_time'])}"
        elif game["status"] == 2:
            period_text = f"Q{game['period']}" if game.get("period") else "Live"
            clock = game.get("clock") or "Live"
            status_extra = f"{period_text} — {escape(clock)}"

        leaders_block = ""
        if game["leaders"]["home"] or game["leaders"]["away"]:
            leader_lines = []
            if game["leaders"]["home"]:
                leader_lines.append(_leader_line(f"{home['tricode']} leader", game["leaders"]["home"]))
            if game["leaders"]["away"]:
                leader_lines.append(_leader_line(f"{away['tricode']} leader", game["leaders"]["away"]))
            leaders_block = "<div class='leaders'>" + "".join(leader_lines) + "</div>"

        cards.append(
            f"<article class='game-card'>"
            f"<header><p class='game-id'>Game ID: {escape(game['id'])}</p>"
            f"<p class='status'>{escape(game['status_text'])}</p>"
            f"<p class='status-extra'>{status_extra}</p></header>"
            f"<div class='teams'>"
            f"<div class='team away'><p class='team-name'>{escape(away['city'])} {escape(away['name'])} ({away['tricode']})" \
            f"<span class='record'>{away['wins']}-{away['losses']}</span></p><p class='score'>{away['score']}</p></div>"
            f"<div class='team home'><p class='team-name'>{escape(home['city'])} {escape(home['name'])} ({home['tricode']})" \
            f"<span class='record'>{home['wins']}-{home['losses']}</span></p><p class='score'>{home['score']}</p></div>"
            f"</div>{leaders_block}</article>"
        )

    games_section = "".join(cards) if cards else "<p class='no-games'>No games scheduled for today.</p>"

    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <title>NBA Daily Scoreboard</title>
  <style>
    :root {{
      --bg: #0b0c10;
      --panel: #1f2833;
      --accent: #66fcf1;
      --muted: #c5c6c7;
      --text: #f8f8f8;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; background: var(--bg); color: var(--text); }}
    header.page {{ padding: 2rem 1.25rem; text-align: center; border-bottom: 2px solid var(--panel); }}
    header.page h1 {{ margin: 0 0 0.4rem; letter-spacing: 0.05em; }}
    header.page p {{ margin: 0.2rem 0; color: var(--muted); }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
    .game-card {{ background: var(--panel); border-radius: 12px; padding: 1rem; box-shadow: 0 6px 18px rgba(0,0,0,0.25); border: 1px solid rgba(102, 252, 241, 0.15); }}
    .game-card header {{ border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.75rem; margin-bottom: 0.75rem; }}
    .game-id {{ font-size: 0.75rem; color: var(--muted); margin: 0; letter-spacing: 0.04em; }}
    .status {{ margin: 0.1rem 0; font-weight: 600; font-size: 1.1rem; color: var(--accent); }}
    .status-extra {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
    .teams {{ display: grid; grid-template-columns: 1fr; gap: 0.4rem; }}
    .team {{ display: flex; justify-content: space-between; align-items: baseline; padding: 0.4rem 0.25rem; }}
    .team-name {{ margin: 0; font-weight: 600; }}
    .record {{ color: var(--muted); font-weight: 400; font-size: 0.85rem; margin-left: 0.35rem; }}
    .score {{ font-size: 1.8rem; font-weight: 700; margin: 0; }}
    .leaders {{ margin-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.5rem; }}
    .leader {{ margin: 0.2rem 0; color: var(--muted); font-size: 0.95rem; }}
    .leader-label {{ color: var(--accent); font-weight: 600; margin-right: 0.35rem; }}
    .no-games {{ grid-column: 1 / -1; text-align: center; color: var(--muted); font-size: 1.05rem; }}
    footer {{ text-align: center; padding: 1rem; color: var(--muted); font-size: 0.9rem; }}
    @media (max-width: 560px) {{
      main {{ padding: 1rem; }}
      .score {{ font-size: 1.5rem; }}
    }}
  </style>
</head>
<body>
  <header class='page'>
    <h1>NBA Daily Scoreboard</h1>
    <p>Game date: {escape(game_date)}</p>
    <p>Updated: {updated_at}</p>
  </header>
  <main>
    {games_section}
  </main>
  <footer>
    <p>Data from nba_api live scoreboard.</p>
  </footer>
</body>
</html>
"""


def generate_report(output_path: Path, game_date: Optional[str] = None) -> None:
    game_date_str, games = fetch_games(game_date)
    html = render_html(game_date_str, games)
    output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    generate_report(project_root / "index.html")
    print("Generated index.html")
