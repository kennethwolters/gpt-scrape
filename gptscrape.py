"""
This python script GETs json data from a given URL and will decide on the right
data structure to use to store the data in a sqlite3 database. The decision is
based on prompting the ChatGPT API.
"""

# import sqlite3
# import openai
import sys
import os
import urllib.request
import json

def parse_args():
    """
    required arg: -u <list of urls separated by space>
    optional args:
        -k <OpenAI API key>
    """
    arg_list = sys.argv

    key = None
    urls = []
    for arg in arg_list:
        if arg == "-k":
            key = arg_list[arg_list.index(arg) + 1]
        elif arg == "-u":
            for arg in arg_list[arg_list.index(arg) + 1 :]:
                if arg[0] != "-":
                    urls.append(arg)
                else:
                    break

    if key is None:
        try:
            key = os.environ["OPENAI_API_KEY"]
        except KeyError as exc:
            raise ValueError("No API key provided.") from exc

    if len(urls) == 0:
        raise ValueError("No urls provided")

    return key, urls


def get_json(urls):
    """
    GET json data from list of urls using urllib.request with browser headers.
    """
    data_dict = {}
    for url in urls:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "application/json",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            data_dict[url] = data

    return data_dict

def parse_json(data_dict):
    """
    In this function a lot of stuff happens:
    - find repetitive objects of the same type/structure
      to make each repetitive object an instance of a row instead of
      the whole json object an instance of a row
    - flatten the json structure so it can be an instance of a row
    """
    for url, data in data_dict.items():
        # flatten key structure recursively so that each terminal key
        # is a string of all its parent + itself connected by underscores
        key_list = traverse_json(data, "")
        key_list = list(key_list)
        if len(key_list) > 100: # if deemed large json, expect repetitive structure
            key_dict = rank_by_occurrence(key_list)
            


def traverse_json(data, key):
    """
    Recursively traverse json data and flatten key structure.
    construct list of all terminal keys and their parent keys.
    lists are exposed and marked by a "-list" suffix.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            yield from  traverse_json(v, key + "_" + k)
    elif isinstance(data, list):
        for v in data:
            yield from traverse_json(v, key + "-list")
    else:
        yield key

def rank_by_occurrence(key_list):
    """
    Rank keys by occurrence and sort dict by value from high to low.
    """
    key_dict = {}
    for key in key_list:
        if key in key_dict:
            key_dict[key] += 1
        else:
            key_dict[key] = 1

    key_dict = {k: v for k, v in sorted(key_dict.items(), key=lambda item: item[1], reverse=True)}

    return key_dict

def main():
    api_key, urls = parse_args()
    data_dict = get_json(urls)
    parse_json(data_dict)

if __name__ == "__main__":
    main()
