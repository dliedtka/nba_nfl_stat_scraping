#!/usr/bin/env python3 

from bs4 import BeautifulSoup
from bs4 import Comment


# skip columns for certain tables
skipped_columns = {
    "defense" : [2, 3, 4, 25], # skip tm, pos, no., awards
}


def parse_header_row(table, table_type):
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
                if counter not in skipped_columns[table_type]:
                    text = str(col).split(">")[1].split("</")[0]
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


def parse_table_columns(table_columns, player_soup):
    '''
    Get column names and descriptions for table types we haven't seen yet.
    '''
    if "defense" not in table_columns:
        defense_tables = player_soup.find_all("table", class_="stats_table", id="defense")
        if defense_tables is not None:
            table_columns["defense"] = parse_header_row(defense_tables[0], "defense")
    return table_columns


def init_dict(my_dict):
    if my_dict is None:
        return {}
    else:
        return my_dict


def parse_defense(table):
    '''
    Note: QBHits recorded since 2006
    Will need to handle 2 team years, just grab total and skip if no year
    Could make a mapping of counter to stat name to make more readable
    '''
    stats = []
    rows = table.find_all("tr", class_="full_table")
    for row in rows:
        # get year
        year_col = str(row.find_all("th")[0]).split("\">")[2].split("</")[0]
        if year_col == "":
            continue 
        year = int(year_col)
        year_stats = [float(year)]
        # skip team, position, award; everything else can be floats
        for counter, col in enumerate(row.find_all("td")):
            if counter + 1 in skipped_columns["defense"]:
                continue
            else:
                stat = str(col).split("\">")[1].split("</")[0].replace("<strong>", "")
                if stat == "":
                    if counter + 1 == 22 and year < 2006:
                        stat = None 
                    else:
                        stat = float(0)
                else:
                    stat = float(stat)
                year_stats.append(stat)
        stats.append(tuple(year_stats))
    return stats


def parse_career_stats(player_soup):
    '''
    TODO: account for missed season, skip row
    '''
    stats = None
    
    # defense & fumbles 
    defense_tables = player_soup.find_all("table", class_="stats_table", id="defense")
    if defense_tables is not None:
        stats = init_dict(stats)
        stats["defense"] = parse_defense(defense_tables[0])
    
    # passing
    # rushing/receiving
    # kick/punt return
    # kicking/punting
    
    # don't think any others
    
    for year in stats["defense"]:
        print (year)
    exit()
    return stats


def parse_birth_year(player_soup):
    paragraphs = player_soup.find_all("p")
    for paragraph in paragraphs:
        if "<strong>Born:</strong>" in str(paragraph):
            birth_year = str(paragraph).split("data-birth=\"")[1][:4]
            return int(birth_year)
    return None


def parse_combine(player_soup):
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

    return tuple(combine_stats)
    