#!/usr/bin/env python
# convert icon challenge instance data to dzn data
# ICON data is offset 0, we make everything offset 1

import sys
import os

def get_int(fin):
    return int(fin.readline())

def get_arr(fin, types):
    line = fin.readline().split(' ')
    if len(line) != len(types):
        raise Exception("Split count (%i) does not match input (%i): '%s'"%(len(line), len(types), ",".join(line)))

    return [types[i](line[i]) for i in range(len(line))]

def get_floats(fin, n):
    line = fin.readline().split(' ')
    if len(line) != n:
        raise Exception("Split count (%i) does not match input (%i): '%s'"%(len(line), n, ",".join(line)))

    return [float(x) for x in line]

def get_ints(fin, n):
    line = fin.readline().split(' ')
    if len(line) != n:
        raise Exception("Split count (%i) does not match input (%i): '%s'"%(len(line), n, ",".join(line)))

    return [int(x) for x in line]

def mean(arr):
    return sum(arr)/len(arr)

def read_machines(nr_mach, nr_res, fin):
        ret = []
        for mach in range(0,nr_mach):
            data = dict()
            (data['m'], data['idle'], data['up'], data['down']) = get_arr(fin, [int,float,float,float])
            data['res'] = get_ints(fin, nr_res)

            if mach != data['m']:
                raise Exception("Machine %i does not match '%i'"%(mach, data['m']))
            #print "Machine: ",mach,
            #print data
            ret.append(data)
        return ret

def read_tasks(nr_task, nr_res, fin):
        ret = []
        for task in range(0,nr_task):
            data = dict()
            (data['j'], data['dur'], data['earl'], data['late'], data['power']) = get_arr(fin, [int,int,int,int,float])
            data['usage'] = get_ints(fin, nr_res)
            
            if task != data['j']:
                raise Exception("Task %i does not match '%i'"%(task, data['j']))
            #print "Task: ",task,
            #print data
            ret.append(data)
        return ret

def read_instance(infile):
    data = dict()
    with open(infile, 'r') as fin:
        data['time_step'] = get_int(fin)
        data['nr_res'] = get_int(fin)
        nr_mach = get_int(fin)

        #for (key, value) in data.iteritems():
        #    print "%s: %s"%(key,value)

        #print "Reading %i machines..."%nr_mach
        data['machines'] = read_machines(nr_mach, data['nr_res'], fin)

        nr_task = get_int(fin)
        #print "Reading %i tasks..."%nr_task
        data['tasks'] = read_tasks(nr_task, data['nr_res'], fin)

    return data

def print_data(data):
    for x in ('time_step', 'nr_res'):
        print "%s: %s"%(x, data[x])
    for m in data['machines']:
        print "Machine: ",m['m'],
        print m
    for t in data['tasks']:
        print "Task: ",t['j'],
        print t

def make_offset1(data):
    # Machines
    for mach in data['machines']:
        mach['m'] += 1

    # Tasks
    for task in data['tasks']:
        task['j'] += 1
        task['earl'] += 1
        task['late'] += 1


def get_dzn(data):
    out = ""
    out += "time_step = %(time_step)i;\n"%data
    out += "nbMachines = %i;\n"%len(data['machines'])
    out += "nbTasks = %i;\n"%len(data['tasks'])
    out += "nbRes = %(nr_res)i;\n"%data

    def subarr(arr, key):
        return [str(x[key]) for x in arr]
    def dzn2darr(arr, key):
        data = [x[key] for x in arr]
        ret = "array2d(1..%i, 1..%i, [\n"%(len(data),len(data[0]))

        rows = [",".join(map(str,d)) for d in data]
        ret += "\t"+",\n\t".join(rows)
        ret += "\n])"
        return ret

    # Machines
    #for x in ('up', 'idle', 'down'): # ignored for capita
    #    out += "m_%s = [%s];\n"%(x, ",".join(subarr(data['machines'],x)))
    out += "m_res = %s;\n"%dzn2darr(data['machines'], 'res')

    # Tasks
    for x in ('earl', 'late', 'dur', 'power'):
        out += "j_%s = [%s];\n"%(x, ",".join(subarr(data['tasks'],x)))
    out += "j_res = %s;\n"%dzn2darr(data['tasks'], 'usage')

    return out



if __name__ == '__main__':

    if len(sys.argv) < 1 or '-h' in sys.argv or '--help' in sys.argv:
        print "%s instance.txt [instance.dzn]"%sys.argv[0]
        sys.exit(0)

    infile = sys.argv[1]
    outfile = "%s.dzn"%os.path.splitext(os.path.basename(infile))[0]

    data = read_instance(infile)
    #print_data(data)

    make_offset1(data)

    dzn = get_dzn(data)
    with open(outfile, 'w') as fout:
        fout.write(dzn)
    print "Output written to:", outfile
