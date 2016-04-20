#!/usr/bin/env python


"""
    Checker for Energy-Cost Aware Scheduling/Forecasting Competition.
    H. Simonis, B. O'Sullivan, D. Mehta, B. Hurley, M. De Cauwer

    Will verify that the solution follows the specification and does not violate
    any constraints of the model. Note that the case of invalid input formats,
    the list of errors may build upon each other. For a valid input, the
    objective value using both the forecast and actual electricity price data
    (if available) will be printed.

        Usage: python checker.py ./pathtoinstancefolder

    The instance folder should contain at least three files:
        * instance.txt [provided]
        * forecast.txt [provided]
        * solution.txt should contain the solution produced by your solver.

    Version: 1.1
"""


import sys
from os.path import join, isfile
from copy import deepcopy
import logging
import cStringIO


datafolder = "data"
INSTANCEBASENAME = "instance.txt"
ACTUALSBASENAME = "actual.txt"
FORECASTBASENAME = "forecast.txt"
SOLUTIONBASENAME = "solution.txt"
MINUTESINDAY = 24 * 60


class Instance(object):

    def __init__(self):
        self.instanceread = False
        self.actualsread = False
        self.forecastread = False
        self.solutionread = False
        self.machines = []
        self.day = self.q = self.nrresources = None

        # Set up error logging to string buffer 'self.errstream'
        self.log = logging.getLogger()
        self.log.setLevel(logging.ERROR)
        for handler in self.log.handlers:  # Remove other handlers
            self.log.removeHandler(handler)
        self.errstream = cStringIO.StringIO()
        handler = logging.StreamHandler(self.errstream)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.log.addHandler(handler)

    def read_instancefolder(self, folder,
                            actual=True,
                            forecast=True,
                            solution=True):
        instancefname = join(folder, INSTANCEBASENAME)
        actualsfname = join(folder, ACTUALSBASENAME)
        forecastfname = join(folder, FORECASTBASENAME)
        solutionfname = join(folder, SOLUTIONBASENAME)

        self.read_instance(instancefname)
        if actual and isfile(actualsfname):
            self.read_actual(actualsfname)
        if forecast:
            self.read_forecast(forecastfname)
        if solution:
            self.read_solution(solutionfname)

    def read_instance(self, filename):
        with open(filename, "rt") as f:
            self.q = int(f.readline())  # Time resolution
            self.nrresources = int(f.readline())

            nrmachines = int(f.readline())
            for m in xrange(nrmachines):
                machine = Machine(self.q, self.nrresources)
                machine.read_instance(f)
                self.machines.append(machine)

            self.day = Day(self.machines, self.q, self.nrresources)
            self.day.read_instance(f)
        self.instanceread = True

    def read_actual(self, filename):
        with open(filename, "rt") as f:
            nrperiods = int(f.readline())
            errlog(MINUTESINDAY / self.q == nrperiods,
                   "Actuals file contains a different number of "
                   "time periods, expected %d, got %d." %
                   (MINUTESINDAY / self.q, nrperiods))

            self.day.read_actual(f, nrperiods)
        self.actualsread = True

    def load_actual(self, arr):
        nrperiods = len(arr)
        errlog(MINUTESINDAY / self.q == nrperiods,
                   "Actuals contain a different number of "
                   "time periods, expected %d, got %d." %
                   (MINUTESINDAY / self.q, nrperiods))

        self.day.actuals = arr
        self.actualsread = True

    def load_forecast(self, arr):
        nrperiods = len(arr)
        errlog(MINUTESINDAY / self.q == nrperiods,
                   "Forecasts contain a different number of "
                   "time periods, expected %d, got %d." %
                   (MINUTESINDAY / self.q, nrperiods))

        self.day.forecast = arr
        self.forecastread = True

    def read_forecast(self, filename):
        with open(filename, "rt") as f:
            nrperiods = int(f.readline())
            errlog(MINUTESINDAY / self.q == nrperiods,
                   "Forecast file contains a different number of "
                   "time periods, expected %d, got %d." %
                   (MINUTESINDAY / self.q, nrperiods))

            self.day.read_forecast(f, nrperiods)
        self.forecastread = True

    def read_solution(self, filename):
        assert self.instanceread, \
            "Please read in the instance before the solution."
        with open(filename, "rt") as f:
            self.day.read_solution(f)
        self.solutionread = True

    def verify(self):
        assert self.instanceread, \
            "Please read in the instance before verifying."
        # assert self.actualsread, \
        #     "Please read in the actual prices before verifying."
        assert self.forecastread, \
            "Please read in the forecast prices before verifying."
        assert self.solutionread, \
            "Please read in the solution before verifying."

        self.day.verify()
        return bool(self.geterrorstring())

    def compute_costs(self):
        actual, forecast = self.day.compute_costs()
        return actual, forecast

    def geterrorstring(self):
        return self.errstream.getvalue()

    def __str__(self):
        return "<Instance q:%d nrresources:%d>" % \
            (self.q, self.nrresources)


