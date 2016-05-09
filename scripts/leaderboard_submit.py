#!/usr/bin/env python

import sys
import os
import argparse
import json
import requests


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Submit JSON to leaderboard")
    parser.add_argument("file_json")
    parser.add_argument("--team", help="teamname", default="none")
    parser.add_argument("--pw", help="password", default="none")
    args = parser.parse_args()

    data= {
        'team': 'YOURTEAMNAME',
        'pw': 'YOURPW_ALWAYS_USE_SAME_AFTER_FIRST_USE',
        'json': ''
    }
    if args.team != "none":
        data['team'] = args.team
    if args.pw != "none":
        data['pw'] = args.pw
    with open(args.file_json, 'r') as f_json:
        data['json'] = f_json.read()

    r = requests.post('https://people.cs.kuleuven.be/~tias.guns/capita/submit.php', data=data)
    
    print r.text
