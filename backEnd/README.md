# Back End

 An anisong database with better artists links and search functions

Build with FastAPI: <https://fastapi.tiangolo.com/>

Database source:

- Expand Library from AMQ: <https://animemusicquiz.com/>
- MugiBotDatabase: Data collected from in game as well as Ranked pastebins. <https://github.com/CarrC2021/MugiBot>

Then enhanced automatically/semi-automatically/manually:

- Automatically split artists with regex
- Add exceptions for artists that shouldn't be splitted by those regex
- Find semi-automatically every artists that are seemingly the same person but with a variation/typo
- Add manually group members
- Fix manually edge cases such as different artist with same name
- Currently: Fixing what has gone through the net

## Get expand.json

```js
new Listener("expandLibrary questions", (payload) => {
  console.log(payload)
}).bindListener()
socket.sendCommand({
    type: "library",
    command: "expandLibrary questions"
})
```

## Start in Local

uvicorn main:app --host 127.0.0.1 --port 8000 --reload

## Start in Production

Using let's encrypt certificate

sudo gunicorn --keyfile=</path_to_privkey/privkey.pem> --certfile=</path_to_fullchain/fullchain.pem> -k uvicorn.workers.UvicornWorker main:app --bind=<ip_adress>
