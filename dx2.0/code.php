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
            $ld = $hy->exe_sql_one("select date from hy.iknow_data order by date desc limit 1");
            $date = $ld[0];
        }
        if (isset($code)){
            $name = $hy->exe_sql_one("select name from iknow_name where code='".$code."'");
            $name = $name[0];
            echo "<title>".$name."(".$date.")</title>";
        }
        else{
            echo "无相应数据";
            exit;
        }
    }
    else{
        echo "无相应DB";
        exit;
    }
}
else{
    echo "无相应DB";
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
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div id='table'>
<?php
    $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"code.php?date=".$prev[0]."&code=".$code."\">prev</a></h2>";
    }
    echo "<h2>".$date."</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"code.php?date=".$next[0]."&code=".$code."\">next</a></h2>";
    }
    echo "</div>";
?>
   <table style="margin:0 auto;width:90%" border="1" align="center">
      <tbody id="tbody">
<?php
      $data = $hy->exe_sql_batch("select date,open,high,low,close,volh from hy.iknow_data where code='".$code."' and date<='".$date."' order by date desc limit 2");
      if(count($data)<2){
          exit;
      }
      echo "<tr><td>代码</td><td>".$code."</td><td>名称</td><td>".$name."</td></tr>";
      echo "<tr><td>上破</td><td></td><td></td><td></td></tr>";
      echo "<tr><td>下破</td><td></td><td></td><td></td></tr>";
      echo "<tr><td>双破</td><td></td><td></td><td></td></tr>";
      echo "<tr><td>不破</td><td></td><td></td><td></td></tr>";
?>
      </tbody>
    </table>
  </div>
</body>
</html>