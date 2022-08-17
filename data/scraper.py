#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import parsers


def scrape(verbose=False):
    # TODO: try to load dataset

    table_column_headers = {}

    for year in range(2000, 2023):
        #print (year)

        page = requests.get(f"https://www.pro-football-reference.com/years/{year}/draft.htm")
        #print (page.status_code)
        
        draft_soup = BeautifulSoup(page.content, 'html.parser')
        table_body = draft_soup.find_all('div', class_='table_container')[0].find_all("tbody")[0]
        
        # loop over players in draft class
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
            if verbose:
                print (name, link)

            # player page
            page = requests.get(f"https://www.pro-football-reference.com{link}")
            #print (page.status_code)
            player_soup = BeautifulSoup(page.content, 'html.parser')

            # TODO: check player, link (2 Adrian Petersons) to make sure not already in dataset 

            # get table header row for different stat tables
            table_column_headers = parsers.parse_table_column_headers(table_column_headers, player_soup)
            
            # season by season stats
            career_stats = parsers.parse_career_stats(player_soup, verbose=verbose)
            if career_stats is None:
                continue

            # combine measurements
            combine_data = parsers.parse_combine(player_soup, verbose=verbose)
            if combine_data is None:
                continue 

            if verbose:
                print ("")
            # temporarily limit to one player
            #exit()

            # TODO: write dataset

        # temporarily limit to one year
        exit()


if __name__ == "__main__":
    scrape(verbose=True)
