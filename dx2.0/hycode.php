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
        if (!isset($code)){
            echo "无相应数据";
            exit;
        }
        if (!isset($date)){
            $ld = $hy->exe_sql_one("select date from iknow_data where code='".$code."' order by date desc limit 1");
            $date = $ld[0];
        }
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
$data = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_code&code=".$code."&date=".$date),true);
echo "<title>".$data[0][1]."(".$data[0][0].")--".$date."</title>";
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
<div id='table'>
<?php
function updn($exp){
    $cla = "up";
    if ($exp<0){
        $cla = "dn";
    }
    return $cla;
}
function echotable($data){
    echo "<table style=\"margin:0 auto;width:90%\" border=\"1\">";
    $base = $data[0];
    $ma = $data[1];
    $next = $data[2];
    $close = $base[4];
    $cla = updn($ma[0][0]-$close);
    echo "<tr><td width=\"80\">名字</td><td width=\"160\"><a href=\"hycode.php?code=".$base[0]."&date=".$date."\" target=\"_blank\">".$base[1]."(".$base[0].")--".$base[2]."</a></td><td width=\"80\">".$ma[0][1]."</td><td width=\"80\">".$ma[0][0]."</td><td width=\"80\" class=\"".$cla."\">".round(100*(($ma[0][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[1][0]-$close);
    echo "<tr><td>时间</td><td>".$base[3]."</td><td>".$ma[1][1]."</td><td>".$ma[1][0]."</td><td class=\"".$cla."\">".round(100*(($ma[1][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[2][0]-$close);
    $zdfcla = updn($base[5]);
    echo "<tr><td>涨跌幅</td><td class=\"".$zdfcla."\">".(100*$base[5])."%</td><td>".$ma[2][1]."</td><td>".$ma[2][0]."</td><td class=\"".$cla."\">".round(100*(($ma[2][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[3][0]-$close);
    echo "<tr><td>成交量</td><td>".$base[6]."/<span class=\"up\">".$base[7]."</span></td><td>".$ma[3][1]."</td><td>".$ma[3][0]."</td><td class=\"".$cla."\">".round(100*(($ma[3][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[4][0]-$close);
    echo "<tr><td>特征值</td><td>".$base[8]."(".$base[9].")</td><td>".$ma[4][1]."</td><td>".$ma[4][0]."</td><td class=\"".$cla."\">".round(100*(($ma[4][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[5][0]-$close);
    $claev = updn($base[10]-50);
    echo "<tr><td>收盘分</td><td class=\"".$claev."\">".$base[10]."</td><td>".$ma[5][1]."</td><td>".$ma[5][0]."</td><td class=\"".$cla."\">".round(100*(($ma[5][0]-$close)/$close),2)."%</td></tr>";
    $clamacd = updn($base[13]);
    $cla = updn($base[11]-$base[12]);
    echo "<tr><td>MACD</td><td class=\"".$clamacd."\">".round($base[13],4)."</td><td>KD</td><td>".round($base[11],2)."/".round($base[12],2)."</td><td class=\"".$cla."\">".round($base[11]-$base[12],2)."</td></tr>";
    $fvp = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_codefv&code=".$data[0][0]),true);
    echo "<tr><td>".$next[0][0]."%(".(100*$fvp["1"])."%)</td><td>".(100*$next[0][1])."%</td><td>".(100*$next[0][2])."%</td><td>".(100*$next[0][3])."%</td><td>".(100*$next[0][4])."%</td></tr>";
    echo "<tr><td>".$next[1][0]."%(".(100*$fvp["2"])."%)</td><td>".(100*$next[1][1])."%</td><td>".(100*$next[1][2])."%</td><td>".(100*$next[1][3])."%</td><td>".(100*$next[1][4])."%</td></tr>";
    echo "<tr><td>".$next[2][0]."%(".(100*$fvp["3"])."%)</td><td>".(100*$next[2][1])."%</td><td>".(100*$next[2][2])."%</td><td>".(100*$next[2][3])."%</td><td>".(100*$next[2][4])."%</td></tr>";
    echo "<tr><td>".$next[3][0]."%(".(100*$fvp["4"])."%)</td><td>".(100*$next[3][1])."%</td><td>".(100*$next[3][2])."%</td><td>".(100*$next[3][3])."%</td><td>".(100*$next[3][4])."%</td></tr>";
    echo "<tr><td>".$next[4][0]."%(".(100*$fvp["5"])."%)</td><td>".(100*$next[4][1])."%</td><td>".(100*$next[4][2])."%</td><td>".(100*$next[4][3])."%</td><td>".(100*$next[4][4])."%</td></tr>";
    echo "<tr><td>".$next[5][0]."%(".(100*$fvp["6"])."%)</td><td>".(100*$next[5][1])."%</td><td>".(100*$next[5][2])."%</td><td>".(100*$next[5][3])."%</td><td>".(100*$next[5][4])."%</td></tr>";
    echo "<tr><td>".$next[6][0]."%(".(100*$fvp["7"])."%)</td><td>".(100*$next[6][1])."%</td><td>".(100*$next[6][2])."%</td><td>".(100*$next[6][3])."%</td><td>".(100*$next[6][4])."%</td></tr>";
    echo "<tr><td>".$next[7][0]."%(".(100*$fvp["8"])."%)</td><td>".(100*$next[7][1])."%</td><td>".(100*$next[7][2])."%</td><td>".(100*$next[7][3])."%</td><td>".(100*$next[7][4])."%</td></tr>";
    echo "</table>";
}

function echort($data){
    echo "<table style=\"margin:0 auto;width:90%\" border=\"1\">";
    $base = $data[0];
    $ma = $data[1];
    $next = $data[2];
    $close = $base[15];
    $cla = updn($ma[0][0]-$close);
    echo "<tr><td width=\"80\">名字</td><td width=\"160\">".$base[2]."(".$base[0].")--".$base[3]."</td><td width=\"80\">".$ma[0][1]."</td><td width=\"80\">".$ma[0][0]."</td><td width=\"80\" class=\"".$cla."\">".round(100*(($ma[0][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[1][0]-$close);
    echo "<tr><td>时间</td><td>".$base[1]."</td><td>".$ma[1][1]."</td><td>".$ma[1][0]."</td><td class=\"".$cla."\">".round(100*(($ma[1][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[2][0]-$close);
    $zdfcla = updn($base[4]);
    echo "<tr><td>涨跌幅</td><td class=\"".$zdfcla."\">".$base[4]."%</td><td>".$ma[2][1]."</td><td>".$ma[2][0]."</td><td class=\"".$cla."\">".round(100*(($ma[2][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[3][0]-$close);
    echo "<tr><td>成交量</td><td>".$base[8]."/<span class=\"up\">".$base[9]."</span></td><td>".$ma[3][1]."</td><td>".$ma[3][0]."</td><td class=\"".$cla."\">".round(100*(($ma[3][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[4][0]-$close);
    echo "<tr><td>特征值</td><td>".$base[13]."(".$base[14].")</td><td>".$ma[4][1]."</td><td>".$ma[4][0]."</td><td class=\"".$cla."\">".round(100*(($ma[4][0]-$close)/$close),2)."%</td></tr>";
    $cla = updn($ma[5][0]-$close);
    $claev = updn($base[7]-50);
    echo "<tr><td>收盘分</td><td class=\"".$claev."\">".$base[7]."</td><td>".$ma[5][1]."</td><td>".$ma[5][0]."</td><td class=\"".$cla."\">".round(100*(($ma[5][0]-$close)/$close),2)."%</td></tr>";
    $clamacd = updn($base[12]);
    $cla = updn($base[10]-$base[11]);
    echo "<tr><td>MACD</td><td class=\"".$clamacd."\">".round($base[12],4)."</td><td>KD</td><td>".round($base[10],2)."/".round($base[11],2)."</td><td class=\"".$cla."\">".round($base[10]-$base[11],2)."</td></tr>";
    $claev = updn($base[16]);
    echo "<tr><td>收盘中位</td><td class=\"".$claev."\">".(100*$base[16])."%</td><td>突破</td><td>".$base[5]."</td><td>".$base[6]."</td></tr>";
    
    echo "<tr><td>".$next[0]."%</td><td>".(100*$next[1])."%</td><td>".(100*$next[2])."%</td><td>".(100*$next[3])."%</td><td>".(100*$next[4])."%</td></tr>";
    echo "<tr><td>".$next[5]."%</td><td>".(100*$next[6])."%</td><td>".(100*$next[7])."%</td><td>".(100*$next[8])."%</td><td>".(100*$next[9])."%</td></tr>";
    echo "<tr><td>".$next[10]."%</td><td>".(100*$next[11])."%</td><td>".(100*$next[12])."%</td><td>".(100*$next[13])."%</td><td>".(100*$next[14])."%</td></tr>";
    echo "<tr><td>".$next[15]."%</td><td>".(100*$next[16])."%</td><td>".(100*$next[17])."%</td><td>".(100*$next[18])."%</td><td>".(100*$next[19])."%</td></tr>";
    echo "<tr><td>".$next[20]."%</td><td>".(100*$next[21])."%</td><td>".(100*$next[22])."%</td><td>".(100*$next[23])."%</td><td>".(100*$next[24])."%</td></tr>";
    echo "<tr><td>".$next[25]."%</td><td>".(100*$next[26])."%</td><td>".(100*$next[27])."%</td><td>".(100*$next[28])."%</td><td>".(100*$next[29])."%</td></tr>";
    echo "<tr><td>".$next[30]."%</td><td>".(100*$next[31])."%</td><td>".(100*$next[32])."%</td><td>".(100*$next[33])."%</td><td>".(100*$next[34])."%</td></tr>";
    echo "<tr><td>".$next[35]."%</td><td>".(100*$next[36])."%</td><td>".(100*$next[37])."%</td><td>".(100*$next[38])."%</td><td>".(100*$next[39])."%</td></tr>";
    echo "</table>";
}
    
    $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"hycode.php?date=".$prev[0]."&code=".$code."\">prev</a></h2>";
    }
    echo "<h2>".$data[0][1]."(".$code.")--".$date."</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hycode.php?date=".$next[0]."&code=".$code."\">next</a></h2>";
    }
    echo "</div>";

    echotable($data);
    if (count($next)>0){
        $ndata = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_code&code=".$code."&date=".$next[0]),true);
        echotable($ndata);
    }
    else{
        $rtdata = json_decode(file_get_contents("http://0.0.0.0:1982/iknow?name=q_codert&code=".$code),true);
        echort($rtdata);
    }

?>
  </div>
</body>
</html>