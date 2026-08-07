-- Music Recommender: SQLite schema
-- Source data: "30,000 Spotify Songs" Kaggle dataset

PRAGMA foreign_keys = ON;

-- One row per unique artist
CREATE TABLE artists (
    artist_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name TEXT NOT NULL UNIQUE
);

-- One row per unique album
CREATE TABLE albums (
    album_id      TEXT PRIMARY KEY,      -- dataset provides a track_album_id
    album_name    TEXT NOT NULL,
    release_date  TEXT                   -- kept as text (YYYY-MM-DD); dataset dates are inconsistent
);

-- Genres and subgenres as seen in the dataset (e.g. genre="r&b", subgenre="new jack swing")
CREATE TABLE genres (
    genre_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name    TEXT NOT NULL,
    subgenre_name TEXT,
    UNIQUE (genre_name, subgenre_name)
);

-- One row per unique track, with audio features attached directly
-- (audio features describe the track itself, not the track-genre pairing,
-- so they belong here rather than in the join table)
CREATE TABLE tracks (
    track_id         TEXT PRIMARY KEY,   -- Spotify track ID from the dataset
    track_name       TEXT NOT NULL,
    artist_id         INTEGER NOT NULL REFERENCES artists(artist_id),
    album_id          TEXT REFERENCES albums(album_id),
    popularity        INTEGER,
    danceability       REAL,
    energy             REAL,
    key_signature       INTEGER,          -- "key" is a SQL reserved-ish word, renamed for clarity
    loudness           REAL,
    mode               INTEGER,
    speechiness         REAL,
    acousticness        REAL,
    instrumentalness    REAL,
    liveness           REAL,
    valence            REAL,
    tempo              REAL,
    duration_ms         INTEGER
);

-- A track can appear under more than one genre/subgenre in the source data
-- (it was pulled from multiple playlists), so this is a many-to-many join
CREATE TABLE track_genres (
    track_id  TEXT NOT NULL REFERENCES tracks(track_id),
    genre_id  INTEGER NOT NULL REFERENCES genres(genre_id),
    PRIMARY KEY (track_id, genre_id)
);

-- Helpful indexes for the recommendation queries you'll write next
CREATE INDEX idx_tracks_artist ON tracks(artist_id);
CREATE INDEX idx_track_genres_genre ON track_genres(genre_id);
CREATE INDEX idx_genres_name ON genres(genre_name);