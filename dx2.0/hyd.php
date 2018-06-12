<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<?php
require "../phplib/dx.php";
parse_str($_SERVER["QUERY_STRING"]);
if (!isset($date)){
    echo "无相应数据";
}
else{
    $dx = new dxlib();
    if ($dx->isok()){
        if ($dx->select_db("hy")){
            echo "<title>汉尧科技(".$date.")</title>";
        }
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
.columnname{
    width:10%;
    height:20px;
    cursor:pointer;
}
.columnno{
    width:5%;
    height:20px;
    cursor:pointer;
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<?php
    $prev = $dx->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $dx->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div><h2>";
    if (count($prev)>0){
        echo "<a href=\"hyd.php?date=".$prev[0]."\">prev</a>";
    }
    echo "&nbsp;".$date."&nbsp;";
    if (count($next)>0){
        echo "<a href=\"hyd.php?date=".$next[0]."\">next</a>";
    }
    echo "</h2></div>";
?>
<div id='find' style="margin:0 auto;width:90%">
<form id="inquiry" name="inquiry" method="post" action="hyc.php" target="_blank">
<input type="text" name="code" id="code" size="20" maxlength="6"/>
<label><input type="submit" name="Submit" value="GO" /></label>
</form>
<!--<input type='text' id='code' /><button id='goto' action="dxcode.php">GO TO</button>-->
</div>
<div id='table'>
   <table class="table table-striped" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnno">#</th>
          <th class="columnname">代码</th>
          <th class="columnname">名称</th>
          <th class="columnname">开盘</th>
          <th class="columnname">最高</th>
          <th class="columnname">最低</th>
          <th class="columnname">收盘</th>
          <th class="columnname">成交(手)</th>
          <th class="columnname">成交(万元)</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $data = $dx->exe_sql_batch("select code,open,high,low,close,volh,volwy from iknow_data where date='".$date."' order by code");
    $i=0;
    foreach($data as $row){
        $name = $dx->exe_sql_one("select name,bdname from iknow_name where code='".$row[0]."'");
        echo "<tr><td>".($i+1)."</td>";
        echo "<td><a href=\"hyc.php?code=".$row[0]."\" target=\"_blank\">".$row[0]."</a></td>";
        echo "<td>".$name[0]."</td>";
        echo "<td>".$row[1]."</td>";
        echo "<td>".$row[2]."</td>";
        echo "<td>".$row[3]."</td>";
        echo "<td>".$row[4]."</td>";
        echo "<td>".$row[5]."</td>";
        echo "<td>".$row[6]."</td></tr>";
        $i++;
    }
?>
      </tbody>
    </table>
  </div>
<script type="text/javascript">
</script>
</body>
</html>