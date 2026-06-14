# Back End

An anisong database with better artist links and search functions.

Built with [FastAPI](https://fastapi.tiangolo.com/). Live API: [https://anisongdb.com](https://anisongdb.com)

Database sources:

- Expand Library from AMQ: [https://animemusicquiz.com/](https://animemusicquiz.com/)
- MugiBotDatabase: data collected in-game and from ranked pastebins. [https://github.com/CarrC2021/MugiBot](https://github.com/CarrC2021/MugiBot)

Then enhanced automatically or manually by me.

## Running locally

Requires **Python 3.10+** ([downloads](https://www.python.org/downloads/)).

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

The API listens on [http://127.0.0.1:8000](http://127.0.0.1:8000). Example: `POST http://127.0.0.1:8000/api/search_request`.

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) or [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

### Request log (optional)

The API serves an in-memory request log viewer from `backEnd/app/log-viewer.html`. Copy `backEnd/.env.example` to `backEnd/.env` and set `REQUEST_LOG_URL_SEGMENT` to the URL path segment you want. Defaults to `log` if `.env` is missing or the segment is blank. Restart the server after changing `.env`.

- Viewer: `http://127.0.0.1:8000/log` (or your custom segment)
- JSON feed: `http://127.0.0.1:8000/log/feed`

## Production

Example with Let's Encrypt and Gunicorn (install `gunicorn` separately; run from `backEnd/app`):
Replace the bracketed values with your Let's Encrypt paths and listen IP address.

```bash
sudo gunicorn --keyfile=[PATH_TO_PRIVKEY] --certfile=[PATH_TO_FULLCHAIN] -k uvicorn.workers.UvicornWorker main:app --bind=[HOST]:[PORT]
```
