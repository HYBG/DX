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
        echo "<title>加速上升(".$date.")</title>";
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
.columnname{
    width:10%;
    height:20px;
    cursor:pointer;
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
    $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"hytp.php?date=".$prev[0]."\">prev</a></h2>";
    }
    echo "<h2 id=\"H2\"></h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hytp.php?date=".$next[0]."\">next</a></h2>";
    }
    echo "</div>";
?>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnname">日期</th>
          <th class="columnname">代码</th>
          <th class="columnname">名称</th>
          <th class="columnname">板块</th>
          <th class="columnname">收盘</th>
          <th class="columnname">涨跌幅(%)</th>
          <th class="columnname">金额(万元)</th>
        </tr>
      </thead>
      <tbody id="tbody">

      </tbody>
    </table>
  </div>
<script type="text/javascript">
<?php
    $codes = $hy->exe_sql_batch("select distinct code from hy.iknow_data where date='".$date."'");
    echo "var data = new Array();\n";
    echo "var dt = \"".$date."\";\n";
    foreach($codes as $code){
        $data = $hy->exe_sql_batch("select macd from hy.iknow_macd where code='".$code[0]."' and date<='".$date."' order by date desc limit 2");
        if (count($data)<2){
            continue;
        }
        $ymacd = floatval($data[1][0]);
        $macd = floatval($data[0][0]);
        if (($macd>0 and $ymacd<0 and abs($macd)>5*abs($ymacd)) or ($macd>0 and $ymacd>0 and abs($macd)>3*abs($ymacd)) or ($macd>0 and $ymacd<0 and abs($ymacd)>6*abs($macd))){
            $base = $hy->exe_sql_batch("select close,volwy from hy.iknow_data where code='".$code[0]."' and date<='".$date."' order by date desc limit 2");
            $close = $base[0][0];
            $volwy = $base[0][1];
            $yc = $base[1][0];
            $zdf = (floatval($base[0][0])-floatval($base[1][0]))/floatval($base[1][0]);
            $names = $hy->exe_sql_one("select name,bdcode,bdname from hy.iknow_name where code='".$code[0]."'");
            $name = $names[0];
            $bdname = $names[1]."(".$names[2].")";
            echo "data.push(Array(\"".$date."\",\"".$code[0]."\",\"".$name."\",\"".$bdname."\",".$close.",".sprintf("%.2f",100*$zdf).",".$volwy."));\n";
        }
    }
?>

function fill(){
    var tbody = document.getElementById("tbody");
    for (i=0,len=data.length;i<len;i++){
        var row = document.createElement('tr');
        row.setAttribute("id",data[i][1]);
        var date = document.createElement('td');
        date.innerHTML = data[i][0];
        row.appendChild(date);
        var code = document.createElement('td');
        var a = document.createElement('a');
        a.innerHTML = data[i][1]; 
        a.setAttribute("href","hyc.php?code="+data[i][1]);
        a.setAttribute("target","_blank");
        code.appendChild(a);
        row.appendChild(code);
        var name = document.createElement('td');
        name.innerHTML = data[i][2];
        row.appendChild(name);
        var bdname = document.createElement('td');
        bdname.innerHTML = data[i][3];
        row.appendChild(bdname);
        var close = document.createElement('td');
        close.innerHTML = data[i][4];
        row.appendChild(close);
        var zdf = document.createElement('td');
        zdf.innerHTML = data[i][5];
        row.appendChild(zdf);
        var volwy = document.createElement('td');
        volwy.innerHTML = data[i][6];
        row.appendChild(volwy);
        tbody.appendChild(row);
    }
}

$(document).ready(function(){
    fill();
    var hm = document.getElementById("H2");
    hm.innerHTML = dt+"("+data.length+")";
    var sorted = new Array(1,3,4,5,6);
    sort_tbody(sorted);
});
</script>
</body>
</html>