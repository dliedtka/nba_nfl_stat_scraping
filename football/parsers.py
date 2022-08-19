#!/usr/bin/env python3 

from bs4 import BeautifulSoup
from bs4 import Comment


# skip columns for certain tables
# skipping AV for now because it only appears in one table, the first on every page, and it's a stat created by pro football reference
# skipping QBRec for now because don't want to add code to handle one string
# skipping QBR for now because isn't part of the table for anyone who didn't play past 2006
skipped_columns = ["Tm", "Pos", "No.", "AV", "Awards", "QBrec", "QBR"]


def parse_header_row(table, table_type):
    '''
    '''
    for row in table.find_all("tr"):
        prepend = None
        if "class=\"over_header\"" in str(row):
            prepend = {}
            counter = 0
            for col in row.find_all("th"):
                if "colspan" in str(col):
                    span = int(str(col).split("colspan=\"")[1].split("\"")[0])
                else:
                    span = 1
                val = str(col).split(">")[1].split("</")[0]
                if val == "":
                    val = None
                for _ in range(span):
                    prepend[counter] = val 
                    counter += 1
            
        elif ">Year<" in str(row):
            headers = []
            counter = 0
            for col in row.find_all("th"):
                text = str(col).split(">")[1].split("</")[0]
                if text not in skipped_columns:
                    if prepend is not None and prepend[counter] is not None:
                        text = f"{prepend[counter]} {text}"
                    if "data-tip" in str(col):
                        description = str(col).split("data-tip=\"")[1].split("\"")[0]
                    else:
                        description = None
                    headers.append((text, description))
                counter += 1
            return tuple(headers)
    
    return None


def parse_table_column_headers(table_column_headers, player_soup):
    '''
    Get column names and descriptions for table types we haven't seen yet.
    '''
    if "defense_fumbles" not in table_column_headers:
        defense_fumbles_tables = player_soup.find_all("table", class_="stats_table", id="defense")
        if len(defense_fumbles_tables) != 0:
            table_column_headers["defense_fumbles"] = parse_header_row(defense_fumbles_tables[0], "defense_fumbles")
    if "returns" not in table_column_headers:
        returns_tables = player_soup.find_all("table", class_="stats_table", id="returns")
        if len(returns_tables) != 0:
            table_column_headers["returns"] = parse_header_row(returns_tables[0], "returns")
    if "receiving_rushing" not in table_column_headers:
        receiving_rushing_tables = player_soup.find_all("table", class_="stats_table", id="receiving_and_rushing")
        if len(receiving_rushing_tables) != 0:
            table_column_headers["receiving_rushing"] = parse_header_row(receiving_rushing_tables[0], "receiving_rushing")
    if "rushing_receiving" not in table_column_headers:
        rushing_receiving_tables = player_soup.find_all("table", class_="stats_table", id="rushing_and_receiving")
        if len(rushing_receiving_tables) != 0:
            table_column_headers["rushing_receiving"] = parse_header_row(rushing_receiving_tables[0], "rushing_receiving") 
    if "passing" not in table_column_headers:
        passing_tables = player_soup.find_all("table", class_="stats_table", id="passing")
        if len(passing_tables) != 0:
            table_column_headers["passing"] = parse_header_row(passing_tables[0], "passing")  
    if "kicking" not in table_column_headers:
        kicking_tables = player_soup.find_all("table", class_="stats_table", id="kicking")
        if len(kicking_tables) != 0:
            table_column_headers["kicking"] = parse_header_row(kicking_tables[0], "kicking")        
    return table_column_headers


def index_skipped_columns(table):
    '''
    Need to set which indices to skip each time (since AV could be in any but only 1 table)
    '''
    skipped_column_indices = []
    for row in table.find_all("tr"):
        if ">Year<" in str(row):
            counter = 0
            for col in row.find_all("th"):
                text = str(col).split(">")[1].split("</")[0]
                if text in skipped_columns:
                    skipped_column_indices.append(counter)
                counter += 1
            return skipped_column_indices
    return None


def parse_table(table_type, table):
    '''
    '''
    # determine columns to skip
    skipped_column_indices = index_skipped_columns(table)

    stats = []
    rows = table.find_all("tr", class_="full_table")
    for row in rows:
        
        # skip missed seasons (injury, etc.)
        if "missed season" in str(row).lower():
            continue
        # get year
        year_col = str(row.find_all("th")[0]).split("\">")[2].split("</")[0]
        # skip partial seasons (when played on 2+ teams, we just take the whole combined season)
        if year_col == "":
            continue 
        year = int(year_col)
        year_stats = [float(year)]
        
        # get stat
        for counter, col in enumerate(row.find_all("td")):
            # skip team, position, award
            if counter + 1 in skipped_column_indices:
                continue
            # everything else can be parsed to floats
            else:
                stat = str(col).split("\">")[1].split("</")[0].replace("<strong>", "").replace("%", "")
                if stat == "":
                    stat = None
                else:
                    stat = float(stat)
                year_stats.append(stat)
        
        stats.append(tuple(year_stats))

    return stats


