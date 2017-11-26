<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>冬夏科技</title>
</head>

<body>
<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<?php
    require 'momlib.php';
    $momlib = new momlib();
    session_start();
    if (!isset($_SESSION['uid'])){
        header('Location: ' . "/mom/result.php?7");
        exit();
    }
    $qstr = $_SERVER["QUERY_STRING"];
    $pid = $qstr;
    $w = date("w");
    $h = date("H");
?>

<?php
    if ($w>=1 and $w<=5 and $h<15){
        echo "<form method=\"POST\" action=\"deal.php?1&".$pid."\">";
?>
        <p>代码<input type="text" name="CODE" size="20">&nbsp;数量<input type="text" name="AMOUNT" size="20">&nbsp;价格<input type="text" name="PRICE" size="20">&nbsp;<input type="submit" value="买入" name="B1"></p>
        </form>
<?php
        echo "<form method=\"POST\" action=\"deal.php?2&".$pid."\">";
?>
        <p>代码<input type="text" name="CODE" size="20">&nbsp;数量<input type="text" name="AMOUNT" size="20">&nbsp;价格<input type="text" name="PRICE" size="20">&nbsp;<input type="submit" value="卖出" name="B1"></p>
        </form>
<?php
    }
    $bsln = $momlib->exe_sql_one("select baseline from ikmom_project_v where pid='".$pid."'");
    $money = $momlib->exe_sql_one("select cash,freeze from ikmom_invest_account_v where pid='".$pid."'");
    $stock = $momlib->exe_sql_batch("select code,amount,freeze from ikmom_project_hold_v where pid='".$pid."'");
    $sdata = array();
    $allval = floatval($money[0])+floatval($money[1]);
    foreach($stock as $row){
        $all = floatval($row[1])+floatval($row[2]);
        $pri = $momlib->rtprice($row[0]);
        $val = $all*$pri;
        $allval = $allval + $val;
        array_push($sdata,array($row[0],$row[1],$row[2],$val));
    }
    $td = date('Y-m-d');
    $ods = $momlib->exe_sql_batch("select orderseq from ikmom_order_seq_v where pid='".$pid."' and date='".$td."'");
    $doneoders = array();
    foreach($ods as $od){
        $order = $momlib->exe_sql_one("select buysell,code,amount,price,status from ikmom_order_v where seqnum='".$od[0]."'");
        if ($order[4]=="1" or $order[4]=="2"){
            array_push($doneoders,array($order[0],$order[1],$order[2],$order[3],$order[4]));
        }
    }
    $orders = $momlib->exe_sql_batch("select buysell,code,amount,price,seqnum from ikmom_order_v where pid='".$pid."' and status=0");
    $odata = array();
    foreach($orders as $row){
        array_push($odata,array($row[0],$row[1],$row[2],$row[3],$row[4]));
    }
    $rate = ($allval-floatval($bsln[0]))/floatval($bsln[0]);
    echo "<table border=\"1\" width=\"50%\">";
    echo "<tr><td width=\"300\" colspan=\"2\"><p align=\"center\">".$pid."</td>";
    if ($rate>0){
         echo "<td width=\"150\"><p align=\"center\"><font color=\"#CC0000\">".sprintf("%.2f",100*$rate)."%</font></td>";
    }
    else{
         echo "<td width=\"150\"><p align=\"center\"><font color=\"#33CC33\">".sprintf("%.2f",100*$rate)."%</font></td>";
    }
    echo "<td width=\"150\"><p align=\"center\"><a href=\"deal.php?4&".$pid."\" target=\"_blank\">计提</td>";
    echo "</tr>";
    echo "<tr><td width=\"150\" rowspan=\"2\">总价值</td>";
    if ($rate>0){
        echo "<td width=\"150\" rowspan=\"2\"><font color=\"#CC0000\">".$allval."</font></td>";
    }
    else{
        echo "<td width=\"150\" rowspan=\"2\"><font color=\"#33CC33\">".$allval."</font></td>";
    }
    echo "<td width=\"150\">可用金额</td>";
    echo "<td width=\"150\">".$money[0]."</td>";
    echo "</tr>";
    echo "<tr>";
    echo "<td width=\"150\">冻结金额</td>";
    echo "<td width=\"150\">".$money[1]."</td>";
    echo "</tr>";
    echo "</table>";
    echo "<p></p>";
    echo "<p></p>";
    echo "<table border=\"1\" width=\"50%\">";
    if (count($sdata)>0){
        echo "<tr><td width=\"150\">代码</td>";
        echo "<td width=\"150\">可用数量</td>";
        echo "<td width=\"150\">冻结数量</td>";
        echo "<td width=\"150\">价格</td>";
        echo "<td width=\"150\">市值</td></tr>";
    }
    $all = 0;
    foreach($sdata as $row){
        $name = $momlib->exe_sql_one("select name from ikmom_name where code='".$row[0]."'");
        echo "<tr><td width=\"150\">".$name[0]."(".$row[0].")</td>";
        echo "<td width=\"150\">".$row[1]."</td>";
        echo "<td width=\"150\">".$row[2]."</td>";
        $p = $momlib->rtprice($row[0]);
        echo "<td width=\"150\">".$p."</td>";
        echo "<td width=\"150\">".$row[3]."</td></tr>";
        $all = $all + floatval($row[3]);
    }
    echo "<tr><td width=\"600\" colspan=\"4\"><p align=\"center\">合计</td>";
    echo "<td width=\"150\">".$all."</td></tr>";
    echo "</table>";
    echo "<p></p>";
    echo "<p></p>";
    echo "<table border=\"1\" width=\"50%\">";
    if (count($odata)>0){
        echo "<tr><td width=\"150\">股票代码</td>";
        echo "<td width=\"150\">数量</td>";
        echo "<td width=\"150\">价格</td>";
        echo "<td width=\"150\">操作</td></tr>";
    }
    foreach($odata as $row){
        $name = $momlib->exe_sql_one("select name from ikmom_name where code='".$row[1]."'");
        echo "<tr><td width=\"150\">".$name[0]."(".$row[1].")</td>";
        echo "<td width=\"150\">".$row[2]."</td>";
        echo "<td width=\"150\">".$row[3]."</td>";
        if ($row[0]=="0"){
            echo "<td width=\"150\"><a href=\"deal.php?3&".$row[4]."\" target=\"_blank\">买入撤单</td>";
        }
        elseif ($row[0]=="1"){
            echo "<td width=\"150\"><a href=\"deal.php?3&".$row[4]."\" target=\"_blank\">卖出撤单</td>";
        }
        echo "</tr>";
    }
    foreach($doneoders as $row){
        $name = $momlib->exe_sql_one("select name from ikmom_name where code='".$row[1]."'");
        echo "<tr><td width=\"150\">".$name[0]."(".$row[1].")</td>";
        echo "<td width=\"150\">".$row[2]."</td>";
        echo "<td width=\"150\">".$row[3]."</td>";
        if ($row[0]=="0"){
            if ($row[4]=="1"){
                echo "<td width=\"150\">买入已成</td>";
            }
            else{
                echo "<td width=\"150\">买入已撤</td>";
            }
        }
        elseif ($row[0]=="1"){
            if ($row[4]=="1"){
                echo "<td width=\"150\">卖出已成</td>";
            }
            else{
                echo "<td width=\"150\">卖出已撤</td>";
            }
        }
        echo "</tr>";
    }
    echo "</table>";
?>


</body>

</html>
