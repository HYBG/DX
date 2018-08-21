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
    if ($hy->select_db("hy")){
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
<div id="more">
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hymore.php" target=\"_blank\">More</a>
</div>
<div id='table-ma'>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:8%;">日期</th>
          <th style="width:8%;">MA5up</th>
          <th style="width:8%;">MA5dn</th>
          <th style="width:8%;">MA10up</th>
          <th style="width:8%;">MA10dn</th>
          <th style="width:8%;">MA20up</th>
          <th style="width:8%;">MA20dn</th>
          <th style="width:8%;">MA30up</th>
          <th style="width:8%;">MA30dn</th>
          <th style="width:8%;">MA60up</th>
          <th style="width:8%;">MA60dn</th>
        </tr>
      </thead>
      <tbody id="tbody-ma">
<?php
    $dates = $hy->exe_sql_batch("select distinct date from hy.iknow_status order by date desc limit ".$limt);
    for($i=0;$i<count($dates);$i++){
        $date = $dates[$i][0];
        $allvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_data where date='".$date."'");
        $ma5upvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=51");
        $ma5dnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=52");
        $ma10upvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=53");
        $ma10dnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=54");
        $ma20upvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=55");
        $ma20dnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=56");
        $ma30upvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=57");
        $ma30dnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=58");
        $ma60upvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=59");
        $ma60dnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=60");
        $ma5upr = round(100*(floatval($ma5upvol[0])/floatval($allvol[0])),2);
        $ma5dnr = round(100*(floatval($ma5dnvol[0])/floatval($allvol[0])),2);
        $ma10upr = round(100*(floatval($ma10upvol[0])/floatval($allvol[0])),2);
        $ma10dnr = round(100*(floatval($ma10dnvol[0])/floatval($allvol[0])),2);
        $ma20upr = round(100*(floatval($ma20upvol[0])/floatval($allvol[0])),2);
        $ma20dnr = round(100*(floatval($ma20dnvol[0])/floatval($allvol[0])),2);
        $ma30upr = round(100*(floatval($ma30upvol[0])/floatval($allvol[0])),2);
        $ma30dnr = round(100*(floatval($ma30dnvol[0])/floatval($allvol[0])),2);
        $ma60upr = round(100*(floatval($ma60upvol[0])/floatval($allvol[0])),2);
        $ma60dnr = round(100*(floatval($ma60dnvol[0])/floatval($allvol[0])),2);
        echo "<tr>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=51\" target=\"_blank\">".$date."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=51\" target=\"_blank\">".$ma5upr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=52\" target=\"_blank\">".$ma5dnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=53\" target=\"_blank\">".$ma10upr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=54\" target=\"_blank\">".$ma10dnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=55\" target=\"_blank\">".$ma20upr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=56\" target=\"_blank\">".$ma20dnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=57\" target=\"_blank\">".$ma30upr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=58\" target=\"_blank\">".$ma30dnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=59\" target=\"_blank\">".$ma60upr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=60\" target=\"_blank\">".$ma60dnr."</a></td>";
        echo "</tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>