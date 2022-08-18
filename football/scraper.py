#!/usr/bin/env python3

import os
import pickle
import requests
from bs4 import BeautifulSoup
import parsers


def scrape(verbose=False):
    # try to load dataset
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(f"{cur_dir}/data.pkl"):
        with open(f"{cur_dir}/data.pkl", "rb") as fin:
            data = pickle.load(fin)
    else:
        data = {}
        data["stats"] = {}

    table_column_headers = {}

    for year in range(2000, 2023):
        if verbose:
            print (year)
            print ("")

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
            if (name, link) in data["stats"].keys():
                continue

            # get table header row for different stat tables
            data["table_column_headers"] = parsers.parse_table_column_headers(table_column_headers, player_soup)
            
            # season by season stats
            career_stats = parsers.parse_career_stats(player_soup, verbose=verbose)
            if career_stats is None:
                continue

            # combine measurements
            combine_data = parsers.parse_combine(player_soup, verbose=verbose)
            if combine_data is None:
                continue 

            data["stats"][(name, link)] = {}
            data["stats"][(name, link)]["career_tables"] = career_stats
            data["stats"][(name, link)]["combine"] = combine_data

            if verbose:
                print ("")
            # temporarily limit to one player
            #exit()

            # write dataset
            with open(f"{cur_dir}/data.pkl", "wb") as fout:
                pickle.dump(data, fout)

        # temporarily limit to one year
        #exit()


def convert():
    '''
    Combine tables so all stats are in one dictionary; do this for headers too.
    '''
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    with open(f"{cur_dir}/data.pkl", "rb") as fin:
        data = pickle.load(fin)

    # headers

    # stats
    for player in data["stats"].keys():
        data["stats"][player]["career"]
        for table in data["stats"][player]["career_tables"].keys():
            # receiving_rushing/rushing_receiving are same tables but in different orders
            if table != "rushing_receiving":
                prepend = table 
            else:
                prepend = "receiving_rushing"

    # delete

    #with open(f"{cur_dir}/data.pkl", "wb") as fout:
    #    pickle.dump(data, fout)


if __name__ == "__main__":
    #scrape(verbose=True)
    convert()
