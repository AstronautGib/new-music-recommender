"""
build_db.py

Loads data/spotify_songs.csv into a SQLite database (music.db) using the
schema defined in schema.sql.

Usage:
    python build_db.py
"""

import csv
import sqlite3
from pathlib import Path

CSV_PATH = Path("data/spotify_songs.csv")
DB_PATH = Path("music.db")
SCHEMA_PATH = Path("schema.sql")


def build_schema(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())


def get_or_create_artist(conn: sqlite3.Connection, cache: dict, artist_name: str) -> int:
    if artist_name in cache:
        return cache[artist_name]
    cur = conn.execute(
        "INSERT OR IGNORE INTO artists (artist_name) VALUES (?)", (artist_name,)
    )
    if cur.lastrowid and cur.rowcount:
        artist_id = cur.lastrowid
    else:
        artist_id = conn.execute(
            "SELECT artist_id FROM artists WHERE artist_name = ?", (artist_name,)
        ).fetchone()[0]
    cache[artist_name] = artist_id
    return artist_id


def get_or_create_genre(conn: sqlite3.Connection, cache: dict, genre_name: str, subgenre_name: str) -> int:
    key = (genre_name, subgenre_name)
    if key in cache:
        return cache[key]
    cur = conn.execute(
        "INSERT OR IGNORE INTO genres (genre_name, subgenre_name) VALUES (?, ?)",
        (genre_name, subgenre_name),
    )
    if cur.lastrowid and cur.rowcount:
        genre_id = cur.lastrowid
    else:
        genre_id = conn.execute(
            "SELECT genre_id FROM genres WHERE genre_name = ? AND subgenre_name = ?",
            (genre_name, subgenre_name),
        ).fetchone()[0]
    cache[key] = genre_id
    return genre_id


def load_csv(conn: sqlite3.Connection) -> None:
    artist_cache: dict = {}
    genre_cache: dict = {}
    album_seen: set = set()
    track_seen: set = set()

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist_id = get_or_create_artist(conn, artist_cache, row["track_artist"])

            album_id = row.get("track_album_id")
            if album_id and album_id not in album_seen:
                conn.execute(
                    "INSERT OR IGNORE INTO albums (album_id, album_name, release_date) "
                    "VALUES (?, ?, ?)",
                    (album_id, row.get("track_album_name"), row.get("track_album_release_date")),
                )
                album_seen.add(album_id)

            track_id = row["track_id"]
            if track_id not in track_seen:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO tracks (
                        track_id, track_name, artist_id, album_id, popularity,
                        danceability, energy, key_signature, loudness, mode,
                        speechiness, acousticness, instrumentalness, liveness,
                        valence, tempo, duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        track_id,
                        row["track_name"],
                        artist_id,
                        album_id or None,
                        row.get("track_popularity"),
                        row.get("danceability"),
                        row.get("energy"),
                        row.get("key"),
                        row.get("loudness"),
                        row.get("mode"),
                        row.get("speechiness"),
                        row.get("acousticness"),
                        row.get("instrumentalness"),
                        row.get("liveness"),
                        row.get("valence"),
                        row.get("tempo"),
                        row.get("duration_ms"),
                    ),
                )
                track_seen.add(track_id)

            genre_id = get_or_create_genre(
                conn, genre_cache, row.get("playlist_genre"), row.get("playlist_subgenre")
            )
            conn.execute(
                "INSERT OR IGNORE INTO track_genres (track_id, genre_id) VALUES (?, ?)",
                (track_id, genre_id),
            )


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Could not find {CSV_PATH}. Did you download and place the CSV there?")

    if DB_PATH.exists():
        DB_PATH.unlink()  # start fresh each run

    conn = sqlite3.connect(DB_PATH)
    try:
        build_schema(conn)
        load_csv(conn)
        conn.commit()
        track_count = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        artist_count = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
        genre_count = conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
        print(f"Loaded {track_count} tracks, {artist_count} artists, {genre_count} genre/subgenre pairs.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()