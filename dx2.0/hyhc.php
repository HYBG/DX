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
        echo "<title>高位回踩(".$date.")</title>";
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
.columnname{
    width:10%;
    height:20px;
    cursor:pointer;
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
        echo "<h2><a href=\"hyhc.php?date=".$prev[0]."\">prev</a></h2>";
    }
    echo "<h2 id=\"H2\"></h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hyhc.php?date=".$next[0]."\">next</a></h2>";
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
          <th class="columnname">均线</th>
          <th class="columnname">当前价</th>
          <th class="columnname">涨跌幅(%)</th>
          <th class="columnname">下行空间(%)</th>
          <th class="columnname">金额(万元)</th>
        </tr>
      </thead>
      <tbody id="tbody">
      </tbody>
    </table>
  </div>
</body>
<script type="text/javascript">
<?php
    $codes = $hy->exe_sql_batch("select iknow_data.code from hy.iknow_data,hy.iknow_bollkd where hy.iknow_data.date='".$date."' and iknow_bollkd.date='".$date."' and  (iknow_data.code=iknow_bollkd.code) and (hy.iknow_data.close>hy.iknow_bollkd.mid) and (hy.iknow_data.close<hy.iknow_bollkd.mid+hy.iknow_bollkd.std)");
    echo "var data = new Array();\n";
    echo "var dt = \"".$date."\";\n";
    $cds = array();
    foreach($codes as $code){
        $data = $hy->exe_sql_batch("select close,high,date,volwy from hy.iknow_data where code='".$code[0]."' and date<='".$date."' order by date desc limit 20");
        if (count($data)<20){
            continue;
        }
        $cls = floatval($data[0][0]);
        $zdf = ($cls-floatval($data[1][0]))/floatval($data[1][0]);
        $volwy = $data[0][3];
        for ($i=1;$i<19;$i++){
            $dt = $data[$i][2];
            $high = floatval($data[$i][1]);
            $close = floatval($data[$i][0]);
            if (($high>floatval($data[$i+1][1])) and ($high>floatval($data[$i-1][1]))){
                $up = $hy->exe_sql_one("select mid+2*std from iknow_bollkd where code='".$code[0]."' and date='".$dt."'");
                if (floatval($data[$i][1])>floatval($up[0])){
                    array_push($cds,array($code[0],$cls,$zdf,$volwy));
                    break;
                }
            }
            else{
                $mid = $hy->exe_sql_one("select mid from iknow_bollkd where code='".$code[0]."' and date='".$dt."'");
                if ($close<floatval($mid[0])){
                    break;
                }
            }
        }
    }
    foreach($cds as $cd){
        $code = $cd[0];
        $close = $cd[1];
        $zdf = $cd[2];
        $volwy = $cd[3];
        $mid = $hy->exe_sql_one("select mid from iknow_bollkd where code='".$code."' and date='".$date."'");
        $mid = floatval($mid[0]);
        $names = $hy->exe_sql_one("select name,bdcode,bdname from iknow_name where code='".$code."'");
        $name = $names[0];
        $bdname = $names[1]."(".$names[2].")";
        $buf = ($close-$mid)/$mid;
        if ($buf<0.025 and $buf>-0.01){
            echo "data.push(Array(\"".$date."\",\"".$code."\",\"".$name."\",\"".$bdname."\",".$mid.",".$close.",".sprintf("%.2f",100*$zdf).",".sprintf("%.2f",100*$buf).",".$volwy."));\n";
        }
    }
?>

function fill(){
    var tbody = document.getElementById("tbody");
    for (i=0,len=data.length;i<len;i++){
        var row = document.createElement('tr');
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
        var mid = document.createElement('td');
        mid.innerHTML = data[i][4];
        row.appendChild(mid);
        var close = document.createElement('td');
        close.innerHTML = data[i][5];
        row.appendChild(close);
        var zdf = document.createElement('td');
        zdf.innerHTML = data[i][6];
        row.appendChild(zdf);
        var buf = document.createElement('td');
        buf.innerHTML = data[i][7];
        row.appendChild(buf);
        var volwy = document.createElement('td');
        volwy.innerHTML = data[i][8];
        row.appendChild(volwy);
        tbody.appendChild(row);
    }
}

$(document).ready(function(){
    fill();
    var hm = document.getElementById("H2");
    hm.innerHTML = dt+"("+data.length+")";
    var sorted = new Array(1,3,4,5,6,7,8);
    sort_tbody(sorted);
});
</script>
</html>