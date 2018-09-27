<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<script src="./js/echarts.min.js"></script>
<?php
require "../phplib/hylib.php";
parse_str($_SERVER["QUERY_STRING"]);
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("hy")){
        echo "<title>HY RT</title>";
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
.up {color: #FF0000}
.dn {color: #00FF00}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div><h1 id="header">汉尧科技</h1></div>
<div id="home"><a href="index.php" target=\"_blank\">Home</a></div>
<div id='table'>
<table style=\"margin:0 auto;width:90%\" border=\"1\">
<?php
    $data = $hy->exe_sql_batch("select code,name,industry,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8,kfv2,kfv2cnt,kfv2p1,kfv2p2,kfv2p3,kfv2p4,kfv2p5,kfv2p6,kfv2p7,kfv2p8,bfv2,bfv2cnt,bfv2p1,bfv2p2,bfv2p3,bfv2p4,bfv2p5,bfv2p6,bfv2p7,bfv2p8,mfv2,mfv2cnt,mfv2p1,mfv2p2,mfv2p3,mfv2p4,mfv2p5,mfv2p6,mfv2p7,mfv2p8 from ik_rt where watch=1");
    foreach($data as $row){
        $mas = array(array($row[9],"close"),array($row[10],"ma5"),array($row[11],"ma10"),array($row[12],"ma20"),array($row[13],"ma30"),array($row[14],"ma60"));
        $keys = array();
        foreach($mas as $val){
            array_push($keys,$val[0]);
        }
        array_multisort($keys,SORT_DESC,SORT_NUMERIC,$mas);
        echo "<tr><td width=\"80\">名字</td><td width=\"160\"><a href=\"hycode.php?code=".$row[0]."\" target=\"_blank\">".$row[1]."(".$row[0].")--".$row[2]."</a></td><td width=\"80\">".$mas[0][1]."</td><td width=\"80\">".$mas[0][0]."</td><td width=\"80\" class=\"".$cla."\">".round(100*(($mas[0][0]-$close)/$close),2)."%</td></tr>";
    }
?>
</table>
</div>
</div>
</body>
</html>



