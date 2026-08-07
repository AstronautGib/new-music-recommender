"""
recommend.py

Query music.db for track recommendations based on genre, mood, or a seed artist.

Usage:
    python recommend.py --genre "r&b"
    python recommend.py --mood energetic
    python recommend.py --artist "Artist"
"""

import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path("music.db")

# Rough mood -> audio feature thresholds. These are starting points, not
# scientifically tuned -- tweak once you see real results.
MOOD_PROFILES = {
    "energetic": "energy > 0.7 AND tempo > 120",
    "chill":     "energy < 0.4 AND acousticness > 0.3",
    "happy":     "valence > 0.7",
    "sad":       "valence < 0.3",
    "dance":     "danceability > 0.7",
}


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit("music.db not found. Run build_db.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def recommend_by_genre(
    conn: sqlite3.Connection, genre: str, limit: int = 15, max_popularity: int = 60
) -> list[sqlite3.Row]:
    # A track can be tagged under multiple subgenres of the same genre
    # (e.g. two different r&b subgenres), so group by track to avoid
    # duplicate rows for the same track.
    #
    # max_popularity caps how mainstream results can be -- without this,
    # results skew toward songs you've almost certainly already heard.
    # Within that capped range we still sort by popularity DESC so you get
    # the "best of the lesser-known" rather than pure obscurity/noise.
    query = """
        SELECT t.track_id, t.track_name, a.artist_name, t.popularity
        FROM tracks t
        JOIN artists a ON t.artist_id = a.artist_id
        JOIN track_genres tg ON t.track_id = tg.track_id
        JOIN genres g ON tg.genre_id = g.genre_id
        WHERE LOWER(g.genre_name) = LOWER(?)
          AND t.popularity <= ?
        GROUP BY t.track_id
        ORDER BY t.popularity DESC
        LIMIT ?
    """
    return conn.execute(query, (genre, max_popularity, limit)).fetchall()
 

def recommend_by_mood(
    conn: sqlite3.Connection, mood: str, limit: int = 15, max_popularity: int = 60
) -> list[sqlite3.Row]:
    mood = mood.lower()
    if mood not in MOOD_PROFILES:
        valid = ", ".join(MOOD_PROFILES.keys())
        raise SystemExit(f"Unknown mood '{mood}'. Try one of: {valid}")
 
    condition = MOOD_PROFILES[mood]
    query = f"""
        SELECT DISTINCT t.track_name, a.artist_name, t.popularity,
               t.energy, t.valence, t.danceability, t.tempo
        FROM tracks t
        JOIN artists a ON t.artist_id = a.artist_id
        WHERE {condition}
          AND t.popularity <= ?
        ORDER BY t.popularity DESC
        LIMIT ?
    """
    return conn.execute(query, (max_popularity, limit)).fetchall()
 

def recommend_by_artist(
    conn: sqlite3.Connection, artist_name: str, limit: int = 15, max_popularity: int = 60
) -> list[sqlite3.Row]:
    # Strategy: find genres the seed artist's tracks belong to, then find
    # other artists who show up in those same genres, ranked by popularity.
    query = """
        SELECT t.track_id, t.track_name, a.artist_name, t.popularity
        FROM tracks t
        JOIN artists a ON t.artist_id = a.artist_id
        JOIN track_genres tg ON t.track_id = tg.track_id
        WHERE tg.genre_id IN (
            SELECT DISTINCT tg2.genre_id
            FROM tracks t2
            JOIN artists a2 ON t2.artist_id = a2.artist_id
            JOIN track_genres tg2 ON t2.track_id = tg2.track_id
            WHERE LOWER(a2.artist_name) = LOWER(?)
        )
        AND LOWER(a.artist_name) != LOWER(?)
        AND t.popularity <= ?
        GROUP BY t.track_id
        ORDER BY t.popularity DESC
        LIMIT ?
    """
    return conn.execute(query, (artist_name, artist_name, max_popularity, limit)).fetchall()
  

def print_results(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("No results found.")
        return
    for row in rows:
        keys = row.keys()
        line = f"{row['track_name']} — {row['artist_name']}"
        if "popularity" in keys and row["popularity"] is not None:
            line += f" (popularity: {row['popularity']})"
        print(line)
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Get music recommendations by genre, mood, or artist.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--genre", help="e.g. r&b, rock, pop")
    group.add_argument("--mood", help=f"one of: {', '.join(MOOD_PROFILES.keys())}")
    group.add_argument("--artist", help="a seed artist to find similar artists from")
    parser.add_argument("--limit", type=int, default=15, help="number of results to return")
    parser.add_argument(
        "--max-popularity",
        type=int,
        default=60,
        help="only surface tracks at or below this popularity score (0-100). "
             "Lower = more obscure/discovery-focused. Default 60.",
    )
    args = parser.parse_args()
 
    conn = connect()
    try:
        if args.genre:
            rows = recommend_by_genre(conn, args.genre, args.limit, args.max_popularity)
        elif args.mood:
            rows = recommend_by_mood(conn, args.mood, args.limit, args.max_popularity)
        else:
            rows = recommend_by_artist(conn, args.artist, args.limit, args.max_popularity)
        print_results(rows)
    finally:
        conn.close()
 
if __name__ == "__main__":
    main()
