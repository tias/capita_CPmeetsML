#!/usr/bin/env python
# convert icon challenge instance data to dzn data

import sys
import os

def get_int(fin):
    return int(fin.readline())

def get_arr(fin, types):
    line = fin.readline().split(' ')
    if len(line) != len(types):
        raise Exception("Split count (%i) does not match input (%i): '%s'"%(len(line), len(types), ",".join(line)))

    return [types[i](line[i]) for i in range(len(line))]


def read_forecast(infile):
    data = []
    with open(infile, 'r') as fin:
        n = get_int(fin)
        for i in range(0,n):
            (ii, v) = get_arr(fin, [int,float])
            data.append(v)
    return data

def get_forecast_dzn(data):
    out = "price = [%s];\n"%(",".join(map(str,data)))

    return out


def rescale(time_step, data):
    data_step = (24*60)/len(data) 
    if data_step > time_step:
        print "Forecast: time_step smaller, repeating data"
        print "Forecast: TODO"
        return data
    if data_step < time_step:
        factor = time_step / data_step
        #print "Forecast: time_step bigger than data, aggregating with factor %i"%factor
        newdata = []
        for t in xrange( (24*60)/time_step ):
            offset = t*factor
            newdata.append( sum(data[offset:offset+factor]) )
        return newdata
    return data


if __name__ == '__main__':

    if len(sys.argv) < 1 or '-h' in sys.argv or '--help' in sys.argv:
        print "%s [-t time_step] forecast.txt [forecast.dzn]"%sys.argv[0]
        sys.exit(0)

    time_step = 5

    # read args, quick hack
    apos = 1 # pos in sys.argv
    args = sys.argv[1:]
    if sys.argv[apos] == '-t':
        apos += 1
        time_step = int(sys.argv[apos])
        apos += 1
    infile = sys.argv[apos]

    outfile = "%s.dzn"%os.path.splitext(os.path.basename(infile))[0]

    data = read_forecast(infile)
    print "Read %i forecasts"%len(data)

    data = rescale(time_step, data)
    dzn = get_forecast_dzn(data)
    with open(outfile, 'w') as fout:
        fout.write(dzn)
    print "Output written to:", outfile
