# Scraping Pro Football Reference

Collects career statistics, combine statistics, and draft position for drafted players that participated in the NFL combine beginning with the 2000 NFL Draft. 

Collects the "Defense & Fumbles", "Returns", "Receiving & Rushing" (or "Rushing & Receiving"), "Passing", and "Kicking" tables in addition to the "Combine Results" table. 

Does not collect statistics for undrafted players (whether they participated in the combine or not) or drafted players that did not participate in the combine (my original goal in doing this was to project career performance based on combine results). 


## Data Structure

Data after running scraper.py is stored in a dictionary that includes the following keys:
- career_stat_names: A list of 5 tuples (one for each table type: "Defense & Fumbles", etc.) with each tuple containing the names and order of stats collected for that table (can be used to interpret a player's career stats tuples)
- career_stat_descriptions: The PFR descriptions of stats collected, uses same structure as career_stat_names
- combine_stat_names: Mirrors career_stat_names but for combine stats (and only 1 table, so no 5 tuples)
- combine_stat_descriptions: Mirrors career_stat_descriptions
- tracked_players: A list of tuples (player name, PFR link) that can be used to index the career_stats, combine_stats, and draft_pick lists
- career_stats: A list of a tuple for each player containing 5 tuples for the different table types with career statistics (a tuple for each year in the table)
- combine_stats: A list of tuples with each tuple a player's set of combine results
- draft_pick: A list of what overall pick in the draft each player was
- untracked_players: A list of players who were drafted but did not participate in the combine, so we don't have stats for them


## Notes

- "Receiving & Rushing" and "Rushing & Receiving" are the same tables, just with stats in different orders depending on if the player was primarily running or catching. I just reorder "Rushing & Receiving" and combine with "Receiving & Rushing".
- Certain columns in the tables are not collected:
    - Tm: Team was not relevant to my prediction task
    - Pos: I used the Position associated with their combine results table and disregarded their position in the career stats tables
    - No.: Uniform Number was not relevant to my prediction task
    - AV: This is a PFR-generated stat that would appear in the player's "primary" table, which was making collecting stats and associating them with the right header more complicated
    - Awards: I didn't feel like handling possibly multiple strings 
    - QBrec: QB Record may be interesting to use eventually, but I didn't feel like making a few exceptions to handle non-numeric data.
    - QBR: ESPN's QB rating has only been collected since 2006 and was part of the table only for primary position QBs (not an RB who through some passes, for example); could have handled it but again did not want to implement an exception for it
- Also note that in the "Defense & Fumbles" table, QBHits is collected only starting in 2006.