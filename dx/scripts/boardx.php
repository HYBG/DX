<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
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

    $infs = explode("&",$_SERVER["QUERY_STRING"]);
    if (count($infs)==2){
        $bdcode = $infs[0];
        $day = $infs[1];
    }
    $db = mysqli_connect('localhost', 'root', '123456');
    $selected = mysqli_select_db($db, "hy");
    $bdname = exe_sql_one($db,"select bdname from iknow_name where boardcode='".$bdcode."' limit 1");
    echo "<title>".$bdname[0]."</title>";
?>
</head>
<body>
    <h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<?php
    $pd = exe_sql_one($db,"select date from iknow_daily where date<'".$day."' order by date desc limit 1");
    $nd = exe_sql_one($db,"select date from iknow_daily where date>'".$day."' order by date limit 1");
    $bt = exe_sql_one($db,"select bt from iknow_board where date='".$day."' and boardcode='".$bdcode."'");
    $bta = array("1"=>"下跌","2"=>"反弹","3"=>"上涨","4"=>"回调");
    echo "<h2 align=\"center\">";
    if (count($pd)>0){
        echo "<a href=\"boardx.php?".$bdcode."&".$pd[0]."\">前一日</a>&nbsp;".$bdname[0]."(".$day.")--".$bta[$bt[0]]."&nbsp;";
    }
    if (count($nd)>0){
        echo "<a href=\"boardx.php?".$bdcode."&".$nd[0]."\">后一日</a>";
    }
    echo "</h2>";
    $data= exe_sql_batch($db,"select code,ranking,volyy from iknow_after where date='".$day."' and code in (select code from iknow_name where boardcode='".$bdcode."') order by ranking");
    $days = exe_sql_batch($db,"select distinct date from iknow_data where date>'".$day."' order by date desc limit 5");
    $n = count($days);
    echo "<table border=\"1\" width=\"100%\"><tr>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">代码</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">名称</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">得分</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">标记</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">操作</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交排名</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交额(亿元)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">收盘价</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">涨跌幅(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">振幅(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">换手率(%)</font></b></td>";
    echo "<td width=\"150\">T+".$n." 高点(%)</td>";
    echo "<td width=\"150\">T+".$n." 低点(%)</td>";
    echo "<td width=\"150\">T+".$n." 收盘(%)</td>";
    echo "</tr>";
    foreach($data as $row){
        $name = exe_sql_one($db,"select name from iknow_name where code='".$row[0]."'");
        $scr = exe_sql_one($db,"select score from iknow_after where code='".$row[0]."' and date='".$day."'");
        $binf = exe_sql_one($db,"select close,zdf,zf,hs from iknow_data where code='".$row[0]."' and date='".$day."'");
        $mt = exe_sql_one($db,"select mt from iknow_attr where code='".$row[0]."' and date='".$day."'");
        echo "<tr>";
        echo "<td><a href=\"codex.php?".$row[0]."\" target=\"_blank\">".$row[0]."</td>";
        echo "<td>".$name[0]."</td>";
        echo "<td>".sprintf("%.4f",$scr[0])."</td>";
        if (intval($mt[0])==3){
            echo "<td><font color=\"#CC0000\">上涨</font></td>";
        }
        elseif(intval($mt[0])==1){
            echo "<td><font color=\"#006600\">下跌</font></td>";
        }
        elseif(intval($mt[0])==2){
            echo "<td><font color=\"#FF9900\">反弹</font></td>";
        }
        else{
            echo "<td><font color=\"#99CC00\">回调</font></td>";
        }
        $op = exe_sql_one($db,"select ops from iknow_ops where code='".$row[0]."' and date='".$day."'");
        if (intval($op[0])==1){
            echo "<td><font color=\"#CC0000\">准备买入</font></td>";
        }
        elseif(intval($op[0])==2){
            echo "<td><font color=\"#006600\">准备卖出</font></td>";
        }
        else{
            echo "<td><font color=\"#0000FF\">观望/持有</font></td>";
        }
        echo "<td>".$row[1]."</td>";
        echo "<td>".$row[2]."</td>";
        echo "<td>".$binf[0]."</td>";
        if (floatval($binf[1])>0){
            echo "<td><font color=\"#CC0000\">".$binf[1]."</font></td>";
        }
        else{
            echo "<td><font color=\"#006600\">".$binf[1]."</font></td>";
        }
        echo "<td>".$binf[2]."</td>";
        echo "<td>".$binf[3]."</td>";
        if ($n>0){
            $cdays = exe_sql_batch($db,"select date from iknow_after where code='".$row[0]."' and date>'".$day."' order by date limit 5");
            if (count($cdays)>0){
                $ld = $cdays[count($cdays)-1][0];
                $tclose = exe_sql_one($db,"select close from iknow_data where date='".$day."' and code='".$row[0]."'");
                $hl = exe_sql_one($db,"select max(high),min(low) from iknow_data where date>'".$day."' and date<='".$ld."' and code='".$row[0]."'");
                $nclose = exe_sql_one($db,"select close from iknow_data where date='".$ld."' and code='".$row[0]."'");
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
    mysqli_close($db);
?>
</body>
</html>
