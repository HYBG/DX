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
        if (!isset($date) or !isset($status)){
            echo "无相应数据";
            exit;
        }
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
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hyma.php" target=\"_blank\">MA</a>&nbsp;&nbsp;<a href="hymore.php" target=\"_blank\">More</a>
</div>
<div id='table'>
<?php
    $prev = $hy->exe_sql_one("select date from iknow_status where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"hydetail.php?date=".$prev[0]."&status=".$status."\">prev</a></h2>";
    }
    echo "<h2>".$date."</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hydetail.php?date=".$next[0]."&status=".$status."\">next</a></h2>";
    }
    echo "</div>";
?>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:8%;">代码</th>
          <th style="width:8%;">名称</th>
          <th style="width:8%;">成交量</th>
          <th style="width:8%;">样本数</th>
          <th style="width:8%;">p1</th>
          <th style="width:8%;">p2</th>
          <th style="width:8%;">p3</th>
          <th style="width:8%;">p4</th>
          <th style="width:8%;">p5</th>
          <th style="width:8%;">p6</th>
          <th style="width:8%;">p7</th>
          <th style="width:8%;">p8</th>
        </tr>
      </thead>
      <tbody id="tbody-ma">
<?php
    $codes = $hy->exe_sql_batch("select distinct code from hy.iknow_status where date='".$date."' and status=".$status." order by volwy desc");
    for($i=0;$i<count($codes);$i++){
        $code = $codes[$i][0];
        $base = $hy->exe_sql_one("select high,low,close from hy.iknow_data where code='".$code."' and date='".$date."'");
        $hr = round((floatval($base[0])-floatval($base[2]))/(floatval($base[2])),4);
        $lr = round((floatval($base[1])-floatval($base[2]))/(floatval($base[2])),4);
        $ffv = $hy->exe_sql_one("select ffv from hy.iknow_feature where code='".$code."' and date='".$date."'");
        if (count($ffv)>0){
            $all = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and not (highr<=".$hr." and (next=1 or next=2 or next=5 or next=6)) and not (lowr>=".$lr." and (next=3 or next=4 or next=5 or next=6)) and not ((highr>".$hr." or lowr<".$lr.") and (next=7 or next=8))");
            $ps = array();
            $c1 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=1 and highr>".$hr." and lowr>=".$lr);
            array_push($ps,round(100*(floatval($c1[0])/floatval($all[0])),2));
            $c2 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=2 and highr>".$hr." and lowr>=".$lr);
            array_push($ps,round(100*(floatval($c2[0])/floatval($all[0])),2));
            $c3 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=3 and highr<=".$hr." and lowr<".$lr);
            array_push($ps,round(100*(floatval($c3[0])/floatval($all[0])),2));
            $c4 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=4 and highr<=".$hr." and lowr<".$lr);
            array_push($ps,round(100*(floatval($c4[0])/floatval($all[0])),2));
            $c5 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=5 and highr>".$hr." and lowr<".$lr);
            array_push($ps,round(100*(floatval($c5[0])/floatval($all[0])),2));
            $c6 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=6 and highr>".$hr." and lowr<".$lr);
            array_push($ps,round(100*(floatval($c6[0])/floatval($all[0])),2));
            $c7 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=7 and highr<=".$hr." and lowr>=".$lr);
            array_push($ps,round(100*(floatval($c7[0])/floatval($all[0])),2));
            $c8 = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$ffv[0]."' and next=8 and highr<=".$hr." and lowr>=".$lr);
            array_push($ps,round(100*(floatval($c8[0])/floatval($all[0])),2));
            echo "<tr>";
            echo "<td><a href=\"hynext.php?date=".$date."&code=".$code."\" target=\"_blank\">".$code."</a></td>";
            $some = $hy->exe_sql_one("select hy.iknow_name.name,hy.iknow_data.volwy from hy.iknow_name,hy.iknow_data where hy.iknow_data.code='".$code."' and hy.iknow_data.date='".$date."' and hy.iknow_name.code='".$code."'");
            echo "<td>".$some[0]."</td>";
            echo "<td>".$some[1]."</td>";
            echo "<td>".$all[0]."</td>";
            for($k=0;$k<8;$k++){
                echo "<td>".$ps[$k]."</td>";
            }
            echo "</tr>";
        }
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>