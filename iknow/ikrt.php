<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<script src="./js/echarts.min.js"></script>
<?php
require "../phplib/hylib.php";
$limt = 0;
if (isset($count)){
    $limt = intval($count);
}
$hy = new hylib('root','123456');
#$hy->setmode("debug");
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>HY RT</title>";
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
#header{
    text-shadow:10px 10px 10px #FF8C00;
    color:#FF4500;
    padding:20px;
    text-align:center;
    font-size:400%;
}
.red {
    color:#CD0000;
}
.green{
    color:#00CD00;
}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div><h1 id="header">汉尧科技</h1></div>
<div id="home"><p style="margin-left:200px"><a href="index.php" target=\"_blank\">Home</a></p></div>
<div id='table'>
<table style="margin-left:50px;margin:auto" width="1200" height="300" border="1">
<?php
    $masd = array();
    $fvsd = array();
    if ($limt == 0){
        $data = $hy->exe_sql_batch("select code,name,industry,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from iknow.ik_rt where rtwatch=1 order by fv4p1 desc");
    }
    else{
        $data = $hy->exe_sql_batch("select code,name,industry,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from iknow.ik_rt where rtwatch=1 order by fv4p1 desc limit ".$limt);
    }
    foreach($data as $row){
        if (floatval($row[9])==0){
            continue;
        }
        echo '<tr><th width="200" height="40">名称</th><th id="name" width="200" height="40"><a href="ikitem.php?code='.$row[0].'" target="_blank">'.$row[1].'('.$row[0].')</a></th>';
        echo '<th rowspan="8"><canvas id="ma'.$row[0].'" width="300" height="300">该浏览器不支持画布</canvas></th><th rowspan="8"><canvas id="fv'.$row[0].'" width="300" height="300">该浏览器不支持画布</canvas></th></tr>';
        echo '<tr><th>板块</th><th id="industry">'.$row[2].'</th></tr>';
        echo '<tr><th>时间</th><th id="date">'.$row[3].' '.$row[4].'</th></tr>';
        $cla = 'green';
        if (floatval($row[5])>0){
            $cla = 'red';
        }
        echo '<tr><th>涨跌幅(%)</th><th id="zdf" class="'.$cla.'">'.floatval($row[5]).'</th></tr>';
        echo '<tr><th>成交量(万元)</th><th id="volwy">'.round(floatval($row[7]),2).'</th></tr>';
        $cla = 'green';
        if (floatval($row[8])>1){
            $cla = 'red';
        }
        echo '<tr><th>量比</th><th id="vr" class="'.$cla.'">'.$row[8].'</th></tr>';
        $cla = 'green';
        if ($row[6]>'50'){
            $cla = 'red';
        }
        echo '<tr><th>收盘分</th><th id="csrc" class="'.$cla.'">'.$row[6].'</th></tr>';
        echo '<tr><th>特征值</th><th id="feature">'.$row[15].'('.$row[16].')</th></tr>';
        $sub = $row[1].'('.$row[3].' '.$row[4].')';
        $masd['ma'.$row[0]] = array($sub,array($row[14],$row[13],$row[12],$row[11],$row[10],$row[9]));
        $fvsd['fv'.$row[0]] = array($sub,array($row[17],$row[18],$row[19],$row[20],$row[21],$row[22],$row[23],$row[24]));
    }
?>
</table>
</div>
</div>
</body>
<script type="text/javascript">
<?php
    echo "var masdic = new Array();\n";
    echo "var fvsdic = new Array();\n";
    foreach($masd as $key=>$val){
        echo 'masdic["'.$key.'"] = ["'.$val[0].'",['.$val[1][0].','.$val[1][1].','.$val[1][2].','.$val[1][3].','.$val[1][4].','.$val[1][5].']];';
    }
    foreach($fvsd as $key=>$val){
        echo 'fvsdic["'.$key.'"] = ["'.$val[0].'",[{value:'.$val[1][0].',name:"上阳"},{value:'.$val[1][1].',name:"上阴"},{value:'.$val[1][2].',name:"下阳"},{value:'.$val[1][3].',name:"下阴"},{value:'.$val[1][4].',name:"双阳"},{value:'.$val[1][5].',name:"双阴"},{value:'.$val[1][6].',name:"内阳"},{value:'.$val[1][7].',name:"内阴"}]];';
    }
?>
for (var key in masdic) {
    var machart = echarts.init(document.getElementById(key));
    var mas = masdic[key][1];
    var length = Math.max.apply(Math,mas)-Math.min.apply(Math,mas);
    var up = Math.round(100*(Math.max.apply(Math,mas)+0.1*length))/100;
    var dn = Math.round(100*(Math.min.apply(Math,mas)-0.1*length))/100;
    machart.setOption({
        title: {
            text: masdic[key][0],
            subtext: '均线排列',
            x:'center'
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: ['MA60', 'MA30', 'MA20', 'MA10', 'MA5', 'close']
        },
        yAxis: {
            min: dn,
            max: up,
            type: 'value'
        },
        toolbox: {
            show : true,
            feature : {
                mark : {show: true},
                saveAsImage : {show: true}
            }
        },
        series: [{
            data: mas,
            type: 'line',
            areaStyle: {},
            label : {
                show: true
            }
        }]
    });
}
for (var key in fvsdic) {
    var fvchart = echarts.init(document.getElementById(key));
    var fvs = fvsdic[key][1];
    var option = {
        title : {
            text: fvsdic[key][0],
            subtext: 'T+1形态概率',
            x:'center'
        },
        tooltip : {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c}"
        },
        legend: {
            orient : 'vertical',
            x : 'left',
            y : 'bottom',
            data:['上阳','上阴','下阳','下阴','双阳','双阴','内阳','内阴']
        },
        toolbox: {
            show : true,
            feature : {
                mark : {show: true},
                saveAsImage : {show: true}
            }
        },
        calculable : true,
        series : [
            {
                name:'prob',
                type:'pie',
                radius : '50%',//饼图的半径大小
                center: ['60%', '60%'],//饼图的位置
                label: {
                    normal: {
                        show: true,
                        formatter: '{d}%' //自定义显示格式(b:name, c:value, d:百分比)
                    }
                },
                data:fvs
            }
        ]
    };
    fvchart.setOption(option);
}


</script>
</html>