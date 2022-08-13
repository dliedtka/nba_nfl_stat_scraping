#!/usr/bin/env python3 

from bs4 import BeautifulSoup
from bs4 import Comment


def parse_career_stats(player_soup):
    stats_table = player_soup.find_all('div', class_='table_container')[0]
    print (stats_table)
    exit()
    # need to parse, probably want to grab colnames from top row since they'll depend on position
    return None


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
    combine_stats.insert(1, combine_year - birth_year)

    return tuple(combine_stats)
    