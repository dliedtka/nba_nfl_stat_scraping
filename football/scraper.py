#!/usr/bin/env python3

import os
import pickle
import requests
from bs4 import BeautifulSoup
import parsers


def create_dataset():
    '''
    '''
    data = {}
    data["career_stat_names"] = []
    data["career_stat_descriptions"] = []
    data["combine_stat_names"] = []
    data["combine_stat_descriptions"] = []
    data["tracked_players"] = []
    data["career_stats"] = []
    data["combine_stats"] = []
    data["draft_pick"] = []
    # keep a list of drafted players who didn't participate in the combine 
    # so we don't needlessly re-process them if we restart scraping
    data["untracked_players"] = []
    return data


def career_stat_names_descriptions(data, verbose=False):
    '''
    Get career stat names and descriptions dynamically.
    '''
    if verbose:
        print ("Collecting career stat names and descriptions...")
    table_column_headers = {}
    
    page = requests.get(f"https://www.pro-football-reference.com/years/2000/draft.htm")
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
        player = str(player.find_all("a")[0])

        # extract link
        link = player.split("\">")[0][9:]
        
        # player page
        page = requests.get(f"https://www.pro-football-reference.com{link}")
        #print (page.status_code)
        player_soup = BeautifulSoup(page.content, 'html.parser')

        # extract stat names and descriptions
        table_column_headers = parsers.parse_table_column_headers(table_column_headers, player_soup)

        if ("defense_fumbles" in table_column_headers and
            "returns" in table_column_headers and
            "receiving_rushing" in table_column_headers and
            "passing" in table_column_headers and
            "kicking" in table_column_headers):
            break

    # convert to our desired format
    names = []
    descriptions = []
    for table in table_column_headers:
        table_names = []
        table_descriptions = []
        for stat in table_column_headers[table]:
            table_names.append(f"{table}_{stat[0]}")
            table_descriptions.append(stat[1])
        names.append(tuple(table_names))
        descriptions.append(tuple(table_descriptions))
    data["career_stat_names"] = tuple(names)
    data["career_stat_descriptions"] = tuple(descriptions)

    if verbose:
        print ("Finished.")

    return data


def combine_stat_names_descriptions(data, verbose):
    '''
    '''
    data["combine_stat_names"].append("Pos")
    data["combine_stat_names"].append("combine_age")
    data["combine_stat_names"].append("Ht")
    data["combine_stat_names"].append("Wt")
    data["combine_stat_names"].append("40yd")
    data["combine_stat_names"].append("Bench")
    data["combine_stat_names"].append("Broad Jump")
    data["combine_stat_names"].append("Shuttle")
    data["combine_stat_names"].append("3Cone")
    data["combine_stat_names"].append("Vertical")  
    data["combine_stat_descriptions"].append("Age by the end of the year of the combine (in almost all cases should be their age during their rookie season.")  
    data["combine_stat_descriptions"].append("In player and team season stats,<br>Capitals indicates primary starter.<br>Lower-case means part-time starter.")
    data["combine_stat_descriptions"].append("Height (ft-inches)")
    data["combine_stat_descriptions"].append("Weight in Pounds")
    data["combine_stat_descriptions"].append("Forty yard dash time")
    data["combine_stat_descriptions"].append("225 lb bench press reps")
    data["combine_stat_descriptions"].append("Broad jump distance, in inches")
    data["combine_stat_descriptions"].append("20 yard shuttle time")
    data["combine_stat_descriptions"].append("Three cone drill time")
    data["combine_stat_descriptions"].append("Vertical jump height, in inches")
    return data


def scrape(verbose=False, save_frequency=2):
    '''
    Scrape the data from Pro Football Reference.

    @param save_frequency 0 for after processing all players, 1 for after each 
    year, 2 for after each player
    '''
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    
    # try to load dataset
    if os.path.exists(f"{cur_dir}/data.pkl"):
        with open(f"{cur_dir}/data.pkl", "rb") as fin:
            data = pickle.load(fin)
    # create dataset
    else:
        data = create_dataset()
        
    if len(data["career_stat_names"]) == 0:
        # get career stat names and descriptions dynamically
        data = career_stat_names_descriptions(data, verbose)
        with open(f"{cur_dir}/data.pkl", "wb") as fout:
            pickle.dump(data, fout)
    
    if len(data["combine_stat_names"]) == 0:
        # now fill out combine stat names/descriptions
        data = combine_stat_names_descriptions(data, verbose)
        with open(f"{cur_dir}/data.pkl", "wb") as fout:
            pickle.dump(data, fout)


    # now collect career and combine stats for players
    for year in range(2000, 2023):
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
                print (name, link, year, f"Pick {pick_counter}")

            # check (name, link) to make sure not already in dataset 
            if (name, link) in data["tracked_players"] or (name, link) in data["untracked_players"]:
                continue
            
            # player page
            page = requests.get(f"https://www.pro-football-reference.com{link}")
            #print (page.status_code)
            player_soup = BeautifulSoup(page.content, 'html.parser')

            # combine measurements
            combine_stats = parsers.parse_combine(player_soup, verbose=verbose)

            # season by season stats
            if combine_stats is not None:
                career_stats = parsers.parse_career_stats(player_soup, verbose=verbose)
            else:
                career_stats = None

            if career_stats is not None:
                data["tracked_players"].append((name, link))
                data["draft_pick"].append(pick_counter)
                data["combine_stats"].append(combine_stats)
                data["career_stats"].append(career_stats)
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


if __name__ == "__main__":
    scrape(verbose=True, save_frequency=1)
    # will want to create another python script to load data and dynamically transform to more usable format
    # create stats like years experience
    # (currently in backup)

    # if it isn't more efficient, could have a dictionary and store by stat
