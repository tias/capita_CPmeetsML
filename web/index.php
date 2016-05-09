<!DOCTYPE html>
<html>
 <head>
  <title>CP-meets-ML Leaderboard</title>
  <link href="css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="css/style.css" media="screen" />
 </head>

<body>
<div class="container">
<h2>Capita CP-meets-ML, leaderboard</h2>
Manual submission <a href="submit.php">page</a>.

<p>
Numbers are total costs (over 14 consecutive days) for the shown loads and start dates.
</p>

<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
$DIR = 'data/';

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

function sortByTot($a, $b) {
    return $a['tot'] - $b['tot'];
}


// the real stuff
$allusers = read_users();
$loads = json_decode(file_get_contents('data/server.json'), true);

$perload = array();
foreach($loads as $loadname => $load) {
    $perload[$loadname] = array();
    $days = array_keys($load);

    // get relevant users
    foreach($allusers as $user) {
        $fname = $DIR.'subm/team_'.$user['id'].'_'.$loadname.'.json';
        if (file_exists($fname)) {
            $userload = json_decode(file_get_contents($fname), true);
            $tot = 0.0;
            foreach ($days as $day)
                $tot += $userload[$day];
            $userload['tot'] = $tot;
            $perload[$loadname][$user['name']] = $userload;
        }
    }
}

foreach($perload as $loadname => $loadusers) {
    print "<h2>".$loadname."</h2>";
    print "<table class=\"table\">";

    // header
    $days = array_keys($loads[$loadname]);
    asort($days);
    print "<tr>";
    print "<th>Team</th>";
    print "<th>Total</th>";
    foreach($days as $day)
        print "<th>".$day."</th>";
    print "</tr>";

    uasort($loadusers, 'sortByTot');
    foreach($loadusers as $username => $results) {
        print "<tr>";
        print "<td>".$username."</td>";
        print "<td>".$results['tot']."</td>";
        foreach($days as $day)
            print "<td>".$results[$day]."</td>";
        print "</tr>";
    }
    print "</table>";
}
?>
</body>
</html>
