<!DOCTYPE html>
<html>
 <head>
  <title>Submit to CP-meets-ML Leaderboard</title>
  <link href="css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="css/style.css" media="screen" />
 </head>

<body>
<div class="container">
<h2>Capita CP-meets-ML, submit</h2>
Leaderboard <a href="index.php">page</a>.

<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
$DIR = 'data/';


function do_load($teamid, $loadname, $load_starts, $task_starts) {
    $costs = array();

    // compute costs
    foreach($load_starts as $startday => $load_days) {
        if (!array_key_exists($startday, $task_starts)) {
            print "Error, load '".$loadname."': day '".$startday."' missing!";
            return;
        }
        $task_days = $task_starts[$startday];
        $cost = 0.0;
        foreach($load_days as $day => $load_day) {
            if (!array_key_exists($day, $task_days)) {
                print "Error, load '".$loadname."', day '".$startday."': f_inst '".$day."' missing!";
                return;
            }
            $task_day = $task_days[$day];
            $q = $load_day['q'];
            $actuals = $load_day['act'];
            foreach($load_day['tasks'] as $taskid => $load_task) {
                if (!array_key_exists($taskid, $task_day)) {
                    print "Error, load '".$loadname."', day '".$startday."', f_inst '".$day."': taskid '".$taskid."' missing!";
                    return;
                }
                $task_task = $task_day[$taskid];
                $start = $task_task['start'];
                $end = $start+$load_task['dur']; // non inclusive
                if ($start < $load_task['est']) {
                    print "Error, load '".$loadname."', day '".$startday."', f_inst '".$f."', taskid '".$taskid."': start before EST!";
                    return;
                }
                if ($end > $load_task['let']) {
                    print "Error, load '".$loadname."', day '".$startday."', f_inst '".$f."', taskid '".$taskid."': end after LET!";
                    return;
                }
                for ($i = $start; $i < $end; $i++)
                    $cost += (1.0*$load_task['pow']*$actuals[$i]*$q/60.0);
            }
        }
        $costs[$startday] = $cost;
    }

    // store costs
    print "Load '".$loadname."' costs:<br >";
    print_r($costs);
    print "<br />";
    $fname = "data/subm/team_".$teamid."_".$loadname.".json";
    $ok = file_put_contents($fname, json_encode($costs)."\n");
    if ($ok)
        print "Stored successfully.<br />";
    else
        print "<em>storing failed... mail Tias</em><br />";
}

function file_put_robust($filename, $entry, $nrtries) {
    for ($i = 0; $i < $nrtries; $i++) {
        // lock it and append a line
        $ok = file_put_contents($filename, $entry."\n", FILE_APPEND | LOCK_EX);
        if ($ok !== FALSE) return TRUE;
        usleep(100000); // micro seconds: 1000000 = 1 second
    }
    return FALSE;
}


// returns NULL or array( array('id': x, 'name': x, 'pwhash': x) )
function read_users() {
    global $DIR;
    $file_users = $DIR.'users.csv';
    if (($handle = fopen($file_users, "r")) === FALSE)
        return NULL;

    $ret = array();
    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE)
        array_push($ret, array('id'=> $data[0], 'name'=> $data[1], 'pwhash'=> $data[2]));

    fclose($handle);
    return $ret;
}

function write_user($data) {
    global $DIR;
    $file_users = $DIR.'users.csv';
    $entry = sprintf("%d,%s,%s", $data['id'], $data['name'], $data['pwhash']);
    file_put_robust($file_users, $entry, 10);
}

// returns NULL or array('id': x, 'name': x, 'pwhash': x)
function check_get_user($allusers, $user) {
    foreach ($allusers as $data) {
        if ($user == $data['name'])
            return $data;
    }
    return NULL;
}

if (isset($_POST['team'])) {
    $allusers = read_users();
    $team_dat = check_get_user($allusers, $_POST['team']);
    
    if ($team_dat == NULL) {
        $team_dat = array();
        $team_dat['id'] = end($allusers)['id']+1; // increment last known id 
        $team_dat['name'] = $_POST['team'];
        $team_dat['pwhash'] = hash('sha256', 'salty'.$_POST['pw']);
        write_user($team_dat);
    }

    if ($team_dat['pwhash'] !== hash('sha256', 'salty'.$_POST['pw'])) {
        print "<p><em>Wrong username/password combination!!</em></p>";
    } else {
        // OK, same pw, continue
        $tasks = json_decode($_POST['json'], true);

        $loads = json_decode(file_get_contents('data/server.json'), true);
        
        $x = false;
        foreach ($loads as $loadname => $load) {
            if (array_key_exists($loadname, $tasks)) {
                $x = true;
                do_load($team_dat['id'], $loadname, $load, $tasks[$loadname]);
            } else {
                print "No load '".$loadname."' in user-supplied json";
            }
        }
        if ($x) {
            print "<p>Correctly received the new loads, see <a href=\"index.php\">the leaderboard</a></p>";
        } else {
            print "<p><em>Warning, no usable loads in the JSON data</em></p>";
        }
    }
} else {
?>

<p>
Use the script to submit automatically, or submit here manually.
</p>

<p>
Note: the password you choose when first submitting has to be used for all subsequent submits.
</p>
<form action="submit.php" method="post">
  <fieldset>
    Teamname:<br>
    <input type="text" name="team"><br>
    Password:<br>
    <input type="text" name="pw"><br>
    JSON file:<br>
    <textarea name="json">
    </textarea><br><br>
    <input type="submit" value="Submit">
  </fieldset>
</form>
</div>

<?php
} // close else
?>
</body>
</html>
