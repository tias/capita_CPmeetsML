#!/usr/bin/env python

MZNSOLUTIONBASENAME = "minizinc.out"

import sys
import os
import shutil
import argparse
import time as ttime
import glob
import json

cwd=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(cwd,'scripts'))
from prices_data import *
from checker import *


def instance2arr(instance):
    tasks = [] 
    for t in instance.day.tasks:
        tasks.append( {'est':t.est, 'let':t.let, 'dur':t.duration, 'pow':t.power} )
#            costs[i] = sum([t.power*day.actuals[j]*t.q/60.0 for j in range(i, i+t.duration)])
    return tasks
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run and check a MZN model in ICON challenge data")
    parser.add_argument("--out", help="file to write the JSON output to", default="server.json")
    # debugging options:
    parser.add_argument("-v", help="verbosity (0,1,2 or 3)", type=int, default=0)
    args = parser.parse_args()

    dir_load = '../'
    datafile = '../data/prices2013.dat';
    dat = load_prices(datafile)
    

    # benchmark setting, you can choose one of load1/load8 instead of both too (but always all start days)
    benchmarks = {'load1': ['2013-02-01', '2013-05-01', '2013-08-01', '2013-11-01'],
                  'load8': ['2013-02-01', '2013-05-01', '2013-08-01', '2013-11-01'],
                 }

    column_predict = 'SMPEP2'

    # {'load1': {'2013-12-01': {'day01.txt': [{'taskid': 1, 'machid': 1, 'start': 1},
    #                                         {'taskid': ... }],
    #                           'day02.txt': [...],
    #                           ...
    #                          },
    #            '2013-05-01': {'day01.txt'...}
    #           },
    #  'load8': ...
    # }
    res = dict()
    for load, startdays in benchmarks.iteritems():
        res[load] = dict()
        globpatt = os.path.join(dir_load, load, 'day*.txt')
        f_instances = sorted(glob.glob(globpatt))

        for day_str in startdays:
            res[load][day_str] = dict()
            day = datetime.strptime(day_str, '%Y-%m-%d').date()

            # get schedule instances

            for (i,f) in enumerate(f_instances):
                today = day + timedelta(i)
                rows_tod = get_data_day(dat, today)
                data_actual = [ eval(row[column_predict]) for row in rows_tod ]

                instance = Instance()
                # read standard instance and load actuals
                instance.read_instance(f)

                f_name = os.path.basename(f)
                res[load][day_str][f_name] = dict({'q': instance.day.q, 'act': data_actual, 'tasks': instance2arr(instance)})

    with open(args.out, 'w') as f_out:
        json.dump(res, f_out)
