#!/usr/bin/env python

MZNSOLUTIONBASENAME = "minizinc.out"

import sys
sys.path.append('../')
from checker import *

# modified from checker.main()
def print_instance(instance):
    d = instance.day
    actual, forecast = instance.compute_costs()

    if instance.actualsread:
            print "               %12s %12s" % ("Actual", "Forecast")
            print "-" * 40
            print "Task costs:    %12.4f %12.4f" % (d.cj_act, d.cj_fore)
    else:
            print "               %12s" % ("Forecast")
            print "-" * 27
            print "Task costs:    %12.4f" % d.cj_fore

def print_instance_csv(f_inst, f_fore, instance, timing=None, header=True):
    d = instance.day
    actual, forecast = instance.compute_costs()

    d_cj_fore = "%.4f"%d.cj_fore
    d_cj_act = "-"
    if instance.actualsread:
        d_cj_act = "%.4f"%d.cj_act

    msg_timing = ""
    csv_timing = ""
    if timing != None:
        msg_timing = "; time"
        csv_timing = "; %.2f"%timing
    if header:    
        print "f_instance; f_forecast; cost_forecast; cost_actual%s"%msg_timing
    print "%s; %s; %s; %s%s"%(f_inst, f_fore, d_cj_fore, d_cj_act, csv_timing)

def pretty_print(instance):
    for m in instance.day.machines:
        assigned = [t for t in instance.day.tasks if t.machineid == m.machineid]
        msg = "== Machine %i "%m.machineid
        print msg+("="*(instance.day.nrperiods-len(msg)))
        for t in assigned:
            out = "-"*(t.est)
            out += " "*(t.start-t.est)
            out += "X"*(t.duration)
            out += " "*(t.let-(t.start+t.duration))
            out += "-"*(t.nrperiods-t.let)
            out += " :: Task %i"%t.taskid
            print out

def read_mznsolution(instance, f):
        assert instance.instanceread, \
            "Please read in the instance before the solution."
        # Fake Machine events
        for machine in instance.day.machines:
            machine.fake_solution()

        # Load task assignments
        if True:
            cost = None
            tasks = [] # tuples (task, machine, start)
            for line in f:
                if not line.startswith('-------') and not line.startswith('======='):
                    fields = line.strip().split(',')
                    elems = dict()
                    for fie in fields:
                        pos = fie.find('=')
                        elems[fie[:pos]] = fie[pos+1:]
                    if 'Cost' in elems.keys():
                        cost = elems['Cost']
                    if set(['Machine', 'Task', 'Start']) == set(elems.keys()):
                        # make offset 0 (from offset 1)
                        t = int(elems['Task'])-1
                        m = int(elems['Machine'])-1
                        s = int(elems['Start'])-1
                        tasks.append( (t,m,s) )
            tasks_by_id = sorted(tasks)
            #print cost, tasks_by_id
            for (i,task) in enumerate(instance.day.tasks):
                if i >= len(tasks_by_id):
                    print "Error: no task with id '%i' in the solution?"%i
                    sys.exit(1)
                (t,m,s) = tasks_by_id[i]
                task.load_solution(t,m,s)
        instance.solutionread = True


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: python %s instancefolder" % sys.argv[0]
        print >> sys.stderr, "Should contain: instance.txt, mzn-gecode.out (optionally: forecast.txt)"
        sys.exit(1)

    folder = sys.argv[1]

    instance = Instance()
    if True:
        # read standard instance and forecast
        instancefname = join(folder, INSTANCEBASENAME)
        instance.read_instance(instancefname)

        forecastfname = join(folder, FORECASTBASENAME)
        instance.read_forecast(forecastfname)

        # read minizinc solution
        solutionfname = join(folder, MZNSOLUTIONBASENAME)
        with open(solutionfname, "rt") as f:
            read_mznsolution(instance, f)

        instance.verify()
        errstr = instance.geterrorstring()
        if errstr:
            print >> sys.stderr, errstr
        else:
            print_instance(instance)
