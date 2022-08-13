#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import parsers

for year in range(2000, 2023):
    #print (year)

    page = requests.get(f"https://www.pro-football-reference.com/years/{year}/draft.htm")
    #print (page.status_code)
    
    draft_soup = BeautifulSoup(page.content, 'html.parser')
    
    table_body = draft_soup.find_all('div', class_='table_container')[0].find_all("tbody")[0]
    
    counter = 0
    for row in table_body.find_all('tr'):
        if "class=\"thead\"" in str(row):
            continue 

        player = row.find_all("td")[2]
        if "href=" not in str(player):
            continue
        else:
            player = str(player.find_all("a")[0])

        # extract link, name
        link, name = player.split("\">")
        link = link[9:]
        name = name[:-4]
        print (name, link)

        # temporarily limit to one player
        page = requests.get(f"https://www.pro-football-reference.com{link}")
        #print (page.status_code)

        player_soup = BeautifulSoup(page.content, 'html.parser')

        # season by season stats
        career_stats = parsers.parse_career_stats(player_soup)
        if career_stats is None:
            continue

        # combine measurements
        combine_data = parsers.parse_combine(player_soup)
        if combine_data is None:
            continue 
        # position, combine age, height, weight, 40, bench, broad jump, shuttle, cone, vertical
        print (combine_data)

        # temporarily limit to one player
        #exit()

    # temporarily limit to one year
    exit()
