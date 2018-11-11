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
$limt = 45;
if (isset($count)){
    $limt = intval($count);
    if ($limt<50){
        $limt = 50;
    }
}
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>KP</title>";
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
tr{
    text-align:center;
}
td.sorted{
    background-color:#FFD000;
}
#pick{
    margin:20px;
    text-align:center;
}
#more{
    margin:20px;
}
#headbase{
    colspan:2
}
#headmore{
    colspan:6
}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<?php
echo "<h2><a href=\"index.php\" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href=\"ikrt.php\" target=\"_blank\">关注</a>&nbsp;&nbsp;<a href=\"ikc.php\" target=\"_blank\">收盘</a></h2>";
?>
<div id='main'>
   <canvas id="P1P2" width="1400" height="300">该浏览器不支持画布</canvas>
   <canvas id="P3P4" width="1400" height="300">该浏览器不支持画布</canvas>
   <canvas id="P5P6" width="1400" height="300">该浏览器不支持画布</canvas>
   <canvas id="P7P8" width="1400" height="300">该浏览器不支持画布</canvas>
<?php
    $dic = array(array(array(),array(),array()),array(array(),array(),array()),array(array(),array(),array()),array(array(),array(),array()));
    $dts = $hy->exe_sql_batch("select distinct date from iknow.ik_deri order by date desc limit ".$limt);
    $dts = array_reverse($dts);
    foreach($dts as $dt){
        $fvcnt1 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=1");
        $fvcnt2 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=2");
        $fvcnt3 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=3");
        $fvcnt4 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=4");
        $fvcnt5 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=5");
        $fvcnt6 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=6");
        $fvcnt7 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=7");
        $fvcnt8 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=8");
        $all = intval($fvcnt1[0])+intval($fvcnt2[0])+intval($fvcnt3[0])+intval($fvcnt4[0])+intval($fvcnt5[0])+intval($fvcnt6[0])+intval($fvcnt7[0])+intval($fvcnt8[0]);
        $p1 = round(100*(floatval($fvcnt1[0])/$all),2);
        $p2 = round(100*(floatval($fvcnt2[0])/$all),2);
        $p3 = round(100*(floatval($fvcnt3[0])/$all),2);
        $p4 = round(100*(floatval($fvcnt4[0])/$all),2);
        $p5 = round(100*(floatval($fvcnt5[0])/$all),2);
        $p6 = round(100*(floatval($fvcnt6[0])/$all),2);
        $p7 = round(100*(floatval($fvcnt7[0])/$all),2);
        $p8 = round(100*(floatval($fvcnt8[0])/$all),2);
        array_push($dic[0][0],substr($dt[0],-5));
        array_push($dic[0][1],$p1);
        array_push($dic[0][2],$p2);
        array_push($dic[1][0],substr($dt[0],-5));
        array_push($dic[1][1],$p3);
        array_push($dic[1][2],$p4);
        array_push($dic[2][0],substr($dt[0],-5));
        array_push($dic[2][1],$p5);
        array_push($dic[2][2],$p6);
        array_push($dic[3][0],substr($dt[0],-5));
        array_push($dic[3][1],$p7);
        array_push($dic[3][2],$p8);
    }
?>
      </tbody>
    </table>
  </div>
</div>
</body>
<script type="text/javascript">
<?php
    echo "var inx = [['P1','P2'],['P3','P4'],['P5','P6'],['P7','P8']];\n";
    $data = "var data = [";
    for($i=0;$i<4;$i++){
        $strdt = "[";
        foreach($dic[$i][0] as $dt){
            $strdt = $strdt."'".$dt."',";
        }
        $strdt = substr($strdt,0,-1);
        $strdt = $strdt."]";
        $strpf = "[";
        foreach($dic[$i][1] as $pf){
            $strpf = $strpf.$pf.",";
        }
        $strpf = substr($strpf,0,-1);
        $strpf = $strpf."]";
        $strps = "[";
        foreach($dic[$i][2] as $ps){
            $strps = $strps.$ps.",";
        }
        $strps = substr($strps,0,-1);
        $strps = $strps."]";
        $data = $data."[".$strdt.",".$strpf.",".$strps."],";
    }
    $data = substr($data,0,-1);
    echo $data."];\n";
?>
function draw(pf,ps,dts,pfs,pss){
    var machart = echarts.init(document.getElementById(pf+ps));
    machart.setOption({
        title: {
            text: pf+'-'+ps,
            subtext: 'K线分布',
            x:'center'
        },
        xAxis: {
            type: 'category',
            boundaryGap: true,
            data: dts
        },
        yAxis: {
            type: 'value',
            name: '占比(%)'
        },
        legend: {
            data:[pf,ps]
        },
        toolbox: {
            show : true,
            orient: 'vertical',
            x: 'right',
            y: 'center',
            feature : {
                mark : {show: true},
                dataView : {show: true, readOnly: false},
                restore : {show: true},
                saveAsImage : {show: true}
            }
        },
        series: [
            {
                name: pf,
                type: "bar",
                barWidth : 10,
                data: pfs,
                itemStyle:{
                    normal:{
                        color:'#FF0000'
                    }
                }
            },
            {
                name:ps,
                type:'bar',
                barWidth : 10,
                data: pss,
                itemStyle:{
                    normal:{
                        color:'#00FF00'
                    }
                }
            }
        ]
    });
}
draw(inx[0][0],inx[0][1],data[0][0],data[0][1],data[0][2]);
draw(inx[1][0],inx[1][1],data[1][0],data[1][1],data[1][2]);
draw(inx[2][0],inx[2][1],data[2][0],data[2][1],data[2][2]);
draw(inx[3][0],inx[3][1],data[3][0],data[3][1],data[3][2]);
</script>
</html>