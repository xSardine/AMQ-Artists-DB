# Project Artist Database

**Live site:** [anisongdb.com](https://anisongdb.com)

An anime song database based on [AMQ](https://animemusicquiz.com/), with extra artist metadata (aliases, group memberships, line-ups) and multi-field search. Feedback is welcome. This is a side project, so feature requests may take a while (or never happen).

> **Warning**  
> Work in progress. Some features may be broken or change without notice.

## Advanced Filters

Open **Advanced Filters** to search each field independently instead of using one combined search box.

Each text field has a **Partial Match** checkbox. When enabled, the query only needs to match part of the stored value (e.g. `frip` matches `fripSide`). Disable it to avoid false positives such as `angela` matching `Angela Aki`, or `YUI` matching `Yui Horie`.

**Artist Filter** adds two settings:

- **Max Other People**: How many other credited performers are allowed on the song besides the artist or group you searched for. At `0`, only solo credits match (e.g. searching LiSA returns songs credited to LiSA alone). At `1`, at most one extra performer is allowed (a duet). The default is `99` (effectively no limit).
- **Min Group Members**: Only applies when your artist search matches a group. Sets how many of that group's members must appear on the song when it is credited under individual names instead of the group name. At `0`, only a direct group credit counts (e.g. Sphere members singing in *Natsuiro Kiseki* under their own names are excluded). Higher values include those songs but can also match unrelated work by solo members (e.g. all Yoshino Nanjo songs when searching fripSide).

**Filter Combination** (how the anime, song, artist, and composer fields combine):

- **Union**: A song can match any one active field (OR logic).
- **Intersection**: A song must match every active field (AND logic).

**Ignore Duplicate**: When the same song name and credited artist string appear on multiple anime, keep one row. If duplicates differ by anime, the row with the lower `annId` is kept. Different performer line-ups on the same song name are not treated as duplicates.

Click **Info** on a result row to see artist aliases, group members, and parent groups.

## Known Database Issues

- Backup vocalists are sometimes stored as full performers, which can affect **Max Other People** (e.g. SMITH with MON, where SMITH is effectively the lead).
- Composer credits, arranger credits, and composer line-ups are only partly built out.

The song list follows AMQ: missing songs, inconsistent artist spellings, and romanization mistakes usually need to be fixed upstream. Report those on the AMQ Discord after reading their pinned change-request guidelines. Artist/group relationship data and occasional extra songs are maintained here separately.

## Contributing

**UI feedback, feature ideas, and database corrections** are all helpful. In particular:

- Groups missing members needed to connect that group to other artists already in the database
- Artists missing alternative names (e.g. Minami Kuribayashi / exige, or Akari Kitou vs Akari Kito)
- Different artists sharing the same display name (e.g. Minami (Kuribayashi) vs Minami (DomexKano))
- Groups whose member roster changes between songs and need separate line-up entries (e.g. JAM Project, Oratorio)
- Songs that exist in AMQ but are missing here

DM **xSardine#8168** on Discord for small database fixes, or open an issue in this repo.

## Thanks

- [Egerod](https://animemusicquiz.com/) and the AMQ mod team for the game and its database
- [MugiBot](https://github.com/CarrC2021/MugiBot) for the database that seeded the first version
