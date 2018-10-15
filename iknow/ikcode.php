<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<script src="./js/echarts.min.js"></script>
<?php
require "../phplib/hylib.php";
$hy = new hylib('root','123456');
#$hy->setmode("debug");
parse_str($_SERVER["QUERY_STRING"]);
if (!isset($code)){
    echo "无相应数据";
    exit;
}
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>".$code."</title>";
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
#header{
    text-shadow:10px 10px 10px #FF8C00;
    color:#FF4500;
    padding:20px;
    text-align:center;
    font-size:400%;
}

}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div><h1 id="header">汉尧科技</h1></div>
<div id="home"><p style="margin-left:200px"><a href="index.php" target=\"_blank\">Home</a></p></div>
<div id='table'>
<table style="margin:0 auto;width:90%" border="1">
<thead style="background-color:#E0EEEE">
<tr><th width="80">日期</th><th width="20">成交量</th><th width="20">特征值</th><th width="20">P1</th><th width="20">P2</th><th width="20">P3</th><th width="20">P4</th><th width="20">P5</th><th width="20">P6</th><th width="20">P7</th><th width="20">P8</th></tr></thead>
<?php
    $names = $hy->exe_sql_one("select name,industry from ik_rt where code='".$code."'");
    $name = $names[0];
    $inds = $names[1];
    echo "<div>";
    echo "<h2>".$name."(".$code.")----".$inds."</h2>";
    echo "</div>";
    $data = $hy->exe_sql_batch("select date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from ik_next where code='".$code."' order by date desc");
    foreach($data as $row){
        $vol = $hy->exe_sql_one("select volwy from ik_data where code='".$code."' and date='".$row[0]."'");
        echo "<tr><th>".$row[0]."</th><th>".$vol[0]."</th><th>".$row[1]."(".$row[2].")</th><th>".$row[3]."</th><th>".$row[4]."</th><th>".$row[5]."</th><th>".$row[6]."</th><th>".$row[7]."</th><th>".$row[8]."</th><th>".$row[9]."</th><th>".$row[10]."</th></tr>";
    }
?>
</table>
</div>
</div>
</body>
</html>