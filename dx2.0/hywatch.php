<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<?php
require "../phplib/hylib.php";
parse_str($_SERVER["QUERY_STRING"]);
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("hy")){
        if (!isset($date)){
            $date = $hy->exe_sql_one("select date from iknow_attr order by date desc limit 1");
            $date = $date[0];
        }
        echo "<title>Watch(".$date.")</title>";
    }
    else{
        echo "无相应数据";
        exit;
    }
}
else{
    echo "无相应数据";
    exit;
}
?>
<style type="text/css">
*{
    margin:0;
    padding:0;
}
h2{
    margin:20px;
    text-align:center;
}
tr{
    text-align:center;
}
td.sorted{
    background-color:#FFD000;
}
.up {color: #FF0000}
.dn {color: #00FF00}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div id="more">
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hyma.php" target=\"_blank\">MA</a>
</div>
<div id='table'>
<?php
function echotable($data,$date){
    echo "<table style=\"margin:0 auto;width:90%\" border=\"1\">";
    echo "<thead style=\"background-color:#E0EEEE\">";
    echo "<tr><th width=\"10\">#</th><th width=\"80\">名称</th><th width=\"40\">板块</th><th width=\"20\">成交量</th><th width=\"20\">特征值</th><th width=\"20\">P1</th><th width=\"20\">P2</th><th width=\"20\">P3</th><th width=\"20\">P4</th><th width=\"20\">P5</th><th width=\"20\">P6</th><th width=\"20\">P7</th><th width=\"20\">P8</th></tr></thead>";
    for($i=0;$i<count($data);$i++){
        $code = $data[$i][0];
        $name = $data[$i][1];
        $inds = $data[$i][2];
        $volwy = $data[$i][3];
        $fv = $data[$i][4];
        $fvcnt = $data[$i][5];
        $probs = $data[$i][6];
        echo "<tr><td>".($i+1)."</td><td><a href=\"hycode.php?code=".$code."&date=".$date."\" target=\"_blank\">".$name."(".$code.")"."</a></td><td>".$inds."</td><td>".$volwy."</td><td>".$fv."(".$fvcnt.")</td><td>".$probs[0]."%</td><td>".$probs[1]."%</td><td>".$probs[2]."%</td><td>".$probs[3]."%</td><td>".$probs[4]."%</td><td>".$probs[5]."%</td><td>".$probs[6]."%</td><td>".$probs[7]."%</td></tr>";
    }
    echo "</table>";
}
    $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"hywatch.php?date=".$prev[0]."\">prev</a></h2>";
    }
    echo "<h2>Watch(".$date.")</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hywatch.php?date=".$next[0]."\">next</a></h2>";
    }
    echo "</div>";

    $data = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_watch&date=".$date,true));
    echotable($data,$date);
?>
  </div>
</body>
</html>