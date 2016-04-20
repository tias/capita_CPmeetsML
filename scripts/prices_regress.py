#!/usr/bin/env python

from prices_data import *
import numpy as np
from sklearn import linear_model
from sklearn import svm
from sklearn import preprocessing

import matplotlib.pyplot as plt

def plot_preds(modelpreds, y_test):
    # Print the mean square errors
    print "Residual sum of squares:"
    for (name,preds) in modelpreds:
        print "%s: %.2f"%(name, np.mean((preds-y_test)**2))

    # Explained variance score: 1 is perfect prediction
    #print "Variance scores:"
    #for (name,clf) in clfs:
    #    pred = clf.predict(X_test)
    #    print "%s: %.2f"%(name, clf.score(X_test, y_test))

    # Plot price vs prediction
    plt.scatter(xrange(len(y_test)), y_test,  color='black', label='actual')
    for (name,preds) in modelpreds:
        plt.plot(xrange(len(y_test)), preds, linewidth=3, label=name)
    plt.axis('tight')
    plt.legend(loc='upper left')
    plt.show()


if __name__ == '__main__':
    # load train/test data
    datafile = '../data/prices2013.dat';
    dat = load_prices(datafile)

    column_features = [ 'HolidayFlag', 'DayOfWeek', 'PeriodOfDay', 'ForecastWindProduction', 'SystemLoadEA', 'SMPEA' ]; # within the same day you can use all except: ActualWindProduction, SystemLoadEP2, SMPEP2
          # I ommitted ORKTemperature and ORKWindspeed because it contains 'NaN' missing values (deal with it if you want to use those features), also CO2Intensity sometimes
    column_predict = 'SMPEP2'
    historic_days = 30

    day = get_random_day(dat, historic_days)
    print "Random day:",day

    preds = [] # [(model_name, predictions)]

    # method one: linear
    rows_prev = get_data_prevdays(dat, day, timedelta(historic_days))
    X_train = [ [eval(v) for (k,v) in row.iteritems() if k in column_features] for row in rows_prev]
    y_train = [ eval(row[column_predict]) for row in rows_prev ]
    rows_tod = get_data_days(dat, day, timedelta(7)) # for next week
    X_test = [ [eval(v) for (k,v) in row.iteritems() if k in column_features] for row in rows_tod]
    y_test = [ eval(row[column_predict]) for row in rows_tod ]


    clf = linear_model.LinearRegression()
    clf.fit(X_train, y_train)
    preds.append( ('lin', clf.predict(X_test)) )

    # method two: svm
    # same features but preprocess the data by scaling to 0..1
    scaler = preprocessing.StandardScaler().fit(X_train)
    sX_train = scaler.transform(X_train)
    sX_test = scaler.transform(X_test)
    clf = svm.SVR()
    clf.fit(sX_train, y_train)
    pred = clf.predict(sX_test)
    preds.append( ('svm',pred) )

    plot_preds(preds, y_test)
