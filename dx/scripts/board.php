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

    $bdcode = $_SERVER["QUERY_STRING"];
    $db = mysqli_connect('localhost', 'root', '123456');
    $selected = mysqli_select_db($db, "hy");
    $bdname = exe_sql_one($db,"select bdname from iknow_name where bdcode='".$bdcode."' limit 1");
    echo "<title>".$bdname[0]."</title>";
?>
</head>
<body>
    <h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<?php
    $cnt = exe_sql_one($db,"select count(*) from iknow_name where boardcode='".$bdcode."'");
    echo "<h2 align=\"center\">".$bdname[0]."(".$cnt[0].")</h2>";
    $data= exe_sql_batch($db,"select date,volwy,weight,hbr,lbr,score,zdlead,zdf,vollead,volyy from iknow_board where boardcode='".$bdcode."' order by date desc limit 60");
    
    echo "<table border=\"1\" width=\"100%\"><tr>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">日期</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">标记</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交额(亿元)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交占比(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">高点突破率(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">低点突破率(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">收盘平均分</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">领涨股票</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">涨跌幅(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交最大</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">成交额(亿元)</font></b></td>";
    echo "</tr>";
    foreach($data as $row){
        $zname = exe_sql_one($db,"select name from iknow_name where code='".$row[6]."'");
        $vname = exe_sql_one($db,"select name from iknow_name where code='".$row[8]."'");
        $dt = substr($row[0],0,4).substr($row[0],5,2).substr($row[0],8,2);
        $bt = exe_sql_one($db,"select bt from iknow_board where date='".$row[0]."' and boardcode='".$bdcode."'");
        echo "<tr>";
        echo "<td align=\"center\"><a href=\"boardx.php?".$bdcode."&".$row[0]."\" target=\"_blank\">".$row[0]."</a></td>";
        if (intval($bt[0])==3){
            echo "<td><font color=\"#CC0000\">上涨</font></td>";
        }
        elseif(intval($bt[0])==1){
            echo "<td><font color=\"#006600\">下跌</font></td>";
        }
        elseif(intval($bt[0])==2){
            echo "<td><font color=\"#FF9900\">反弹</font></td>";
        }
        else{
            echo "<td><font color=\"#99CC00\">回调</font></td>";
        }
        echo "<td align=\"center\">".sprintf("%.4f",floatval($row[1])/10000)."</td>";
        echo "<td align=\"center\">".$row[2]."</td>";
        echo "<td align=\"center\">".$row[3]."</td>";
        echo "<td align=\"center\">".$row[4]."</td>";
        echo "<td align=\"center\">".$row[5]."</td>";
        echo "<td align=\"center\"><a href=\"codex.php?".$row[6]."\" target=\"_blank\">".$zname[0]."(".$row[6].")</a></td>";
        if (floatval($row[7])>0){
            echo "<td align=\"center\"><font color=\"#CC0000\">".$row[7]."</font></td>";
        }
        else{
            echo "<td align=\"center\"><font color=\"#006600\">".$row[7]."</font></td>";
        }
        echo "<td align=\"center\"><a href=\"codex.php?".$row[8]."\" target=\"_blank\">".$vname[0]."(".$row[8].")</a></td>";
        echo "<td align=\"center\">".$row[9]."</td>";
        echo "</tr>";
    }
    echo "</table>";
    mysqli_close($db);
?>
</body>
</html>
