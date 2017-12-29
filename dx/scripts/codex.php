<html>

<head>
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
    $code = $_POST['code'];
    if (!isset($code)){
        $code = $_SERVER["QUERY_STRING"];
    }
?>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<?php
    $name = exe_sql_one($db,"select name from iknow_name where code='".$code."'");
    echo "<title>".$name[0]."</title>";
?>
</head>


<body>
<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<iframe style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="https://rcm-cn.amazon-adsystem.com/e/cm?ref=tf_til&t=lightnightfig-23&m=amazon&o=28&p=8&l=as1&IS1=1&asins=B00ZTRXFBA&linkId=2676ffef42b962afafc7ac70b2564900&bc1=FFFFFF&lt1=_top&fc1=333333&lc1=0066C0&bg1=FFFFFF&f=ifr">
</iframe>
<?php
    $data = exe_sql_batch($db,"select date,ops,crn,hrn,lrn,ev,std from iknow_ops where code='".$code."' order by date desc");
    $nb = exe_sql_one($db,"select name,boardcode,boardname from iknow_name where code='".$code."'");

    echo "<h2 align=\"center\">".$nb[0]."(".$code.") <a href=\"board.php?".$nb[1]."\">".$nb[2]."</a></h2>";
    echo "<div align=\"center\">";
    echo "<table border=\"1\" width=\"100%\">";
    echo "<tr>";
    echo "<td width=\"120\"><p align=\"center\">日期</td>";
    echo "<td width=\"120\"><p align=\"center\">操作</td>";
    echo "<td width=\"120\"><p align=\"center\">得分</td>";
    echo "<td width=\"120\"><p align=\"center\">收盘</td>";
    echo "<td width=\"120\"><p align=\"center\">涨跌幅(%s)</td>";
    echo "<td width=\"120\"><p align=\"center\">成交量(亿元)</td>";
    echo "<td width=\"120\"><p align=\"center\">成交排名</td>";
    echo "<td width=\"120\"><p align=\"center\">振幅(%)</td>";
    echo "<td width=\"120\"><p align=\"center\">换手率(%)</td>";
    echo "<td width=\"120\"><p align=\"center\">止损</td>";
    echo "<td width=\"120\" colspan=\"3\"><p align=\"center\">当日价格区间</td>";
    echo "<td width=\"120\" colspan=\"3\"><p align=\"center\">推测(T+1)</td>";
    echo "</tr>";
    for($i=0;$i<count($data);$i++){
        $aft = exe_sql_one($db,"select score,ranking,volyy,crn,hrn,lrn from iknow_after where code='".$code."' and date='".$data[$i][0]."'");
        $ps = exe_sql_one($db,"select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from iknow_tell where code='".$code."' and date='".$data[$i][0]."'");
        $base = exe_sql_one($db,"select close,zdf,zf,hs,high,low from iknow_data where code='".$code."' and date='".$data[$i][0]."'");
        $up = floatval($base[0])*(1+(floatval($data[$i][5])+floatval($data[$i][6]))/100);
        $md = floatval($base[0])*(1+(floatval($data[$i][5])/100));
        $dn = floatval($base[0])*(1+(floatval($data[$i][5])-floatval($data[$i][6]))/100);
        $lose = floatval($base[0])*(1+(floatval($ps[4])-floatval($ps[5]))/100);
        $tev = (floatval($base[0])+floatval($base[4])+floatval($base[5]))/3.0;
        echo "<tr>";
        echo "<td rowspan=\"3\"><p align=\"center\">".$data[$i][0]."</td>";
        if (intval($data[$i][1])==1){
            echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\"><font color=\"#CC0000\">准备买入</font></td>";
        }
        elseif(intval($data[$i][1])==2){
            echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\"><font color=\"#006600\">准备卖出</font></td>";
        }
        else{
            echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\"><font color=\"#0000FF\">持有/观望</font></td>";
        }
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".sprintf("%.4f",$aft[0])."</td>";
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".$base[0]."</td>";
        if (floatval($base[1])>0){
            echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\"><font color=\"#CC0000\">".$base[1]."</font></td>";
        }
        else{
            echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\"><font color=\"#006600\">".$base[1]."</font></td>";
        }
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".$aft[2]."</td>";
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".$aft[1]."</td>";
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".$base[2]."</td>";
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".$base[3]."</td>";
        echo "<td rowspan=\"3\" width=\"120\"><p align=\"center\">".sprintf("%.2f",$lose)."</td>";
        echo "<td width=\"60\">".$data[$i][2]."</td>";
        echo "<td width=\"60\">".$aft[3]."</td>";
        echo "<td width=\"60\">".$base[4]."</td>";
        echo "<td width=\"60\">".sprintf("%.2f",$up)."</td>";
        echo "<td width=\"60\">".$ps[0]."</td>";
        echo "<td width=\"60\">".$ps[1]."</td>";
        echo "</tr><tr>";
        echo "<td width=\"60\">".$data[$i][3]."</td>";
        echo "<td width=\"60\">".$aft[4]."</td>";
        echo "<td width=\"60\">".sprintf("%.2f",$tev)."</td>";
        echo "<td width=\"60\">".sprintf("%.2f",$md)."</td>";
        echo "<td width=\"60\">".$ps[2]."</td>";
        echo "<td width=\"60\">".$ps[3]."</td>";
        echo "</tr><tr>";
        echo "<td width=\"60\">".$data[$i][4]."</td>";
        echo "<td width=\"60\">".$aft[5]."</td>";
        echo "<td width=\"60\">".$base[5]."</td>";
        echo "<td width=\"60\">".sprintf("%.2f",$dn)."</td>";
        echo "<td width=\"60\">".$ps[4]."</td>";
        echo "<td width=\"60\">".$ps[5]."</td>";
        echo "</tr>";
    }
    echo "</table>";
    echo "</div>";
    mysqli_close($db);
?>

</body>

</html>