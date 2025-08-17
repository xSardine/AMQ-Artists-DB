# Back End

 An anisong database with better artists links and search functions

Build with FastAPI: <https://fastapi.tiangolo.com/>

Database source:

- Expand Library from AMQ: <https://animemusicquiz.com/>
- MugiBotDatabase: Data collected from in game as well as Ranked pastebins. <https://github.com/CarrC2021/MugiBot>

Then enhanced automatically/semi-automatically/manually by me.

## Running locally

Install Python 3.12 or above [here](https://www.python.org/downloads/).

Create a virtual environment :

```bash
python -m venv venv
```

Activate the virtual environment :

```bash
source venv/bin/activate # Linux
venv\Scripts\activate # Windows
```

Install the python dependencies :

```bash
pip install -r requirements.txt
```

Rename `app/data/Enhanced-AMQ-Database.sample.db` to `app/data/Enhanced-AMQ-Database.db`.

```bash
cp app/data/Enhanced-AMQ-Database.sample.db app/data/Enhanced-AMQ-Database.db # Linux
copy app\data\Enhanced-AMQ-Database.sample.db app\data\Enhanced-AMQ-Database.db # Windows
```

Move to the app folder :

```bash
cd app
```

From within the app folder :

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The app will run on http://127.0.0.1:8000 by default. 

I.E, to call the `search_request` endpoint, the call must be made to http://127.0.0.1:8000/api/search_request.

The associated documentation can be found at <http://127.0.0.1:8000/docs> or <http://127.0.0.1:8000/redoc>.

## Start in Production

Using let's encrypt certificate

```bash
sudo gunicorn --keyfile=</path_to_privkey/privkey.pem> --certfile=</path_to_fullchain/fullchain.pem> -k uvicorn.workers.UvicornWorker main:app --bind=<ip_adress>
```

## Database

A sample of the database is available in `backEnd/app/data/Enhanced-AMQ-Database.sample.db` ;
This database is a clone of the entire database, except it doesn't have links for the songs (beside the first 500 songs).  
Rename it to `Enhanced-AMQ-Database.db` to make it work.
