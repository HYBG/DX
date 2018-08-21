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
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hyma.php" target=\"_blank\">MA</a>
</div>
<div id='table'>
   <table border="1" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:10%;">日期</th>
          <th style="width:8%;">突破</th>
          <th style="width:8%;">背离</th>
          <th style="width:8%;">反弹</th>
          <th style="width:8%;">站上</th>
          <th style="width:8%;">打开</th>
          <th style="width:8%;">回踩</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $dates = $hy->exe_sql_batch("select distinct date from hy.iknow_status order by date desc limit ".$limt);
    for($i=0;$i<count($dates);$i++){
        $date = $dates[$i][0];
        $allvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_data where date='".$date."'");
        $brokenupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=1");
        $brokendnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=2");
        $deviupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=3");
        $devidnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=4");
        $rebupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=5");
        $rebdnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=6");
        $stdupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=7");
        $stddnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=8");
        $openupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=9");
        $opendnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=10");
        $adjustupvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=11");
        $adjustdnvol = $hy->exe_sql_one("select sum(volwy) from hy.iknow_status where date='".$date."' and status=12");
        $brokenupr = round(100*(floatval($brokenupvol[0])/floatval($allvol[0])),2);
        $brokendnr = round(100*(floatval($brokendnvol[0])/floatval($allvol[0])),2);
        $deviupr = round(100*(floatval($deviupvol[0])/floatval($allvol[0])),2);
        $devidnr = round(100*(floatval($devidnvol[0])/floatval($allvol[0])),2);
        $rebupr = round(100*(floatval($rebupvol[0])/floatval($allvol[0])),2);
        $rebdnr = round(100*(floatval($rebdnvol[0])/floatval($allvol[0])),2);
        $stdupr = round(100*(floatval($stdupvol[0])/floatval($allvol[0])),2);
        $stddnr = round(100*(floatval($stddnvol[0])/floatval($allvol[0])),2);
        $openupr = round(100*(floatval($openupvol[0])/floatval($allvol[0])),2);
        $opendnr = round(100*(floatval($opendnvol[0])/floatval($allvol[0])),2);
        $adjustupr = round(100*(floatval($adjustupvol[0])/floatval($allvol[0])),2);
        $adjustdnr = round(100*(floatval($adjustdnvol[0])/floatval($allvol[0])),2);
        echo "<tr>";
        echo "<td rowspan=\"2\"><a href=\"index.php target=\"_blank\">".$date."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=1\" target=\"_blank\">".$brokenupr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=3\" target=\"_blank\">".$deviupr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=5\" target=\"_blank\">".$rebupr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=7\" target=\"_blank\">".$stdupr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=9\" target=\"_blank\">".$openupr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=11\" target=\"_blank\">".$adjustupr."</a></td></tr>";
        
        echo "<tr><td><a href=\"hydetail.php?date=".$date."&status=2\" target=\"_blank\">".$brokendnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=4\" target=\"_blank\">".$devidnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=6\" target=\"_blank\">".$rebdnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=8\" target=\"_blank\">".$stddnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=10\" target=\"_blank\">".$opendnr."</a></td>";
        echo "<td><a href=\"hydetail.php?date=".$date."&status=12\" target=\"_blank\">".$adjustdnr."</a></td>";
        echo "</tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>