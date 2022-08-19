#!/usr/bin/env python3

import os
import pickle
import requests
from bs4 import BeautifulSoup
import parsers


def scrape(verbose=False, save_frequency=2):
    '''
    Scrape the data from Pro Football Reference.

    @param save_frequency 0 for after processing all players, 1 for after each 
    year, 2 for after each player
    '''
    # try to load dataset
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(f"{cur_dir}/data.pkl"):
        with open(f"{cur_dir}/data.pkl", "rb") as fin:
            data = pickle.load(fin)
    else:
        data = {}
        data["stats"] = {}
        # keep a list of drafted players who didn't participate in the combine 
        # so we don't needlessly re-process them if we restart scraping
        data["untracked_players"] = []

    table_column_headers = {}

    for year in range(2000, 2023):
        if verbose:
            print ("")
            print (year)
            print ("")

        page = requests.get(f"https://www.pro-football-reference.com/years/{year}/draft.htm")
        #print (page.status_code)
        
        draft_soup = BeautifulSoup(page.content, 'html.parser')
        table_body = draft_soup.find_all('div', class_='table_container')[0].find_all("tbody")[0]
        
        # loop over players in draft class
        pick_counter = 0
        for row in table_body.find_all('tr'):
            if "College/Univ" not in str(row):
                pick_counter += 1
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

            # check (name, link) to make sure not already in dataset 
            if (name, link) in data["stats"] or (name, link) in data["untracked_players"]:
                continue
            
            # player page
            page = requests.get(f"https://www.pro-football-reference.com{link}")
            #print (page.status_code)
            player_soup = BeautifulSoup(page.content, 'html.parser')

            # get table header row for different stat tables
            data["table_column_headers"] = parsers.parse_table_column_headers(table_column_headers, player_soup)
            
            # combine measurements
            combine_data = parsers.parse_combine(player_soup, verbose=verbose)

            # season by season stats
            if combine_data is not None:
                career_stats = parsers.parse_career_stats(player_soup, verbose=verbose)
            else:
                career_stats = None

            if career_stats is not None:
                data["stats"][(name, link)] = {}
                data["stats"][(name, link)]["draft_pick"] = pick_counter
                data["stats"][(name, link)]["career_tables"] = career_stats
                data["stats"][(name, link)]["combine"] = combine_data
            else:
                data["untracked_players"].append((name, link))

            if verbose:
                print ("")

            # write dataset
            if save_frequency == 2:
                with open(f"{cur_dir}/data.pkl", "wb") as fout:
                    pickle.dump(data, fout)
        if save_frequency == 1:
            with open(f"{cur_dir}/data.pkl", "wb") as fout:
                pickle.dump(data, fout)
    if save_frequency == 0:
        with open(f"{cur_dir}/data.pkl", "wb") as fout:
            pickle.dump(data, fout)


def convert(verbose=False):
    '''
    Put the data into a format that will be nicer to work with. Combine tables 
    so all stats are in one dictionary; do this for headers too.
    '''
    if verbose:
        print ("Converting data to more easily usable format...")

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    with open(f"{cur_dir}/data.pkl", "rb") as fin:
        data = pickle.load(fin)

    # headers
    if "table_column_headers" in data:
        if "stat_descriptions" not in data:
            data["stat_descriptions"] = {}
            data["stat_descriptions"]["career"] = {}
        for table in data["table_column_headers"]:
            # receiving_rushing/rushing_receiving are same tables but in different orders
            if table != "rushing_receiving":
                prepend = table 
            else:
                prepend = "receiving_rushing"
            
            for stat in data["table_column_headers"][table]:
                data["stat_descriptions"]["career"][f"{prepend}_{stat[0]}"] = stat[1]
            # years experience added stat
            data["stat_descriptions"]["career"][f"{prepend}_years_exp"] = "Number of NFL seasons since player was drafted (including that year, so value is 1 for rookies)"
        # probably should dynamically pull combine stat descriptions, but it's a small enough table that I'll just hard code
        data["stat_descriptions"]["combine"] = []
        # will make a tuple, not dict, since I have combine stats in a tuple not dict
        data["stat_descriptions"]["combine"].append(("Year", None))
        data["stat_descriptions"]["combine"].append(("Pos", "In player and team season stats,<br>Capitals indicates primary starter.<br>Lower-case means part-time starter."))
        data["stat_descriptions"]["combine"].append(("Ht", "Height (ft-inches)"))
        data["stat_descriptions"]["combine"].append(("Wt", "Weight in Pounds"))
        data["stat_descriptions"]["combine"].append(("40yd", "Forty yard dash time"))
        data["stat_descriptions"]["combine"].append(("Bench", "225 lb bench press reps"))
        data["stat_descriptions"]["combine"].append(("Broad Jump", "Broad jump distance, in inches"))
        data["stat_descriptions"]["combine"].append(("Shuttle", "20 yard shuttle time"))
        data["stat_descriptions"]["combine"].append(("3Cone", "Three cone drill time"))
        data["stat_descriptions"]["combine"].append(("Vertical", "Vertical jump height, in inches"))

    # stats
    for player in data["stats"]:
        if "career_tables" in data["stats"][player]:
            data["stats"][player]["career"] = {}
            for table in data["stats"][player]["career_tables"]:
                # receiving_rushing/rushing_receiving are same tables but in different orders
                if table != "rushing_receiving":
                    prepend = table 
                else:
                    prepend = "receiving_rushing"
                
                for idx, stat in enumerate(data["table_column_headers"][table]):
                    data["stats"][player]["career"][f"{prepend}_{stat[0]}"] = []
                    for year in data["stats"][player]["career_tables"][table]:
                        data["stats"][player]["career"][f"{prepend}_{stat[0]}"].append(year[idx])
                    data["stats"][player]["career"][f"{prepend}_{stat[0]}"] = tuple(data["stats"][player]["career"][f"{prepend}_{stat[0]}"])
                    
                # add years_experience column for each table 
                # (need to do each "table" because not guaranteed to have all years for each table)
                data["stats"][player]["career"][f"{prepend}_years_exp"] = tuple([age - data["stats"][player]["combine"][1] + 1. for age in data["stats"][player]["career"][f"{prepend}_Age"]])
                    
            del (data["stats"][player]["career_tables"])

    # delete
    if "table_column_headers" in data:
        del (data["table_column_headers"])

    with open(f"{cur_dir}/data.pkl", "wb") as fout:
        pickle.dump(data, fout)
    if verbose:
        print ("Finished.")


def reduce(verbose=False):
    '''
    Change the data into a more efficient format. Will also want to create a 
    separate script to load the data in memory in the nicer to work with format.
    '''
    pass


if __name__ == "__main__":
    scrape(verbose=True, save_frequency=1)
    convert(verbose=True)
    reduce(verbose=True)
