<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>汉尧科技</title>
<?php
require "../phplib/dx.php";
$dx = new dxlib();
parse_str($_SERVER["QUERY_STRING"]);
$limt = 40;
if (isset($count)){
    $limt = intval($count);
    if ($limt<40){
        $limt = 40;
    }
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
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div id='table'>
<?php
      if ($dx->isok()){
        if ($dx->select_db("hy")){
            $status = $dx->exe_sql_one("select value from hy.iknow_conf where name='status'");
            if ($status[0]=="busy"){
                echo "<h2>后台清算时间,数据可能不准确</h2>";
            }
            echo "<h2><a href=\"hyrthc.php\" target=\"_blank\">实时回调</a></h2>";
        }
      }
?>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:5%;">#</th>
          <th style="width:10%;">日期</th>
          <th style="width:10%;">总量</th>
          <th style="width:10%;">上破率(%)</th>
          <th style="width:10%;">下破率(%)</th>
          <th style="width:10%;">收盘分</th>
          <th style="width:15%;">策略</th>
        </tr>
      </thead>
      <tbody>
<?php
    $dates = $dx->exe_sql_batch("select distinct date from hy.iknow_kinfo order by date desc limit ".$limt);
    for($i=0;$i<count($dates);$i++){
        $cnt = $dx->exe_sql_one("select count(*) from hy.iknow_kinfo where date='".$dates[$i][0]."'");
        $hbcnt = $dx->exe_sql_one("select count(*) from hy.iknow_kinfo where date='".$dates[$i][0]."' and hb=1");
        $lbcnt = $dx->exe_sql_one("select count(*) from hy.iknow_kinfo where date='".$dates[$i][0]."' and lb=1");
        $src = $dx->exe_sql_one("select avg(csrc) from hy.iknow_kinfo where date='".$dates[$i][0]."'");
        echo "<tr><td>".($i+1)."</td>";
        echo "<td><a href=\"hyd.php?date=".$dates[$i][0]."\" target=\"_blank\">".$dates[$i][0]."</a></td>";
        echo "<td>".$cnt[0]."</td>";
        echo "<td>".sprintf("%.2f",100*($hbcnt[0]/$cnt[0]))."</td>";
        echo "<td>".sprintf("%.2f",100*($lbcnt[0]/$cnt[0]))."</td>";
        echo "<td>".sprintf("%.2f",floatval(100*$src[0]))."</td>";
        echo "<td><a href=\"hya.php?date=".$dates[$i][0]."\" target=\"_blank\">分析</a><a href=\"hyft.php?date=".$dates[$i][0]."\" target=\"_blank\">反弹</a><a href=\"hyzs.php?date=".$dates[$i][0]."\" target=\"_blank\">站上</a><a href=\"hyup.php?date=".$dates[$i][0]."\" target=\"_blank\">上升</a><a href=\"hyqr.php?date=".$dates[$i][0]."\" target=\"_blank\">确认</a><a href=\"hyhc.php?date=".$dates[$i][0]."\" target=\"_blank\">回踩</a><a href=\"hybl.php?date=".$dates[$i][0]."\" target=\"_blank\">背离</a><a href=\"hytp.php?date=".$dates[$i][0]."\" target=\"_blank\">加速</a></td></tr>";
    }
?>
      </tbody>
    </table>
  </div>
</body>
</html>