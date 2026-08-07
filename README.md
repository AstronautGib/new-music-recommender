# New Music Recommender
A SQL-based music recommendation engine that suggests new artists and tracks based on genre, mood, or an artist you already like.

## Why this project

I like R&B, Contemporary, and Rock, but wanted a way to explore new artists in and around those genres. This project builds that recommendation logic from scratch on top of a real music dataset, using SQL to do the heavy lifting.

## How it works

1. Track and audio-feature data (genre, subgenre, danceability, energy, valence, tempo, etc.) is loaded into a local SQLite database.
2. Recommendation queries match on:
   - **Genre** — tracks sharing a genre/subgenre with what you already like
   - **Mood** — tracks with similar energy/valence/tempo profiles
   - **Artist** — tracks similar to a specific artist you name
3. Results are returned as a ranked list of tracks/artists to check out.

## Tech stack

- **Python** — data loading and query scripts
- **SQLite** — local relational database
- **Dataset**: [30,000 Spotify Songs](https://www.kaggle.com/datasets/joebeachcapital/30000-spotify-songs) (Kaggle)

## Setup

1. Clone the repo:
   ```
   git clone <repo-url>
   cd music-recommender
   ```
2. Download the dataset CSV from Kaggle and place it in a `data/` folder (not committed to the repo — see `.gitignore`).
3. Build the database:
   ```
   python build_db.py
   ```
4. Run a recommendation query:
   ```
   python recommend.py --genre "r&b"
   ```

## Project status

Early stage — data model and SQL recommendation logic in progress. A proper CLI/UI is planned as a later step.

## License

MIT