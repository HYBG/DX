<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>汉尧科技</title>
<?php
require "../phplib/hylib.php";
$hy = new hylib();
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
.date{
    width: 200px;
}
.feature{
    width: 150px;
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
    <table border="1" style="margin:0 auto;width:90%">
    <tr>
    <th class="date" rowspan="2">日期</th>
    <th colspan="6" rowspan="2">策略池</th>
    <th colspan="2">总量</th>
    <th>收盘分</th>
    </tr>
    <tr>
    <th colspan="2">上破率(%)</th>
    <th>下破率(%)</th>
    </tr>
    <tr>
    <th class="date" rowspan="2">2018-07-16</th>
    <th class="feature" colspan="3"><a href=\"hy.php?action=ft&date=\" target=\"_blank\">反弹</a></th>
    <th class="feature">背离</th>
    <th class="feature">&nbsp;</th>
    <th class="feature">&nbsp;</th>
    <th colspan="2">1</th>
    <th>3</th>
    </tr>
    <tr>
    <th class="feature"  colspan="3">突破</th>
    <th class="feature">上升</th>
    <th class="feature">&nbsp;</th>
    <th class="feature">&nbsp;</th>
    <th colspan="2">2</th>
    <th>4</th>
    </tr>
    </table>
  </div>
</body>
</html>