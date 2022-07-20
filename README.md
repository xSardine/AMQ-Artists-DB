# Project Artist Database

URL: <https://anisongdb.com>

I'm taking in any feedbacks, tho this is just a side project for fun, so I won't promise I will implements your ideas soon (if I will ever). ~~I'll still work more on that than Ege works on AMQ, rest assured~~

The main reason I decided to make this was because I felt like there wasn't any database that was fulfilling my wishes. So I decided to make one myself.

/!\ This is a work in progress, some stuff might not work, some stuff might change.

# Advanced Filters Documentation

Advanced Filters will let you search specifically for an artist, a composer, a song name or an anime name (along with other settings defined below)

Each of this element has a box that can be checked:

- `Partial Match`: If checked the string will only have to match part of what is in the database. I.E: Let's say you search for `frip`, it will detect `fripSide`, however for artist like `angela` and `YUI`, unchecking it will let you avoid catching stuff like `Angela Aki` or `Yui Horie`.

Then `Artist Filter` have 2 more parameters:

- `Max Other People`: This is the maximum amount of people that are not in your `Artist Filter` field that are allowed. So if you didn't input a group, `1` mean no more than duet.
- `Min group members`: This is only relevant if you're inputing a group name. This will ensure there is a minimal amount of group members singing in the song if it is not the group itself.
  If 0, it will only take the group itself, meaning if all the group members are present in the song but they are not credited as the group itself, it will not include it (Sphere members in Natsuiro Kiseki for example). Setting it to a high number will catch these too but is dumb for groups with only one singer such as fripside where you will catch all Yoshino Nanjou's.

Finally:

- `Filter Combination`:
  - `Union`: The song informations will have to match at least one the filter that you entered (anime/song name/artist/composer).
  - `Intersection`: The song informations will have to match every filter that you entered.
- `Ignore Duplicate`: This will ignore duplicates and only take into account the first instance of [Song Name by Artist] that it has encountered. (Different sets of artists are not considered duplicates)

# Known Database Issues

I know there are some problems:

- Sometime, there are multiple people credited as singing, but there is one main singer, and the rest are backup and should not be considered as "other people" by the `maximum other people` settings. (Fast example: Smith with MON, where it's basically just SMITH (yu kobayashi) singing)
- Composers and Arrangers are a work in progress

I plan to work on this in the future.

The database is based of AMQ database, which means it also import its problems. Some song might be missing because they either are not in AMQ or because it doesn't fit AMQ requirements of what can be added. Some artists might have inconsistent name, some song names might be improperly romanized and stuff like this. All of this will not be fixed unless it is fixed in AMQ as I want to keep a 1:1 relation with their database (+ anything that I added myself), so I invite you to ask for such change directly on the AMQ discord after carefully reading the pins on how to request such changes.

# If you want to help me

Feedbacks on the User Interface, new functionalities, etc...

Let me know if you find any of these that are not properly done in the DB:

- Any groups that has relevant people missing (by relevant, I mean an artist that will make a link between this group and any other group/artist already in the DB)
- Any artists that is not linked with all their alternative names. Alternative names are proper alternative names such as Minami Kuribayashi / exige, but also database inconsistencies like Akari Kitou and Akari Kito
- Different artists that have the exact same name such as Minami (Kuribayashi) and Minami (DomexKano), etc...
- Groups that have different sets of singers in each songs such as Jam Project, Oratorio, etc...
- And finally, let me know if you find any song that is in AMQ and is missing in the DB

You can either DM me on Discord: xSardine#8168 for simple requests (such as database fixes), or open an issue on this repository.

## Thanks

Egerod for making <https://animemusicquiz.com/> and the mods maintaining its database.

MugitBot for providing me with their database, which helped me for the first iteration <https://github.com/CarrC2021/MugiBot>
