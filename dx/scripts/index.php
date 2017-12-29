<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>冬夏科技</title>
</head>

<body>
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
    $db = mysqli_connect('localhost', 'root', '123456');
    $selected = mysqli_select_db($db, "hy");
?>

<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>

<form id="inquiry" name="inquiry" method="post" action="codex.php" target="_blank">
    <p><a href="bdindex.php" target="_blank">板块一览</a>
    <label for="code"><strong>快速查询</strong></label>
    <input type="text" name="code" id="code" size="20" maxlength="6"/>
    <label><input type="submit" name="Submit" value="GO" /></label></p>
</form>

<?php
    $data= exe_sql_batch($db,"select date,count,hbr,lbr,oscore,cscore from iknow_daily order by date desc limit 200");
    echo "<table border=\"1\" width=\"100%\"><tr>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">日期</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">交易品种数量</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">高点突破率(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">低点突破率(%)</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">开盘平均分</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">收盘平均分</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">平均涨跌幅</font></b></td>";
    echo "<td width=\"150\" align=\"center\"><b><font size=\"3\">操作建议</font></b></td>";
    echo "</tr>";
    foreach($data as $row){
        $dt = substr($row[0],0,4).substr($row[0],5,2).substr($row[0],8,2);
        echo "<tr><td align=\"center\"><a href=\"date.php?".$dt."\" target=\"_blank\">".$row[0]."</td>";
        echo "<td align=\"center\">".$row[1]."</td>";
        echo "<td align=\"center\">".$row[2]."</td>";
        echo "<td align=\"center\">".$row[3]."</td>";
        echo "<td align=\"center\">".$row[4]."</td>";
        echo "<td align=\"center\">".$row[5]."</td>";
        $zdev = exe_sql_one($db,"select avg(zdf) from iknow_data where date='".$row[0]."'");
        if (floatval($zdev[0])>0){
            echo "<td align=\"center\"><font color=\"#CC0000\">".sprintf("%.2f",$zdev[0])."</font></td>";
        }
        else{
            echo "<td align=\"center\"><font color=\"#006600\">".sprintf("%.2f",$zdev[0])."</font></td>";
        }
        echo "<td align=\"center\">";
        echo "<a href=\"oper.php?b&".$row[0]."\" target=\"_blank\">买入</a>,";
        echo "<a href=\"oper.php?s&".$row[0]."\" target=\"_blank\">卖出</a>,";
        echo "<a href=\"oper.php?o&".$row[0]."\" target=\"_blank\">持有/观望</a>";
        echo "</td>";
        echo "</tr>";
    }
    echo "</table>";
    mysqli_close($db);
?>

</body>

</html>
