<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/hy.js"></script>
<script src="./js/echarts.min.js"></script>
<?php
require "../phplib/hylib.php";
$hy = new hylib('root','123456');
#$hy->setmode("debug");
$code = $_POST['code'];
if (!isset($code)){
    parse_str($_SERVER["QUERY_STRING"]);
}
if (!isset($code)){
    echo "无相应数据";
}
elseif ($hy->isok()){
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
<table style="margin:auto" width="1200" height="300" border="1">
<?php
    $data = $hy->exe_sql_one("select date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from iknow.ik_next where code='".$code."' order by date desc limit 1");
    $vol5 = $hy->exe_sql_batch("select vol5 from ik_attr where code='".$code."' and date<='".$data[0]."' order by date desc limit 2");
    $mas = $hy->exe_sql_one("select ik_data.close,ik_data.volwy,ik_attr.zdf,ik_attr.csrc,ik_attr.ma5,ik_attr.ma10,ik_attr.mid,ik_attr.ma30,ik_attr.ma60 from ik_data,ik_attr where ik_data.code='".$code."' and ik_data.date='".$data[0]."' and ik_attr.code='".$code."' and ik_attr.date='".$data[0]."'");
    $names = $hy->exe_sql_one("select name,industry from ik_rt where code='".$code."'");
    $vr = round(floatval($mas[1])/(floatval($vol5[1][0])/5.0),2);
    echo '<tr><th width="200" height="40">名称</th><th id="name" width="200" height="40">'.$names[0].'('.$code.')</th>';
    echo '<th rowspan="8"><canvas id="ma" width="300" height="300">该浏览器不支持画布</canvas></th><th rowspan="8"><canvas id="fv" width="300" height="300">该浏览器不支持画布</canvas></th></tr>';
    echo '<tr><th>板块</th><th id="industry">'.$names[1].'</th></tr>';
    echo '<tr><th>时间</th><th id="date">'.$data[0].'</th></tr>';
    $cla = 'green';
    if (floatval($mas[2])>0){
        $cla = 'red';
    }
    echo '<tr><th>涨跌幅(%)</th><th id="zdf" class="'.$cla.'">'.(100*(floatval($mas[2]))).'</th></tr>';
    echo '<tr><th>成交量(万元)</th><th id="volwy">'.$mas[1].'</th></tr>';
    $cla = 'green';
    if ($vr>1){
        $cla = 'red';
    }
    echo '<tr><th>量比</th><th id="vr" class="'.$cla.'">'.$vr.'</th></tr>';
    echo '<tr><th>收盘分</th><th id="csrc">'.(100*floatval($mas[3])).'</th></tr>';
    echo '<tr><th>特征值</th><th id="feature">'.$data[1].'('.$data[2].')</th></tr>';
?>
</table>
<table style="margin:auto" width="1200" height="300" border="1">
<?php
    $rtdata = $hy->exe_sql_one("select code,name,industry,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from iknow.ik_rt where code='".$code."'");

    echo '<tr><th width="200" height="40">名称</th><th id="name" width="200" height="40">'.$rtdata[1].'('.$code.')</th>';
    echo '<th rowspan="8"><canvas id="mart" width="300" height="300">该浏览器不支持画布</canvas></th><th rowspan="8"><canvas id="fvrt" width="300" height="300">该浏览器不支持画布</canvas></th></tr>';
    echo '<tr><th>板块</th><th id="industry">'.$rtdata[2].'</th></tr>';
    echo '<tr><th>时间</th><th id="date">'.$rtdata[3].' '.$rtdata[4].'</th></tr>';
    $cla = 'green';
    if (floatval($rtdata[5])>0){
        $cla = 'red';
    }
    echo '<tr><th>涨跌幅(%)</th><th id="zdf" class="'.$cla.'">'.$rtdata[5].'</th></tr>';
    echo '<tr><th>成交量(万元)</th><th id="volwy">'.round(floatval($rtdata[7]),2).'</th></tr>';
    $cla = 'green';
    if (floatval($rtdata[8]>1)){
        $cla = 'red';
    }
    echo '<tr><th>量比</th><th id="vr" class="'.$cla.'">'.$rtdata[8].'</th></tr>';
    echo '<tr><th>收盘分</th><th id="csrc">'.floatval($rtdata[6]).'</th></tr>';
    echo '<tr><th>特征值</th><th id="feature">'.$rtdata[15].'('.$rtdata[16].')</th></tr>';
?>
</table>
</div>
</div>
</body>
<script type="text/javascript">
<?php
    echo 'var hd = "'.$names[0].'('.$data[0].')";';
    echo "var mas = new Array(".$mas[8].",".$mas[7].",".$mas[6].",".$mas[5].",".$mas[4].",".$mas[0].");\n";
    echo "var fvs = [{value:".$data[3].",name:'上阳'},{value:".$data[4].",name:'上阴'},{value:".$data[5].",name:'下阳'},{value:".$data[6].",name:'下阴'},{value:".$data[7].",name:'双阳'},{value:".$data[8].",name:'双阴'},{value:".$data[9].",name:'内阳'},{value:".$data[10].",name:'内阴'}];\n";

    echo 'var hdrt = "'.$rtdata[1].'('.$rtdata[3].' '.$rtdata[4].')";';
    echo "var masrt = new Array(".$rtdata[14].",".$rtdata[13].",".$rtdata[12].",".$rtdata[11].",".$rtdata[10].",".$rtdata[9].");\n";
    echo "var fvsrt = [{value:".$rtdata[17].",name:'上阳'},{value:".$rtdata[18].",name:'上阴'},{value:".$rtdata[19].",name:'下阳'},{value:".$rtdata[20].",name:'下阴'},{value:".$rtdata[21].",name:'双阳'},{value:".$rtdata[22].",name:'双阴'},{value:".$rtdata[23].",name:'内阳'},{value:".$rtdata[24].",name:'内阴'}];\n";
?>
var machart = echarts.init(document.getElementById("ma"));
var fvchart = echarts.init(document.getElementById("fv"));
var length = Math.max.apply(Math,mas)-Math.min.apply(Math,mas);
var up = Math.round(100*(Math.max.apply(Math,mas)+0.1*length))/100;
var dn = Math.round(100*(Math.min.apply(Math,mas)-0.1*length))/100;

machart.setOption({
    title: {
        text: hd,
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
    legend: {
        top: '10',
        bottom: '10'
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
var option = {
    title : {
        text: hd,
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

var machart = echarts.init(document.getElementById("mart"));
var fvchart = echarts.init(document.getElementById("fvrt"));
var length = Math.max.apply(Math,masrt)-Math.min.apply(Math,masrt);
var up = Math.round(100*(Math.max.apply(Math,masrt)+0.1*length))/100;
var dn = Math.round(100*(Math.min.apply(Math,masrt)-0.1*length))/100;
machart.setOption({
     title: {
         text: hdrt,
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
    legend: {
        top: '10',
        bottom: '10'
    },
    toolbox: {
        show : true,
        feature : {
            mark : {show: true},
            saveAsImage : {show: true}
        }
    },
    series: [{
        data: masrt,
        type: 'line',
        areaStyle: {},
        label : {
            show: true
        }
    }]
});
var option = {
    title : {
        text: hdrt,
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
            data:fvsrt
        }
    ]
};
fvchart.setOption(option);
</script>
</html>