#!/usr/bin/env python

MZNSOLUTIONBASENAME = "minizinc.out"

import sys
import os
import shutil
import argparse
import random
import subprocess
import tempfile
import time
import glob


cwd=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(cwd,'scripts'))
from checker import *
import instance2dzn as i2dzn
import forecast2dzn as f2dzn
import checker_mzn as chkmzn

def basename(fname):
    return os.path.splitext(os.path.basename(fname))[0]

# source: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    def ext_candidates(fpath):
        yield fpath
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            yield fpath + ext

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            for candidate in ext_candidates(exe_file):
                if is_exe(candidate):
                    return candidate

    return None

def mzn_run(file_mzn, file_instance, data_forecasts, tmpdir, mzn_solver='mzn-g12mip', mzn_dir=None, print_output=False, verbose=0, check_win_hack=True):
    # ./instance2dzn.py ../smallinstances/demo_00/instance.txt
    # TODO: maybe this should (have) use(d) Instance() from checker...
    data = i2dzn.read_instance(file_instance)
    i2dzn.make_offset1(data)
    dzn_data = i2dzn.get_dzn(data)
    dzn_instance = join(tmpdir, "%s.dzn"%basename(file_instance))
    with open(dzn_instance, 'w') as fout:
        fout.write(dzn_data)
    if verbose >= 2:
        print "Written dzn_instance to",dzn_instance

    # ./forecast2dzn.py -t 30 forecast.txt
    # starts from actual data
    dzn_data_forecasts = f2dzn.get_forecast_dzn(data_forecasts)
    dzn_forecast = join(tmpdir, "forecast.dzn")
    with open(dzn_forecast, 'w') as fout:
        fout.write(dzn_data_forecasts)
    if verbose >= 2:
        print "Written dzn_forecast to:", dzn_forecast

    # every more checks in case people don't set their path...
    env = os.environ.copy()
    if mzn_dir:
        env['PATH'] += os.pathsep + mzn_dir
    if not which('minizinc'):
        print "Error: '%s' not on PATH (nor in --mzn-dir)"%'minizinc'
        sys.exit(1)
    mzn_solver_bin = which(mzn_solver)
    if mzn_solver_bin == None:
        print "Error: '%s' not on PATH (nor in --mzn-dir)"%mzn_solver
        sys.exit(1)
    # Special hack for some windows users:
    if check_win_hack and os.name == "nt":
        if not mzn_solver_bin.endswith('.bat'):
            mzn_solver_bin += '.bat'

    # mzn-g12mip energy_noupdown.mzn ../smallinstances/demo_00/instance.dzn forecast.dzn > minizinc.out
    cmd = [mzn_solver, file_mzn, dzn_instance, dzn_forecast]
    if verbose >= 1:
        print "Running:", " ".join(cmd)

    time_start = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out, err = p.communicate()
    timing = (time.time() - time_start)

    if print_output or verbose >= 1:
        print "Output: \"\"\""
        print out
        print "\"\"\""
    if err != None and err.strip() != "":
        print "Error running '%s':"%(' '.join(cmd))
        print err
    else:
        out = out.split('\n')
        #print "done, ",[x for x in out if x.startswith('Cost=')]
        return (timing, out)

    return (timing, None)

def mzn_toInstance(file_instance, out, data_forecasts, data_actual=None, pretty_print=False, verbose=0):
        # ./checker_mzn.py ../smallinstances/demo_01
        instance = Instance()

        # read standard instance and load forecast
        instance.read_instance(file_instance)
        instance.load_forecast(data_forecasts)
        if data_actual:
            instance.load_actual(data_actual)
        # load minizinc solution from 'out'
        chkmzn.read_mznsolution(instance, out)

        if pretty_print or verbose >= 1:
            chkmzn.pretty_print(instance)

        instance.verify()
        errstr = instance.geterrorstring()
        if errstr:
            print "Error: Error trying to verify the instance: '%s'"%(errstr)
            print >> sys.stderr, errstr
        else:
            return instance

        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run and check a MZN model in ICON challenge data")
    parser.add_argument("file_mzn")
    parser.add_argument("file_instance", help="(can also be a directory to run everything matching 'day*.txt' in the directory)")
    parser.add_argument("file_forecast")
    parser.add_argument("--mzn-solver", help="the mzn solver to use (mzn-g12mip or mzn-gecode for example)", default='mzn-g12mip')
    parser.add_argument("--mzn-dir", help="optionally, if the binaries are not on your PATH, set this to the directory of the MiniZinc IDE", default="")
    parser.add_argument("--tmp", help="temp directory (default = automatically generated)")
    # debugging options:
    parser.add_argument("-p", "--print-pretty", help="pretty print the machines and tasks", action="store_true")
    parser.add_argument("-v", help="verbosity (0,1 or 2)", type=int, default=0)
    parser.add_argument("--print-output", help="print the output of minizinc", action="store_true")
    parser.add_argument("--tmp-keep", help="keep created temp subdir", action="store_true")
    args = parser.parse_args()
    
    # if you want to hardcode the MiniZincIDE path for the binaries, here is a resonable place to do that
    #args.mzn_dir = "/home/tias/local/src/MiniZincIDE-2.0.13-bundle-linux-x86_64"

    tmpdir = ""
    if args.tmp:
        tmpdir = args.tmp
        os.mkdir(args.tmp)
    else:
        tmpdir = tempfile.mkdtemp()

    # single or multiple instances
    f_instances = [args.file_instance]
    if os.path.isdir(args.file_instance):
        globpatt = os.path.join(args.file_instance, 'day*.txt')
        f_instances = sorted(glob.glob(globpatt))

    # prep data_forecasts (same for all instances here)
    data_forecasts = f2dzn.read_forecast(args.file_forecast)
    timestep = i2dzn.read_instance(f_instances[0])['time_step']
    data_forecasts = f2dzn.rescale(timestep, data_forecasts)

    # the actual stuff
    for (i,f) in enumerate(f_instances):
        (timing, out) = mzn_run(args.file_mzn, f, data_forecasts,
                                tmpdir, mzn_dir=args.mzn_dir,
                                mzn_solver=args.mzn_solver,
                                print_output=args.print_output,
                                verbose=args.v)
        instance = mzn_toInstance(f, out, data_forecasts,
                                  pretty_print=args.print_pretty,
                                  verbose=args.v)
        # csv print:
        chkmzn.print_instance_csv(f, args.file_forecast, instance, timing=timing, header=(i==0))

    if not args.tmp_keep:
        shutil.rmtree(tmpdir)
