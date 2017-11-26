<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<?php
    
    function exe_sql_one($db,$sql){
        //echo $sql."\n";
        $a = array();
        $result = mysqli_query($db, $sql);
        if($ret=mysqli_fetch_row($result)){
            foreach($ret as $item){
                array_push($a,$item);
            }
        }
        return $a;
    }
        
    function exe_sql_batch($db,$sql){
        //echo $sql."\n";
        $a = array();
        $result = mysqli_query($db, $sql);
        while($ret=mysqli_fetch_row($result)){
            array_push($a,$ret);
        }
        return $a;
    }

    $qstr = $_SERVER["QUERY_STRING"];
    $its = explode("&",$qstr);
    if (count($its)==2){
        $op = $its[0];
        $day = $its[1];
    }
    if ($op=="b"){
        $o = "买入";
    }
    elseif($op=="s"){
        $o = "卖出";
    }
    else{
        $o = "持有/观望";
    }
    echo "<title>建议".$o."</title>";
    $db = mysqli_connect('localhost', 'root', '123456');
    $selected = mysqli_select_db($db, "hy");
?>

</head>

<body>
<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<?php
    $pd = exe_sql_one($db,"select date from ikbill_daily where date<'".$day."' order by date desc limit 1");
    $nd = exe_sql_one($db,"select date from ikbill_daily where date>'".$day."' order by date limit 1");
    echo "<h2 align=\"center\">";
    if (count($pd)>0){
        echo "<a href=\"oper.php?".$op."&".$pd[0]."\">前一日</a>&nbsp;".$o."(".$day.")&nbsp;";
    }
    if (count($nd)>0){
        echo "<a href=\"oper.php?".$op."&".$nd[0]."\">后一日</a>";
    }
    echo "</h2>";
    $oper = 0;
    if ($op=="b"){
        $oper = 1;
    }
    elseif ($op=="s"){
        $oper = 2;
    }
    $rows = exe_sql_batch($db,"select code,score,ranking,volyy from ikbill_after where date='".$day."' and code in (select code from ikbill_ops where date='".$day."' and ops=".$oper.") order by ranking");
    $days = exe_sql_batch($db,"select distinct date from ikbill_data where date>'".$day."' order by date desc limit 5");
    $n = count($days);
    echo "<div align=\"center\">";
    echo "<table border=\"1\" width=\"80%\">";
    echo "<tr>";
    echo "<td width=\"200\">序号</td>";
    echo "<td width=\"200\">代码</td>";
    echo "<td width=\"200\">名称</td>";
    echo "<td width=\"200\">行业</td>";
    echo "<td width=\"200\">得分</td>";
    echo "<td width=\"200\">成交排名</td>";
    echo "<td width=\"200\">成交额(亿元)</td>";
    echo "<td width=\"200\">T+".$n." 高点(%)</td>";
    echo "<td width=\"200\">T+".$n." 低点(%)</td>";
    echo "<td width=\"200\">T+".$n." 收盘(%)</td>";
    echo "</tr>";
    $seq = 1;
    foreach($rows as $row){
        
        $names = exe_sql_one($db,"select name,bdname,bdcode from ikbill_name where code='".$row[0]."'");
        //$scr = exe_sql_one($db,"select score,ranking,volyy from ikbill_after where code='".$row[0]."' and date='".$day."'");
        echo "<tr>";
        echo "<td><p align=\"center\">".$seq."</td>";
        $seq = $seq + 1;
        echo "<td><a href=\"codex.php?".$row[0]."\" target=\"_blank\">".$row[0]."</td>";
        echo "<td>".$names[0]."</td>";
        echo "<td><a href=\"board.php?".$names[2]."\" target=\"_blank\">".$names[1]."</td>";
        echo "<td>".sprintf("%.4f",$row[1])."</td>";
        echo "<td>".$row[2]."</td>";
        echo "<td>".$row[3]."</td>";
        if ($n>0){
            $cdays = exe_sql_batch($db,"select date from ikbill_ops where code='".$row[0]."' and date>'".$day."' order by date limit 5");
            if (count($cdays)>0){
                $ld = $cdays[count($cdays)-1][0];
                $tclose = exe_sql_one($db,"select close from ikbill_data where date='".$day."' and code='".$row[0]."'");
                $hl = exe_sql_one($db,"select max(high),min(low) from ikbill_data where date>'".$day."' and date<='".$ld."' and code='".$row[0]."'");
                $nclose = exe_sql_one($db,"select close from ikbill_data where date='".$ld."' and code='".$row[0]."'");
                $tc = floatval($tclose[0]);
                $high = (floatval($hl[0])-$tc)/($tc);
                $low = (floatval($hl[1])-$tc)/($tc);
                $nc = (floatval($nclose[0])-$tc)/($tc);
                if ($high>0){
                    echo "<td><font color=\"#CC0000\">".sprintf("%.2f",100*$high)."</font></td>";
                }
                else{
                    echo "<td><font color=\"#006600\">".sprintf("%.2f",100*$high)."</font></td>";
                }
                if ($low>0){
                    echo "<td><font color=\"#CC0000\">".sprintf("%.2f",100*$low)."</font></td>";
                }
                else{
                    echo "<td><font color=\"#006600\">".sprintf("%.2f",100*$low)."</font></td>";
                }
                if ($nc>0){
                    echo "<td><font color=\"#CC0000\">".sprintf("%.2f",100*$nc)."</font></td>";
                }
                else{
                    echo "<td><font color=\"#006600\">".sprintf("%.2f",100*$nc)."</font></td>";
                }
            }
            else{
                echo "<td>N/A</td>";
                echo "<td>N/A</td>";
                echo "<td>N/A</td>";
            }
        }
        else{
            echo "<td>N/A</td>";
            echo "<td>N/A</td>";
            echo "<td>N/A</td>";
        }
        echo "</tr>";
    }
    echo "</table>";
    echo "</div>";
    mysqli_close($db);
?>

</body>

</html>