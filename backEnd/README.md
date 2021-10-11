# Back End
 An anisong database with better artists links and search functions

Build with FastAPI: https://fastapi.tiangolo.com/
Currently the API is just taking datas from JSONs, however I do have an SQL database design in mind.

Database source: 
- Expand Library from AMQ: https://animemusicquiz.com/
- MugiBotDatabase: Data collected from in game as well as Ranked pastebins. https://github.com/CarrC2021/MugiBot
- Data collected by Husa when playing with the S/A script on AMQ (mainly for getting romaji names)

Then enhanced automatically/semi-automatically/manually:
- Automatically split artists with regex
- Add exceptions for artists that shouldn't be splitted by those regex
- Find semi-automatically every artists that are seemingly the same person but with a variation/typo
- Add manually group members
- Fix manually edge cases such as different artist with same name
- Currently: Fixing what has gone through the net