def parse_career_stats(player_soup, verbose=False):
    '''
    TODO: account for missed season, skip row
    '''

    stats = {}
    
    # defense & fumbles 
    defense_fumbles_tables = player_soup.find_all("table", class_="stats_table", id="defense")
    if len(defense_fumbles_tables) != 0:
        stats["defense_fumbles"] = parse_table("defense_fumbles", defense_fumbles_tables[0])
    
    # kick/punt return
    returns_tables = player_soup.find_all("table", class_="stats_table", id="returns")
    if len(returns_tables) != 0:
        stats["returns"] = parse_table("returns", returns_tables[0])
    
    # receiving/rushing
    receiving_rushing_tables = player_soup.find_all("table", class_="stats_table", id="receiving_and_rushing")
    if len(receiving_rushing_tables) != 0:
        stats["receiving_rushing"] = parse_table("receiving_rushing", receiving_rushing_tables[0])

    # rushing/receiving
    rushing_receiving_tables = player_soup.find_all("table", class_="stats_table", id="rushing_and_receiving")
    if len(rushing_receiving_tables) != 0:
        stats["rushing_receiving"] = parse_table("rushing_receiving", rushing_receiving_tables[0])

    # passing
    passing_tables = player_soup.find_all("table", class_="stats_table", id="passing")
    if len(passing_tables) != 0:
        stats["passing"] = parse_table("passing", passing_tables[0])

    # kicking/punting
    kicking_tables = player_soup.find_all("table", class_="stats_table", id="kicking")
    if len(kicking_tables) != 0:
        stats["kicking"] = parse_table("kicking", kicking_tables[0])

    # don't think any other table types
    
    if verbose:
        if "defense_fumbles" in stats:
            print ("DEFENSE & FUMBLES")
            for year in stats["defense_fumbles"]:
                print (year)
        if "returns" in stats:
            print ("KICK & PUNT RETURNS")
            for year in stats["returns"]:
                print (year)
        if "receiving_rushing" in stats:
            print ("RECEIVING & RUSHING")
            for year in stats["receiving_rushing"]:
                print (year)
        if "rushing_receiving" in stats:
            print ("RUSHING & RECEIVING")
            for year in stats["rushing_receiving"]:
                print (year)
        if "passing" in stats:
            print ("PASSING")
            for year in stats["passing"]:
                print (year)
        if "kicking" in stats:
            print ("KICKING")
            for year in stats["kicking"]:
                print (year)
    
    return stats


def parse_birth_year(player_soup):
    paragraphs = player_soup.find_all("p")
    for paragraph in paragraphs:
        if "<strong>Born:</strong>" in str(paragraph):
            birth_year = str(paragraph).split("data-birth=\"")[1][:4]
            return int(birth_year)
    return None


def parse_combine(player_soup, verbose=False):
    # these are commented out by default
    comments = player_soup.find_all(string=lambda text: isinstance(text, Comment))
    combine_comment = None
    for comment in comments:
        if "<caption>Combine Measurements Table</caption>" in str(comment):
            combine_comment = comment 
            break 
    if combine_comment is None:
        return None

    combine_table = BeautifulSoup(combine_comment, "html.parser")
    combine_data = combine_table.find_all("tbody")[0]
    combine_year = int(str(combine_data.find_all("th")[0]).split("\">")[2].split("</")[0])
    stats = combine_data.find_all("td")

    # position, height, weight, 40, bench, broad jump, shuttle, cone, vertical
    combine_stats = []
    pos = True
    for val in tuple(map(lambda x: str(x).split("\">")[1].split("</")[0], stats)):
        if pos:
            combine_stats.append(val)
            pos = False 
        else:
            if val == "":
                combine_stats.append(None)
            else:
                combine_stats.append(float(val))

    # figure out combine age
    birth_year = parse_birth_year(player_soup)
    if birth_year is None:
        return None
    combine_stats.insert(1, float(combine_year - birth_year))

    # position, combine age, height, weight, 40, bench, broad jump, shuttle, cone, vertical
    if verbose:
        print ("COMBINE")
        print (tuple(combine_stats))

    return tuple(combine_stats)
    