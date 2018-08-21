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
   <table style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:8%;">#</th>
          <th style="width:8%;">代码</th>
          <th style="width:8%;">名称</th>
          <th style="width:8%;">板块</th>
          <th style="width:8%;">日均成交量</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $codes = $hy->exe_sql_batch("select distinct code from hy.iknow_tags");
    $ld = $hy->exe_sql_one("select date from hy.iknow_data order by date desc limit 1");
    $data = array();
    foreach($codes as $code){
        $cnt = $hy->exe_sql_one("select count(*) from hy.iknow_data where code='".$code[0]."'");
        if (intval($cnt[0])<500){
            continue;
        }
        $vols = $hy->exe_sql_batch("select volwy from hy.iknow_data where code='".$code[0]."' and date<='".$ld[0]."' order by date desc limit 200");
        $allvol = 0;
        foreach($vols as $vol){
            $allvol = $allvol + floatval($vol[0]);
        }
        $ev = round($allvol/count($vols),2);
        $names = $hy->exe_sql_one("select name,tag from hy.iknow_tags where code='".$code[0]."' and tagtype='industry'");
        if(strpos($names[0],'ST') !== false){ 
            continue;
        }
        array_push($data,array($ev,$code[0],$names[0],$names[1]));
    }
    foreach($data as $val){
        $key_arrays[]=$val[0];
    }
    array_multisort($key_arrays,SORT_DESC,SORT_NUMERIC,$data);
    $date = date('Y-m-d');
    $sqls = array();
    for($i=0;$i<count($data);$i++){
        echo "<tr><td>".($i+1)."</td><td>".$data[$i][1]."</td><td>".$data[$i][2]."</td><td>".$data[$i][3]."</td><td>".$data[$i][0]."</td></tr>";
        if ($i<600){
            $sql = "insert into hy.iknow_watch(code,name,industry) values('".$data[$i][1]."','".$data[$i][2]."','".$data[$i][3]."')";
            //echo $sql;
            array_push($sqls,$sql);
        }
    }
    $hy->task($sqls);
?>
      </tbody>
    </table>
  </div>
</body>
</html>