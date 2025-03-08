# Back End

 An anisong database with better artists links and search functions

Build with FastAPI: <https://fastapi.tiangolo.com/>

Database source:

- Expand Library from AMQ: <https://animemusicquiz.com/>
- MugiBotDatabase: Data collected from in game as well as Ranked pastebins. <https://github.com/CarrC2021/MugiBot>

Then enhanced automatically/semi-automatically/manually by me.

## Start in Local

From the app folder :

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Start in Production

Using let's encrypt certificate

```bash
sudo gunicorn --keyfile=</path_to_privkey/privkey.pem> --certfile=</path_to_fullchain/fullchain.pem> -k uvicorn.workers.UvicornWorker main:app --bind=<ip_adress>
```

## Database

A sample of the database is available in `backEnd/app/data/Enhanced-AMQ-Database.sample.db` ;
This database is a clone of the entire database, except it doesn't have links for the songs (beside the first 500 songs).  
Rename it to `Enhanced-AMQ-Database.db` to make it work.