class Day(object):

    def __init__(self, machines, q, nrresources):
        # Take a deepcopy of the machines so we can parse their on/off data.
        self.machines = deepcopy(machines)
        self.q = q
        self.nrperiods = MINUTESINDAY / q
        self.nrresources = nrresources
        self.tasks = []
        self.actuals = []
        self.forecast = []

    def read_instance(self, f):
        nrtasks = int(f.readline())
        for j in xrange(nrtasks):
            task = Task(self.q, self.nrresources)
            task.read_instance(f)
            self.tasks.append(task)

    def read_actual(self, f, nrperiods):
        self.actuals = []
        for i in xrange(nrperiods):
            bits = f.readline().split(" ")
            intervalid = int(bits[0])
            errlog(len(self.actuals) == intervalid,
                   "Actuals price data appears to be specified out of order."
                   "found interval %d, expected %d." %
                   (intervalid, len(self.actuals)))
            price = float(bits[1])  # euro/kWh
            self.actuals.append(price)

    def read_forecast(self, f, nrperiods):
        self.forecast = []
        for i in xrange(nrperiods):
            bits = f.readline().split(" ")
            intervalid = int(bits[0])
            errlog(len(self.forecast) == intervalid,
                   "Forecase price data appears to be specified out of order."
                   "found interval %d, expected %d." %
                   (intervalid, len(self.forecast)))
            price = float(bits[1])  # euro/kWh
            self.forecast.append(price)

    def read_solution(self, f):
        # Read Machine events
        nrmachines = int(f.readline())
        errlog(nrmachines == len(self.machines),
               "Instance contains a different number of machines."
               "Expected %d got %d." % (len(self.machines), nrmachines))
        for machine in self.machines:
            machine.read_solution(f)

        # Read task assignments
        bits = f.readline().split(" ")
        errlog(len(bits) == 1,
               "Invalid solution format, expected a single integer for "
               "the number of tasks, but got %r" % repr(" ".join(bits)))
        nrtasks = int(bits[0])
        errlog(nrtasks == len(self.tasks),
               "Instance contains a different number of tasks."
               "Expected %d got %d." % (len(self.tasks), nrtasks))
        for task in self.tasks:
            task.read_solution(f)

    def verify(self):
        for task in self.tasks:
            task.verify()

        # Find tasks running on each machine and compute usage
        for m in self.machines:
            assigned = [t for t in self.tasks if t.machineid == m.machineid]
            m.compute_usage(assigned)

        for machine in self.machines:
            machine.verify()

    def compute_costs(self):
        cj_act = cj_fore = cm_act = cm_fore = cup = cdown = 0.0

        for machine in self.machines:
            upcost, downcost, idleactual, idlefore, poweractual, powerfore = \
                machine.compute_costs(self.actuals, self.forecast)

            cup += upcost
            cdown += downcost
            cj_act += poweractual
            cj_fore += powerfore
            cm_act += idleactual
            cm_fore += idlefore

        actual = cj_act + cm_act + cup + cdown
        forecast = cj_fore + cm_fore + cup + cdown

        self.cj_act = cj_act
        self.cj_fore = cj_fore
        self.cm_act = cm_act
        self.cm_fore = cm_fore
        self.cup = cup
        self.cdown = cdown
        return actual, forecast

    def __str__(self):
        return "<Day tasks:%d machines:%d>" % \
            (len(self.tasks), len(self.machines))


