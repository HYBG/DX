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
$data = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_rt",true));
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
.up {color: #FF0000}
.dn {color: #00FF00}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div id="more">
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hyma.php" target=\"_blank\">MA</a>
</div>
<?php
function updn($exp){
    $cla = "up";
    if ($exp<0){
        $cla = "dn";
    }
    return $cla;
}
    $hbr = $data[0];
    $lbr = $data[1];
    $csrc = $data[2];
    echo "<div style=\"margin:0 auto;width:90%\">上破率:".$hbr."% 下破率:".$lbr."% 当前价格平均分:".round($csrc,2)." 标的数量:".count($data[3])."</div>";
    echo "<div id='table'>";
    echo "<table style=\"margin:0 auto;width:90%\" border=\"1\">";
    foreach($data[3] as $row){
        $close = $row[15];
        $mas = array(array($row[15],"close"),array($row[17],"ma5"),array($row[18],"ma10"),array($row[19],"ma20"),array($row[20],"ma30"),array($row[21],"ma60"));
        $keys = array();
        foreach($mas as $val){
            array_push($keys,$val[0]);
        }
        array_multisort($keys,SORT_DESC,SORT_NUMERIC,$mas);
        $cla = updn($mas[0][0]-$close);
        echo "<tr><td width=\"80\">名字</td><td width=\"160\"><a href=\"hycode.php?code=".$row[0]."\" target=\"_blank\">".$row[2]."(".$row[0].")--".$row[3]."</a></td><td width=\"80\">".$mas[0][1]."</td><td width=\"80\">".$mas[0][0]."</td><td width=\"80\" class=\"".$cla."\">".round(100*(($mas[0][0]-$close)/$close),2)."%</td></tr>";
        $cla = updn($mas[1][0]-$close);
        echo "<tr><td>时间</td><td>".$row[1]."</td><td>".$mas[1][1]."</td><td>".$mas[1][0]."</td><td class=\"".$cla."\">".round(100*(($mas[1][0]-$close)/$close),2)."%</td></tr>";
        $cla = updn($mas[2][0]-$close);
        $zdfcla = updn($row[4]);
        echo "<tr><td>涨跌幅</td><td class=\"".$zdfcla."\">".($row[4])."%</td><td>".$mas[2][1]."</td><td>".$mas[2][0]."</td><td class=\"".$cla."\">".round(100*(($mas[2][0]-$close)/$close),2)."%</td></tr>";
        $cla = updn($mas[3][0]-$close);
        echo "<tr><td>成交量</td><td>".$row[8]."/<span class=\"up\">".$row[9]."</span></td><td>".$mas[3][1]."</td><td>".$mas[3][0]."</td><td class=\"".$cla."\">".round(100*(($mas[3][0]-$close)/$close),2)."%</td></tr>";
        $cla = updn($mas[4][0]-$close);
        echo "<tr><td>特征值</td><td>".$row[13]."(".$row[14].")</td><td>".$mas[4][1]."</td><td>".$mas[4][0]."</td><td class=\"".$cla."\">".round(100*(($mas[4][0]-$close)/$close),2)."%</td></tr>";
        $cla = updn($mas[5][0]-$close);
        $claev = updn($row[16]);
        echo "<tr><td>收盘中位</td><td class=\"".$claev."\">".(100*$row[16])."%</td><td>".$mas[5][1]."</td><td>".$mas[5][0]."</td><td class=\"".$cla."\">".round(100*(($mas[5][0]-$close)/$close),2)."%</td></tr>";
        
        $claev = updn($row[12]);
        $cla = updn($row[10]-$row[11]);
        echo "<tr><td>MACD</td><td class=\"".$claev."\">".round($row[12],4)."</td><td>KD</td><td>".round($row[10],2)."/".round($row[11],2)."</td><td class=\"".$cla."\">".round($row[10]-$row[11],2)."</td></tr>";

        echo "<tr><td class=\"up\">".$row[22]."%</td><td>".(100*$row[23])."%</td><td>".(100*$row[24])."%</td><td>".(100*$row[25])."%</td><td>".(100*$row[26])."%</td></tr>";
        echo "<tr><td>".$row[27]."%</td><td>".(100*$row[28])."%</td><td>".(100*$row[29])."%</td><td>".(100*$row[30])."%</td><td>".(100*$row[31])."%</td></tr>";
        echo "<tr><td>".$row[32]."%</td><td>".(100*$row[33])."%</td><td>".(100*$row[34])."%</td><td>".(100*$row[35])."%</td><td>".(100*$row[36])."%</td></tr>";
        echo "<tr><td>".$row[37]."%</td><td>".(100*$row[38])."%</td><td>".(100*$row[39])."%</td><td>".(100*$row[40])."%</td><td>".(100*$row[41])."%</td></tr>";
        echo "<tr><td>".$row[42]."%</td><td>".(100*$row[43])."%</td><td>".(100*$row[44])."%</td><td>".(100*$row[45])."%</td><td>".(100*$row[46])."%</td></tr>";
        echo "<tr><td>".$row[47]."%</td><td>".(100*$row[48])."%</td><td>".(100*$row[49])."%</td><td>".(100*$row[50])."%</td><td>".(100*$row[51])."%</td></tr>";
        echo "<tr><td>".$row[52]."%</td><td>".(100*$row[53])."%</td><td>".(100*$row[54])."%</td><td>".(100*$row[55])."%</td><td>".(100*$row[56])."%</td></tr>";
        echo "<tr><td>".$row[57]."%</td><td>".(100*$row[58])."%</td><td>".(100*$row[59])."%</td><td>".(100*$row[60])."%</td><td>".(100*$row[61])."%</td></tr>";
    }
    echo "</table>";
    echo "</div>";
?>
</body>
</html>