#!/usr/bin/env python

import random
import csv
import sys
from datetime import *


def load_prices(filename):
    data = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"', skipinitialspace=True)
        for row in reader:
            row['datetime'] = datetime.strptime(row['#DateTime'], '%a %d/%m/%Y %H:%M')
            data.append(row)
    return data

def get_all_days(dat):
    days = set()
    for row in dat:
        days.add( row['datetime'].date() )
    return sorted(days)

def get_random_day(dat, historic_days=100):
    days = get_all_days(dat)
    rand = random.randint(historic_days,len(days)) # always have 'historic_days' previous days
    return days[rand]

def get_data_day(dat, day):
    rows = []
    for row in dat:
        if row['datetime'].date() == day:
            rows.append( row )
    return rows

def get_data_days(dat, day, delta):
    rows = []
    for row in dat:
        mydate = row['datetime'].date()
        if day <= mydate and mydate < day+delta:
            rows.append( row )
    return rows

def get_data_prevdays(dat, day, delta):
    rows = []
    for row in dat:
        mydate = row['datetime'].date()
        if day-delta <= mydate and mydate < day:
            rows.append( row )
    return rows

if __name__ == '__main__':
    datafile = '../data/prices2013.dat';
    dat = load_prices(datafile)

    column_features = [ 'HolidayFlag', 'DayOfWeek', 'PeriodOfDay', 'ForecastWindProduction', 'SystemLoadEA', 'SMPEA', 'CO2Intensity' ]; # within the same day you can use all except: ActualWindProduction, SystemLoadEP2, SMPEP2
          # I ommitted ORKTemperature and ORKWindspeed because it contains 'NaN' missing values (deal with it if you want to use those features)
    column_predict = 'SMPEP2'

    historic_days = 30


    days = get_all_days(dat)
    #print days

    day = get_random_day(dat, historic_days)
    print "Random day:",day

    rows = get_data_day(dat, day)
    features = [ [eval(v) for (k,v) in row.iteritems() if k in column_features] for row in rows]
    prices = [ eval(row[column_predict]) for row in rows ]
    #print "Data of today: ", features
    print "Average real price today:", sum(prices)*1.0/len(prices)

    rows = get_data_prevdays(dat, day, timedelta(historic_days))
    features = [ [eval(v) for (k,v) in row.iteritems() if k in column_features] for row in rows]
    prices = [ eval(row[column_predict]) for row in rows ]
    print "Average real price previous days:", sum(prices)*1.0/len(prices)

    prices = [ eval(row[column_predict]) for row in rows if row['PeriodOfDay'] == '0' ]
    print "Average real price previous days for 0th hour only:", sum(prices)*1.0/len(prices)

