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
<a href="hyma.php" target=\"_blank\">MA</a>
</div>
<?php
echo "<h2><a href=\"hyrthc.php\" target=\"_blank\">实时回调</a>&nbsp;&nbsp;<a href=\"ikrt.php\" target=\"_blank\">实时关注</a></h2>";
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
          <th style="width:10%;">准备</th>
          <th style="width:8%;" colspan="2">氛围</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $data = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_base"),true);
    foreach($data as $row){
        $fix = 2.56*$row[7];
        $wei = 6;
        $cntredp = sprintf("%02X",round((($wei-1)*2.56*$row[2]+$fix))/$wei);
        $cntgrep = sprintf("%02X",round((($wei-1)*2.56*$row[3]+$fix))/$wei);
        $cntbkg = $cntredp.$cntgrep."00";
        $redp = sprintf("%02X",round((($wei-1)*2.56*$row[5]+$fix))/$wei);
        $grep = sprintf("%02X",round((($wei-1)*2.56*$row[6]+$fix))/$wei);
        $bkg = $redp.$grep."00";
        echo "<tr><td><a href=\"hyma.php?date=".$row[0]."\" target=\"_blank\">".$row[0]."</a></td>";
        echo "<td>".$row[1]."/".round($row[4],0)."</td>";
        echo "<td>".round($row[2],2)."/".round($row[5],2)."</td>";
        echo "<td>".round($row[3],2)."/".round($row[6],2)."</td>";
        echo "<td>".round($row[7],2)."</td>";
        echo "<td><a href=\"hywatch.php?date=".$row[0]."\" target=\"_blank\">关注</a></td>";
        echo "<td bgcolor=\"#".$cntbkg."\"></td>";
        echo "<td bgcolor=\"#".$bkg."\"></td></tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>