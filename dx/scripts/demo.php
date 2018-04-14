<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>汉尧科技</title>
<?php
require "../phplib/dx.php";
$dx = new dxlib();
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
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div class='table-cont' id='table-cont'>
   <table class="table table-striped" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:5%;">#</th>
          <th style="width:10%;">日期</th>
          <th style="width:10%;">总量</th>
          <th style="width:10%;">上突平均概率(%)</th>
          <th style="width:10%;">下突平均概率(%)</th>
          <th style="width:10%;">高点平均概率(%)</th>
          <th style="width:10%;">低点平均概率(%)</th>
        </tr>
      </thead>
      <tbody>
<?php
      if ($dx->isok()){
        if ($dx->select_db("dx")){
            $dates = $dx->exe_sql_batch("select distinct date from dx.iknow_tell order by date desc limit 40");
            for($i=0;$i<count($dates);$i++){
                $cnt = $dx->exe_sql_one("select count(*) from dx.iknow_tell where date='".$dates[$i][0]."'");
                $bcnt = $dx->exe_sql_one("select count(*) from dx.iknow_base where date='".$dates[$i][0]."'");
                $hbp = $dx->exe_sql_one("select avg(hbp) from dx.iknow_tell where date='".$dates[$i][0]."'");
                $lbp = $dx->exe_sql_one("select avg(lbp) from dx.iknow_tell where date='".$dates[$i][0]."'");
                $hpp = $dx->exe_sql_one("select avg(hpp) from dx.iknow_tell where date='".$dates[$i][0]."'");
                $lpp = $dx->exe_sql_one("select avg(lpp) from dx.iknow_tell where date='".$dates[$i][0]."'");
                echo "<tr><td>".($i+1)."</td>";
                echo "<td><a href=\"dxd.php?date=".$dates[$i][0]."\" target=\"_blank\">".$dates[$i][0]."</a></td>";
                echo "<td>".$cnt[0]."</td>";
                echo "<td>".sprintf("%.2f",100*floatval($hbp[0]))."</td>";
                echo "<td>".sprintf("%.2f",100*floatval($lbp[0]))."</td>";
                echo "<td>".sprintf("%.2f",100*floatval($hpp[0]))."</td>";
                echo "<td>".sprintf("%.2f",100*floatval($lpp[0]))."</td></tr>";
            }
        }
      }
?>
      </tbody>
    </table>
  </div>
</body>
</html>