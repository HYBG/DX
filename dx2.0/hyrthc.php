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
          <th class="columnname">当前价</th>
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
    $data = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_adjust"),true);
    echo "var data = new Array();\n";
    foreach($data as $row){
        $name = $hy->exe_sql_one("select name from hy.iknow_tags where code='".$row["code"]."' limit 1");
        echo "data.push(Array(\"".$row["date"]."\",\"".$row["time"]."\",\"".$row["code"]."\",\"".$name[0]."\",\"".$row["close"]."\",".$row["space"].",".$row["volwy"]."));\n";
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
        var close = document.createElement('td');
        close.innerHTML = data[i][4];
        row.appendChild(close);
        var dn = document.createElement('td');
        dn.innerHTML = data[i][5];
        row.appendChild(dn);
        var volwy = document.createElement('td');
        volwy.innerHTML = data[i][6];
        row.appendChild(volwy);
        tbody.appendChild(row);
    }
}

$(document).ready(function(){
    fill();
    var sorted = new Array(1,2,3,5,6,7);
    sort_tbody(sorted);
});
</script>
</html>