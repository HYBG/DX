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
    if ($hy->select_db("iknow")){
        if (!isset($date)){
            $date = $hy->exe_sql_one("select date from ik_attr order by date desc limit 1");
            $date = $date[0];
        }
        echo "<title>IKWatch(".$date.")</title>";
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
    $prev = $hy->exe_sql_one("select date from ik_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from ik_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"ikwatch.php?date=".$prev[0]."\">prev</a></h2>";
    }
    echo "<h2>Watch(".$date.")</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"ikwatch.php?date=".$next[0]."\">next</a></h2>";
    }
    echo "</div>";
?>
<table style="margin:0 auto;width:90%" border="1">
<thead style="background-color:#E0EEEE">
<tr><th width="10">#</th><th width="80">名称</th><th width="40">板块</th><th width="20">成交量</th><th width="20">特征值</th><th width="20">P1</th><th width="20">P2</th><th width="20">P3</th><th width="20">P4</th><th width="20">P5</th><th width="20">P6</th><th width="20">P7</th><th width="20">P8</th></tr></thead>
<?php
    $data = $hy->exe_sql_batch("select code,date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from iknow.ik_next where date='".$date."' and code in (select code from ik_rt where watch=1) order by fv4p1 desc");
    for($i=0;$i<count($data);$i++){
        $row = $data[$i];
        $names = $hy->exe_sql_one("select ik_rt.name,ik_rt.industry,ik_data.volwy from ik_rt,ik_data where ik_rt.code='".$row[0]."' and ik_data.code='".$row[0]."' and ik_data.date='".$row[1]."'");
        echo "<tr><td>".($i+1)."</td><td><a href=\"ikcode.php?code=".$row[0]."&date=".$date."\" target=\"_blank\">".$names[0]."(".$row[0].")"."</a></td><td>".$names[1]."</td><td>".$names[2]."</td><td>".$row[2]."(".$row[3].")</td><td>".$row[4]."%</td><td>".$row[5]."%</td><td>".$row[6]."%</td><td>".$row[7]."%</td><td>".$row[8]."%</td><td>".$row[9]."%</td><td>".$row[10]."%</td><td>".$row[11]."%</td></tr>";
    }
?>
</table>

</div>
</body>
</html>