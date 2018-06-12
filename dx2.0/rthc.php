<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<!--<meta http-equiv="refresh" content="20">-->
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<?php
require "../phplib/hylib.php";
parse_str($_SERVER["QUERY_STRING"]);
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("hy")){
        $dt = date('Y-m-d H:i:s');
        echo "<title>实时回踩(".$dt.")</title>";
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
    $ld = $hy->exe_sql_one("select date from iknow_data order by date desc limit 1");
    $ld = $ld[0];
?>
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnname">日期</th>
          <th class="columnname">时间</th>
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
    $codes = $hy->exe_sql_batch("select iknow_data.code from hy.iknow_data,hy.iknow_bollkd where hy.iknow_data.date='".$ld."' and iknow_bollkd.date='".$ld."' and  (iknow_data.code=iknow_bollkd.code) and (hy.iknow_data.close>hy.iknow_bollkd.mid) and (hy.iknow_data.close<hy.iknow_bollkd.mid+2*hy.iknow_bollkd.std)");
    echo "var data = new Array();\n";
    $cds = array();
    $cddata = array();
    foreach($codes as $code){
        $data = $hy->exe_sql_batch("select close from hy.iknow_data where code='".$code[0]."' and date<='".$ld."' order by date desc limit 19");
        if (count($data)<19){
            continue;
        }
        array_push($cds,$code[0]);
        $cddata[$code[0]] = 0;
        foreach($data as $row){
            $cddata[$code[0]] = $cddata[$code[0]]+floatval($row[0]);
        }
    }
    if (count($cds)>800){
        $cds = array_slice($cds,0,800);
    }
    $hq = $hy->rtprices($cds);
    foreach($hq as $row){
        $cd = $row[0];
        $cur = $row[4];
        $dt = $row[9];
        $tm = $row[10];
        $volwy = strval(floor(floatval($row[5])/10000));
        if (array_key_exists($cd,$cddata) and ($cur<$row[8])){
            $mid = ($cddata[$cd]+$cur)/20;
            $names = $hy->exe_sql_one("select name,bdcode,bdname from iknow_name where code='".$cd."'");
            $name = $names[0];
            $bdname = $names[1]."(".$names[2].")";
            $zdf = (floatval($row[4])-floatval($row[8]))/floatval($row[8]);
            $buf = (floatval($cur)-$mid)/$mid;
            if ($buf<0.015){
                echo "data.push(Array(\"".$dt."\",\"".$tm."\",\"".$cd."\",\"".$name."\",\"".$bdname."\",".$mid.",".$cur.",".sprintf("%.2f",100*$zdf).",".sprintf("%.2f",100*$buf).",".$volwy."));\n";
            }
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
        var tm = document.createElement('td');
        tm.innerHTML = data[i][1];
        row.appendChild(tm);
        var code = document.createElement('td');
        code.innerHTML = data[i][2];
        row.appendChild(code);
        var name = document.createElement('td');
        name.innerHTML = data[i][3];
        row.appendChild(name);
        var bdname = document.createElement('td');
        bdname.innerHTML = data[i][4];
        row.appendChild(bdname);
        var mid = document.createElement('td');
        mid.innerHTML = data[i][5];
        row.appendChild(mid);
        var close = document.createElement('td');
        close.innerHTML = data[i][6];
        row.appendChild(close);
        var zdf = document.createElement('td');
        zdf.innerHTML = data[i][7];
        row.appendChild(zdf);
        var dn = document.createElement('td');
        dn.innerHTML = data[i][8];
        row.appendChild(dn);
        var volwy = document.createElement('td');
        volwy.innerHTML = data[i][9];
        row.appendChild(volwy);
        tbody.appendChild(row);
    }
}

$(document).ready(function(){
    fill();
    var sorted = new Array(1,3,4,5,6,7);
    sort_tbody(sorted);
});
</script>
</html>