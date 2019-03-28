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
<div id='table'>
   <table style="margin:0 auto;width:80%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:10%;">日期</th>
          <th style="width:10%;">代码</th>
          <th style="width:10%;">名称</th>
          <th style="width:10%;">成交量(万元)</th>
          <th style="width:10%;">均值</th>
          <th style="width:10%;">状态(kd)</th>
          <th style="width:10%;">状态(macd)</th>
          <th style="width:10%;">状态(ma)</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $data = $hy->exe_sql_batch("select date,code,name,volwy,mean,kdstatus,macdstatus,mastatus from ik_pool order by date desc,volwy desc limit ".$limt);
    foreach($data as $row){
        echo "<tr><td>".$row[0]."</td>";
        echo "<td><a href=\"ikcode.php?date=".$row[1]."\" target=\"_blank\">".$row[1]."</a></td>";
        echo "<td>".$row[2]."</td>";
        echo "<td>".$row[3]."</td>";
        echo "<td>".$row[4]."</td>";
        echo "<td>".$row[5]."</td>";
        echo "<td>".$row[6]."</td>";
        echo "<td>".$row[7]."</td></tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>