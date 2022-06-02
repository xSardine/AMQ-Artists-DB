# Project Artist Database

URL: <https://anisongdb.com>

I'm taking in any feedbacks, tho this is just a side project for fun, so I won't promise I will implements your ideas soon (if I will ever). ~~I'll still work more on that than Ege works on AMQ, rest assured~~

# Advanced Filters Documentation

The main reason I decided to make this was because I felt like there wasn't any database that was fulfilling my wishes. So I decided to make one myself.

## Filters

Here are the different parameters `Advanced Filters` lets you configure:

- `Anime Filter`: The string you enter will need to match an anime in the database (currently, only half of the anime entries have their romaji names associated, because Expand only gives you the English name).
- `Song Name Filter`: The string you enter will need to match a song name in the database.
- `Artist Filter`: The string you enter will need to match an artist in the database: this part is the main enhancement compared to existing database, I will explain it better further down.

- Each of this filters has 3 boxes linked to it that you can check:
    - - `Partial Match`: If checked the string will only have to match part of what is in the database. I.E: Let's say you search for `frip`, it will detect `fripSide`, however for artist like `angela` and `YUI`, unchecking it will let you avoid catching stuff like `Angela Aki` or `Yui Horie`.
    - - `Ignore Special Caracters`: If checked, it will ignore specials caracters such as ☆, ♪, ō vs ou, etc...
    - - `Case Sensitive`: If checked, it will make your search case sensitive. I.E: If you want to disambiguate people like `ERIKA` (Erika Masaki from Tales of Zestiria and Cocotama), and `Erika` (random ass VA in Animal Yokocho).

Then `Artist Filter` have 2 more parameters:

- `Maximum Amount of Other people`: This is the maximum amount of people that are not in your `Artist Filter` field that are allowed. So if you didn't input a group, `1` mean no more than duet.
- `Minimal Amount of group members`: This is only relevant if you're inputing a group name. This will ensure there is a minimal amount of group members singing in the song if it is not the group itself.
  If 0, it will only take the group itself, meaning if all the group members are present in the song but they are not credited as the group itself, it will not include it (Sphere members in Natsuiro Kiseki for example). Setting it to a  high number will catch these too but can cause problem for groups with only one singer such as fripside.

Finally:

- `Filter Combination`:
    - - `Union`: The song informations will have to match at least one the filter that you entered (anime/song name/artist).
    - - `Intersection`: The song informations will have to match every filter that you entered.
- `Ignore Duplicate`: This will ignore duplicates and only take into account the first instance of [Song Name by Artist] that it has encountered. (Different sets of artists are not considered duplicates)

# Known Database Issues

I know there are some types of edge cases that are not taken into account yet:

- Sometime, there are multiple people credited as singing, but there is one main singer, and the rest are backup and should not be considered as "other people" by the `maximum other people` settings. (Fast example: Smith with MON, where it's basically just SMITH (yu kobayashi) singing.)

I plan to work on this in the future.

# If you want to help me

Feedbacks on the User Interface, new functionalities, etc...

Let me know if you find any of these that are wrong in the DB:

- Any groups that has relevant people in them and not have their members added yet (by relevant, I mean an artist that will make a link between this group and any other group/artist already in the DB)
- Any artists that is not linked with all their alternative names. Alternative names are proper alternative names such as Minami Kuribayashi / exige, but also database inconsistencies like Ayaka ōhashi, Ayaka Ohashi
- Different artists that have the exact same name such as Minami (Kuribayashi) and Minami (DomexKano), etc...
- Groups that have different sets of singers in each songs such as Jam Project, Oratorio, etc...
- And finally, let me know if you find any song I'm missing.

## TODO List

- ~~dark theme~~
- ~~better information modal window~~
- ~~download song list as JSON~~
- ~~mp3 player~~
- ~~quick search button for artists~~
- ~~delete rows from song list to download what you need~~
- ~~quick search button for annId~~
- ~~better access to information modal window to make it more obvious~~
- ~~script to check validity of current exceptions configuration~~
- add an artist dropdown to select them in the artist filter
- ~~searching for artist name in reversed order~~
- ~~Update DB to be able to fix edge cases~~
  - ~~different artists with same names~~
  - ~~same group with different artists~~
- more information in db
  - main singer / backup
  - ~~composer(?)~~
- ~~add domain name~~ + domain path to get history
  - ~~https on fastapi~~
- ~~add date/season on anime entries~~ + date/season filter

## Thanks

Egerod for making <https://animemusicquiz.com/> and the mods maintaining its database.

MugitBot for providing me with their database, which helped me for the first iteration <https://github.com/CarrC2021/MugiBot>
