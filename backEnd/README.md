# Back End

An anisong database with better artist links and search functions.

Built with [FastAPI](https://fastapi.tiangolo.com/). Live API: [https://anisongdb.com](https://anisongdb.com)

Database sources:

- Expand Library from AMQ: [https://animemusicquiz.com/](https://animemusicquiz.com/)
- MugiBotDatabase: data collected in-game and from ranked pastebins. [https://github.com/CarrC2021/MugiBot](https://github.com/CarrC2021/MugiBot)

Then enhanced automatically or manually by me.

## Running locally

Requires **Python 3.10+**

### Setup

Open a terminal from the repo root

```bash
cd backEnd
python -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Prepare the SQLite database (run from `backEnd/app`). A sample ships at `data/Enhanced-AMQ-Database.sample.db` - a clone of the full database except song links are stripped (except for the first 500 songs).

```bash
cd app
cp data/Enhanced-AMQ-Database.sample.db data/Enhanced-AMQ-Database.db     # Linux / macOS
copy data/Enhanced-AMQ-Database.sample.db data/Enhanced-AMQ-Database.db   # Windows
```

### Start the server

From `backEnd/app`:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API listens on [http://127.0.0.1:8000](http://127.0.0.1:8000)
Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Configuration

Copy [`.env.example`](.env.example) to `.env`.

IP addresses in the log are anonymized. Set an optional salt value `REQUEST_LOG_IP_HASH_SALT`. If empty, a random value is chosen on each startup.

Set `LOG_PASSWORD` and `REVIEW_PASSWORD` for Log and Review access.

In production, set `AUTH_COOKIE_SECURE=true` and `FRONTEND_ORIGINS` to your frontend's origin. 

Restart after configuration changes.

Contributions are stored in `app/data/contributions.db`, created automatically. Reviewers approve original names and artist IDs. Approved changes take effect on the next backend restart; imported catalog database and JSON files stay unchanged.

## Production

Example with Let's Encrypt and Gunicorn (install `gunicorn` separately; run from `backEnd/app`):
Replace the bracketed values with your Let's Encrypt paths and listen IP address.

```bash
sudo gunicorn --keyfile=[PATH_TO_PRIVKEY] --certfile=[PATH_TO_FULLCHAIN] -k uvicorn.workers.UvicornWorker main:app --bind=[HOST]:[PORT]
```