class Task(object):

    def __init__(self, q, nrresources):
        self.q = q
        self.nrperiods = MINUTESINDAY / q
        self.nrresources = nrresources
        self.machineid = self.start = None

    def read_instance(self, f):
        bits1 = f.readline().strip().split(" ")
        self.taskid, self.duration, self.est, self.let = map(int, bits1[:4])
        self.power = float(bits1[4])
        self.resourceuse = map(int, f.readline().strip().split(" "))

        assert self.duration > 0, "Internal: invalid durtaion"
        assert self.est >= 0, "Internal: invalid est"
        assert self.let <= self.nrperiods, "Internal: invalid let"
        assert self.est + self.duration <= self.let, "Internal: est+d<let"
        assert len(self.resourceuse) == self.nrresources, "Internal: nrres"

    def read_solution(self, f):
        bits = f.readline().split(" ")
        errlog(len(bits) == 3,
               "Invalid solution format for task %d, expected 3 integers "
               "but got %r" % (self.taskid, repr(" ".join(bits))))
        taskid, self.machineid, self.start = map(int, bits)

        errlog(taskid == self.taskid,
               "TaskID mismatch, are the tasks specified out of order?"
               "Expected %d, got %d." % (self.taskid, taskid))

    # data = dict({'Machine': int, 'Task': int, Time: int})
    def load_solution(self, taskid, machid, start):
        taskid = int(taskid)
        self.machineid = int(machid)
        self.start = int(start)

        errlog(taskid == self.taskid,
               "TaskID mismatch, is there a task missing or specified out of order?"
               "Expected %d, got %d." % (self.taskid, taskid))

    def verify(self):
        # Checks that a task has a valid start/end times
        # Does not check resource use, that is done by the machine.

        # Constraint 2
        errlog(self.start >= self.est,
               "Task %d starting at %d is before its earliest start time %d." %
               (self.taskid, self.start, self.est))

        # Constraint 3
        ends = self.start + self.duration
        errlog(ends <= self.let,
               "Task %d ending at %d is after its latest end time %d." %
               (self.taskid, ends, self.let))

    def __str__(self):
        assignstr = ""
        if self.machineid and self.start:
            assignstr = " machine:%d start:%d" % (self.machineid, self.start)
        return "<Task %d dur:%d est:%d let:%d%s>" % \
            (self.taskid, self.duration, self.est, self.let, assignstr)


