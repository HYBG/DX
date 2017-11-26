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
    $db = mysqli_connect('localhost', 'root', '123456');
    $selected = mysqli_select_db($db, "hy");
?>
<title>冬夏板块</title>
</head>

<body>

<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>

<h2 align="center">板块一览</h2>
<?php
    $bds = exe_sql_batch($db,"select distinct bdcode from ikbill_name order by bdcode");
    echo "<div align=\"center\">";
    echo "<table border=\"1\" width=\"80%\">";
    $colcnt = 6;
    $rowcnt = (count($bds)/$colcnt);
    $cnt = count($bds);
    for($i=0;$i<$rowcnt;$i++){
        echo "<tr>";
        for($j=0;$j<$colcnt;$j++){
            $inx = $i*$colcnt+$j;
            if ($inx>=$cnt){
                echo "<td width=\"200\">N/A</td>";
            }
            else{
                $bname = exe_sql_one($db,"select bdname from ikbill_name where bdcode='".$bds[$inx][0]."' limit 1");
                $ccnt = exe_sql_one($db,"select count(*) from ikbill_name where bdcode='".$bds[$inx][0]."'");
                echo "<td width=\"200\"><a href=\"board.php?".$bds[$inx][0]."\" target=\"_blank\">".$bname[0]."(".$ccnt[0].")</a></td>";
            }
        }
        echo "</tr>";
    }
    echo "</table>";
    echo "</div>";
?>
</body>

</html>