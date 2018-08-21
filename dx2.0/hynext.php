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
    if (isset($date) and isset($code)){
        $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
        $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
        echo "<div>";
        if (count($prev)>0){
            echo "<h2><a href=\"hynext.php?date=".$prev[0]."&code=".$code."\">prev</a></h2>";
        }
        $name = $hy->exe_sql_one("select name from hy.iknow_tags where code='".$code."' limit 1");
        echo "<h2>".$name[0]."(".$code.")</h2>";
        if (count($next)>0){
            echo "<h2><a href=\"hynext.php?date=".$next[0]."&code=".$code."\">next</a></h2>";
        }
        echo "</div>";
    }
    elseif (isset($fv)){
        echo "<div>";
        echo "<h2>".$fv."</h2>";
        echo "</div>";
    }
?>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:8%;">代码</th>
          <th style="width:8%;">next</th>
          <th style="width:8%;">probability</th>
          <th style="width:8%;">open</th>
          <th style="width:8%;">high</th>
          <th style="width:8%;">low</th>
          <th style="width:8%;">close</th>
        </tr>
      </thead>
      <tbody id="tbody-ma">
<?php
    $use = null;
    if (isset($date) and isset($code)){
        $ffv = $hy->exe_sql_one("select ffv from hy.iknow_feature where code='".$code."' and date='".$date."'");
        $use = $ffv[0];
    }
    elseif (isset($fv)){
        $use = $fv;
    }
    $all = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$use."'");
    for($j=1;$j<=8;$j++){
        $its = $hy->exe_sql_one("select count(*) from hy.iknow_feature where fv='".$use."' and next=".$j);
        $openr = $hy->exe_sql_batch("select openr from hy.iknow_feature where fv='".$use."' and next=".$j." order by openr");
        $highr = $hy->exe_sql_batch("select highr from hy.iknow_feature where fv='".$use."' and next=".$j." order by highr");
        $lowr = $hy->exe_sql_batch("select lowr from hy.iknow_feature where fv='".$use."' and next=".$j." order by lowr");
        $closer = $hy->exe_sql_batch("select closer from hy.iknow_feature where fv='".$use."' and next=".$j." order by closer");
        $prob = round(100*(floatval($its[0])/floatval($all[0])),2);
        $openr = 100*$openr[count($openr)/2][0];
        $highr = 100*$highr[count($highr)/2][0];
        $lowr = 100*$lowr[count($lowr)/2][0];
        $closer = 100*$closer[count($closer)/2][0];
        echo "<tr>";
        if (isset($code)){
            echo "<td>".$code."</td>";
        }
        else{
            echo "<td>######</td>";
        }
        echo "<td>".$j."</td>";
        echo "<td>".$prob."</td>";
        echo "<td>".$openr."</td>";
        echo "<td>".$highr."</td>";
        echo "<td>".$lowr."</td>";
        echo "<td>".$closer."</td>";
        echo "</tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>