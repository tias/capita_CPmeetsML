% data
%%%%%%
int: nbMachines;
int: nbTasks;
int: nbRes;
set of int: Machines = 1..nbMachines;
set of int: Tasks = 1..nbTasks;
set of int: Res = 1..nbRes; % Resources

% Machine resources
array[Machines,Res] of int: m_res;

% Tasks
array[Tasks] of int: j_earl; % earliest start
array[Tasks] of int: j_late; % latest end
array[Tasks] of int: j_dur; % duration
array[Tasks] of float: j_power; % power use per time unit
array[Tasks,Res] of int: j_res;

% Energy
int: time_step;
float: q = int2float(time_step);
set of int: Times = 1..(round(24.0*60.0/q));
array[Times] of float: price;


% decis. variables
%%%%%%%%%%%%%%%%%%
% x_jmt: task j starts at time t on machine m
array[Tasks,Machines,Times] of var 0..1: x;

% Task constraints
%%%%%%%%%%%%%%%%%%


% Objective function
%%%%%%%%%%%%%%%%%%%%

var float: c_task = 0;

solve minimize c_task;

output  [ "Machine=\(m),Start=\(t),Task=\(j)\n" | m in Machines, t in Times, j in Tasks where fix(x[j,m,t])==1]++
        [ "Cost=\(c_task)" ];