class Machine(object):

    def __init__(self, q, nrresources):
        self.q = q
        self.nrperiods = MINUTESINDAY / q
        self.nrresources = nrresources
        self.status = None
        self.events = None
        self.idlecost = self.upcost = self.downcost = None

    def read_instance(self, f):
        bits1 = f.readline().strip().split(" ")
        self.machineid = int(bits1[0])
        self.idle, self.up, self.down = map(float, bits1[1:])
        self.resoursecap = map(int, f.readline().strip().split(" "))

    def read_solution(self, f):
        bits = f.readline().split(" ")
        errlog(len(bits) == 1,
               "Invalid solution format for machine, expected a single integer"
               "for machine ID but got %r" % repr(" ".join(bits)))
        machineid = int(bits[0])
        errlog(machineid == self.machineid,
               "MachineID mismatch, are the machines specified out of order?"
               "Expected %d, got %d." % (self.machineid, machineid))

        bits = f.readline().split(" ")
        errlog(len(bits) == 1,
               "Invalid solution format for machine %d, expected a single "
               "integer for number of events, but got %r" %
               (self.machineid, repr(" ".join(bits))))
        nrevents = int(bits[0])
        events = []
        for i in xrange(nrevents):
            bits = map(int, f.readline().strip().split(" "))
            errlog(len(bits) == 2,
                   "Machine event lines should only contina two values, "
                   "1/0 for on/off and the timepoint. Found %d instead of 2" %
                   len(bits))
            action, time = bits
            events.append((action, time))

        # Sort events by start time, where tied startup actions happen first.
        self.events = sorted(events, key=lambda (a, t): t + float(1 - a) / 2)

    def fake_solution(self):
        # always on (first on, last off)
        self.events = [(1,0), (0,self.nrperiods-1)] # [on, off]

    def compute_usage(self, assigned):
        # Compute the up/down status of the machine over the time horizon
        # Off initially at all time points. +1 for verifying its off at end
        self.status = [0] * (self.nrperiods + 1)
        for i, (action, time) in enumerate(self.events):
            endtime = self.nrperiods
            if i + 1 < len(self.events):
                endtime = self.events[i + 1][1] + 1

            if action == 0:
                time += 1  # Shutdown takes place at the end of time period

            # Set the status of the machine between these time points
            self.status[time:endtime] = [action] * (endtime - time)

        # Compute cumulative resouce use
        self.usage = [[0] * self.nrresources for i in xrange(self.nrperiods)]
        self.power = [0] * self.nrperiods
        for task in assigned:
            errlog(task.start + task.duration <= self.nrperiods,
                   "Invalid start time %d with duration %d for task %d "
                   "on machine %d." % (task.start, task.duration, task.taskid,
                                       task.machineid))

            for t in xrange(task.start, task.start + task.duration):
                for r, use in enumerate(task.resourceuse):
                    self.usage[t][r] += use
                self.power[t] += task.power

    def verify(self):
        # Verify that machines are in the correct state for specified events
        for i, (action, time) in enumerate(self.events):
            if action == 0:
                # Constraint 7
                errlog(self.status[time] == 1,
                       "Machine %d is not running at time %d but action 0" %
                       (self.machineid, time))
                time += 1  # Shutdown takes place at the end of time period

            elif action == 1 and time > 0:
                # Constraint 6
                errlog(self.status[time - 1] == 0,
                       "Machine %d is running at time %d-1 but action 1" %
                       (self.machineid, time))

        errlog(not self.status[-1],
               "Machine %d must be off at the end of the time period." %
               (self.machineid))

        for t, resourceuse in enumerate(self.usage):
            for r, use in enumerate(resourceuse):
                # Constraint 4
                errlog(use <= self.resoursecap[r],
                       "Machine %d t:%d resource %d capacity %d exceeded %d." %
                       (self.machineid, t, r, self.resoursecap[r], use))

            # Constraint 9
            if sum(resourceuse) > 0:  # Is there activity?
                errlog(self.usage[t],
                       "Machine %d is down but has jobs at time period %d." %
                       (self.machineid, t))

    def compute_costs(self, actuals, forecasts):
        # Compute up and down costs
        upcost = self.up * sum(a for a, t in self.events)
        downcost = self.down * sum(1 - a for a, t in self.events)

        # Idle cost of running the machine
        idleactual = idlefore = 0.0
        for t, state in enumerate(self.status[:-1]):
            if actuals:
                idleactual += state * self.idle * actuals[t] * self.q / 60
            idlefore += state * self.idle * forecasts[t] * self.q / 60

        # Power consumption by running tasks
        poweractual = powerfore = 0.0
        for t, power in enumerate(self.power):
            if actuals:
                poweractual += power * actuals[t] * self.q / 60
            powerfore += power * forecasts[t] * self.q / 60

        return upcost, downcost, idleactual, idlefore, poweractual, powerfore

    def __str__(self):
        return "<Machine %d [%s]> " % \
            (self.machineid, ",".join(map(str, self.resoursecap)))


def errlog(truthtest, msg, *args, **kwargs):
    if not truthtest:
        logging.error(msg, *args, **kwargs)


def main(folder):
    instance = Instance()

    try:
        instance.read_instancefolder(folder)
        instance.verify()
        d = instance.day
        actual, forecast = instance.compute_costs()

    except Exception as e:
        print >> instance.errstream, type(e), str(e)

    errstr = instance.geterrorstring()
    if errstr:
        print >> sys.stderr, errstr
    else:
        if instance.actualsread:
            print "               %12s %12s" % ("Actual", "Forecast")
            print "-" * 40
            print "Machine up:    %12.4f %12.4f" % (d.cup, d.cup)
            print "Machine down:  %12.4f %12.4f" % (d.cdown, d.cdown)
            print "Machine idle:  %12.4f %12.4f" % (d.cm_act, d.cm_fore)
            print "Task costs:    %12.4f %12.4f" % (d.cj_act, d.cj_fore)
            print "-" * 40
            print "Total cost:    %12.4f %12.4f" % (actual, forecast)
        else:
            print "               %12s" % ("Forecast")
            print "-" * 27
            print "Machine up:    %12.4f" % d.cup
            print "Machine down:  %12.4f" % d.cdown
            print "Machine idle:  %12.4f" % d.cm_fore
            print "Task costs:    %12.4f" % d.cj_fore
            print "-" * 27
            print "Total cost:    %12.4f" % forecast


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: python %s instancefolder" % sys.argv[0]
        sys.exit(1)

    main(sys.argv[1])
