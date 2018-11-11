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
$limt = 50;
if (isset($count)){
    $limt = intval($count);
    if ($limt<50){
        $limt = 50;
    }
}
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>KC</title>";
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
echo "<h2><a href=\"index.php\" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href=\"ikrt.php\" target=\"_blank\">关注</a>&nbsp;&nbsp;<a href=\"ikk.php\" target=\"_blank\">K线</a></h2>";
?>
<div id='main'>
   <canvas id="C1" width="1400" height="200">该浏览器不支持画布</canvas>
   <canvas id="C2" width="1400" height="200">该浏览器不支持画布</canvas>
   <canvas id="C3" width="1400" height="200">该浏览器不支持画布</canvas>
   <canvas id="C4" width="1400" height="200">该浏览器不支持画布</canvas>
   <canvas id="C5" width="1400" height="200">该浏览器不支持画布</canvas>
<?php
    $dic = array('C1'=>array(array(),array()),'C2'=>array(array(),array()),'C3'=>array(array(),array()),'C4'=>array(array(),array()),'C5'=>array(array(),array()));
    $dts = $hy->exe_sql_batch("select distinct date from iknow.ik_attr order by date desc limit ".$limt);
    $dts = array_reverse($dts);
    foreach($dts as $dt){
        $csrc1 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.2");
        $csrc2 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.4 and csrc>0.2");
        $csrc3 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.6 and csrc>0.4");
        $csrc4 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.8 and csrc>0.6");
        $csrc5 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc>0.8");
        $all = intval($csrc5[0])+intval($csrc4[0])+intval($csrc3[0])+intval($csrc2[0])+intval($csrc1[0]);
        $p1 = round(100*(floatval($csrc1[0])/$all),2);
        $p2 = round(100*(floatval($csrc2[0])/$all),2);
        $p3 = round(100*(floatval($csrc3[0])/$all),2);
        $p4 = round(100*(floatval($csrc4[0])/$all),2);
        $p5 = round(100*(floatval($csrc5[0])/$all),2);
        array_push($dic['C1'][0],substr($dt[0],-5));
        array_push($dic['C1'][1],$p1);
        array_push($dic['C2'][0],substr($dt[0],-5));
        array_push($dic['C2'][1],$p2);
        array_push($dic['C3'][0],substr($dt[0],-5));
        array_push($dic['C3'][1],$p3);
        array_push($dic['C4'][0],substr($dt[0],-5));
        array_push($dic['C4'][1],$p4);
        array_push($dic['C5'][0],substr($dt[0],-5));
        array_push($dic['C5'][1],$p5);
    }
?>
      </tbody>
    </table>
  </div>
</div>
</body>
<script type="text/javascript">
<?php
    echo "var kdic = new Array();\n";
    foreach($dic as $key=>$val){
        echo "var da = new Array();\n";
        echo "var ka = new Array();\n";
        for($i=0;$i<count($dic[$key][0]);$i++){
            echo "da.push('".$dic[$key][0][$i]."');";
            echo "ka.push(".$dic[$key][1][$i].");";
        }
        echo "var val = Array(da,ka);";
        echo "kdic['".$key."'] = val;";
    }
?>
var col = new Array();
col['C1'] = '#00FF00';
col['C2'] = '#00EE00';
col['C3'] = '#CDCD00';
col['C4'] = '#FF4500';
col['C5'] = '#FF0000';
for (var key in kdic) {
    var machart = echarts.init(document.getElementById(key));
    machart.setOption({
        title: {
            text: key,
            subtext: '收盘分布',
            x:'center'
        },
        xAxis: {
            type: 'category',
            boundaryGap: true,
            data: kdic[key][0]
        },
        yAxis: {
            type: 'value',
            name: '占比(%)'
        },
        toolbox: {
            show : true,
            feature : {
                mark : {show: true},
                saveAsImage : {show: true}
            }
        },
        series: [
            {
                "name": "C",
                "type": "bar",
                "barWidth" : 10,
                "data": kdic[key][1],
                itemStyle:{
                    normal:{
                        color:col[key]
                    }
                }
            }
        ]
    });
}
</script>
</html>