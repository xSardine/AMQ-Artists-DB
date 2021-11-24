# Process Artist

Scripts that let me reconstruct the database from scratch with the updated exceptions. Temporary until I have a proper UI for admin stuff.

- `map1_artist_id`: Will split artists with regex (ignoring exceptions in `config1_exceptions`) and assign an ID to them
- `map2_group_id`: Will use `config2_groups` to assign members to each group
- `map3_alt_groups`: Will use `config3_alt_groups` to add alternative group configuration (example: Stylips)
- `map4_same_name`: Will use `config4_same_name` to split two artist with the same name but which are actually different
- `map5_member_of`: Will add an attribute to each artists for easier future processing
- `map6_composer`: Will use `config5_composer` to add the composer when it is credited in the artist string (in construction)