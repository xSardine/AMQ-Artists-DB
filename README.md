# Project Artist Database

URL: <https://anisongdb.com>

I'm taking in any feedbacks, tho this is just a side project for fun, so I won't promise I will implements your ideas soon (if I will ever). ~~I'll still work more on that than Ege works on AMQ, rest assured~~

The main reason I decided to make this was because I felt like there wasn't any database that was fulfilling my wishes. So I decided to make one myself.

/!\ This is a work in progress, some stuff might not work, some stuff might change.

# Advanced Filters Documentation

## Filters

Here are the different parameters `Advanced Filters` lets you configure:

- `Anime Filter`: The string you enter will need to match an anime in the database (currently, only half of the anime entries have their romaji names associated, because Expand only gives you the English name).
- `Song Name Filter`: The string you enter will need to match a song name in the database.
- `Artist Filter`: The string you enter will need to match an artist in the database: this part is the main enhancement compared to existing database, I will explain it better further down.

- Each of this filters has a box that can be checked:
  - - `Partial Match`: If checked the string will only have to match part of what is in the database. I.E: Let's say you search for `frip`, it will detect `fripSide`, however for artist like `angela` and `YUI`, unchecking it will let you avoid catching stuff like `Angela Aki` or `Yui Horie`.

Then `Artist Filter` have 2 more parameters:

- `Maximum Amount of Other people`: This is the maximum amount of people that are not in your `Artist Filter` field that are allowed. So if you didn't input a group, `1` mean no more than duet.
- `Minimal Amount of group members`: This is only relevant if you're inputing a group name. This will ensure there is a minimal amount of group members singing in the song if it is not the group itself.
  If 0, it will only take the group itself, meaning if all the group members are present in the song but they are not credited as the group itself, it will not include it (Sphere members in Natsuiro Kiseki for example). Setting it to a high number will catch these too but is dumb for groups with only one singer such as fripside where you will catch all Yoshinon Nanjou's.

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

## Thanks

Egerod for making <https://animemusicquiz.com/> and the mods maintaining its database.

MugitBot for providing me with their database, which helped me for the first iteration <https://github.com/CarrC2021/MugiBot>
