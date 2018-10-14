<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<?php
require "../phplib/hylib.php";
parse_str($_SERVER["QUERY_STRING"]);
$limt = 40;
if (isset($count)){
    $limt = intval($count);
    if ($limt<40){
        $limt = 40;
    }
}
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>HY</title>";
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
#pick{
    margin:20px;
    text-align:center;
}
#more{
    margin:20px;
}
#headbase{
    colspan:2
}
#headmore{
    colspan:6
}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<?php
echo "<h2><a href=\"ikrt.php\" target=\"_blank\">实时关注</a></h2>";
?>
<div id='table'>
   <table style="margin:0 auto;width:80%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:10%;">日期</th>
          <th style="width:10%;">总量</th>
          <th style="width:10%;">上破率(%)</th>
          <th style="width:10%;">下破率(%)</th>
          <th style="width:10%;">收盘分</th>
          <th style="width:8%;">氛围</th>
          <th style="width:8%;">氛围</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $dts = $hy->exe_sql_batch("select distinct date from iknow.ik_attr order by date desc limit ".$limt);
    foreach($dts as $dt){
        $all = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."'");
        $hbc = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and hb=1");
        $lbc = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and lb=1");
        $allvol = $hy->exe_sql_one("select sum(volwy) from ik_data where date='".$dt[0]."'");
        $hbvol = $hy->exe_sql_one("select sum(volwy) from ik_data where date='".$dt[0]."' and code in (select code from ik_attr where date='".$dt[0]."' and hb=1)");
        $lbvol = $hy->exe_sql_one("select sum(volwy) from ik_data where date='".$dt[0]."' and code in (select code from ik_attr where date='".$dt[0]."' and lb=1)");
        $src = $hy->exe_sql_one("select avg(csrc) from ik_attr where date='".$dt[0]."'");
        $hbr = round(100*(floatval($hbc[0])/floatval($all[0])),2);
        $lbr = round(100*(floatval($lbc[0])/floatval($all[0])),2);
        $hbvr = round(100*(floatval($hbvol[0])/floatval($allvol[0])),2);
        $lbvr = round(100*(floatval($lbvol[0])/floatval($allvol[0])),2);
        echo "<tr><td><a href=\"ikwatch.php?date=".$dt[0]."\" target=\"_blank\">".$dt[0]."</a></td>";
        echo "<td>".$all[0]."/".round(floatval($allvol[0])/10000,2)."</td>";
        echo "<td>".$hbr."/".$hbvr."</td>";
        echo "<td>".$lbr."/".$lbvr."</td>";
        echo "<td>".round(100*floatval($src[0]),2)."</td>";
        echo "<td bgcolor=\"#".sprintf("%02X",round((2.56*$hbr))).sprintf("%02X",round((2.56*$lbr)))."00\"></td>";
        echo "<td bgcolor=\"#".sprintf("%02X",round((2.56*$hbvr))).sprintf("%02X",round((2.56*$lbvr)))."00\"></td></tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>