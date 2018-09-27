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
.item {
    width: 200;
    height: 40;
}
.itemv{
    
}
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div><h1 id="header">汉尧科技</h1></div>
<div id="home"><a href="index.php" target=\"_blank\">Home</a></div>
<div id='table'>
<table width="1000" height="400" border="1">
  <tr>
    <th class="item">名称</th>
    <th class="item" id="name">&nbsp;</th>
    <th width="275" rowspan="6"><canvas id="fv" width="400" height="400">该浏览器不支持画布</canvas></th>
    <th width="227" rowspan="6"><canvas id="kfv" width="400" height="400">该浏览器不支持画布</canvas></th>
  </tr>
  <tr>
    <th class="item">板块</th>
    <th class="item" id="industry"></th>
  </tr>
  <tr>
    <th class="item">日期</th>
    <th class="item" id="date">&nbsp;</th>
  </tr>
  <tr>
    <th class="item">涨跌幅(%)</th>
    <th class="itemv" id="zdf">&nbsp;</th>
  </tr>
  <tr>
    <th class="item">成交量(万元)</th>
    <th class="item" id="volwy">&nbsp;</th>
  </tr>
  <tr>
    <th class="item">量比</th>
    <th class="itemv" id="vr">&nbsp;</th>
  </tr>
  
  <tr>
    <td height="208" colspan="2"><canvas id="ma" width="600" height="400">该浏览器不支持画布</canvas></td>
    <td><canvas id="bfv" width="400" height="400">该浏览器不支持画布</canvas></td>
    <td><canvas id="mfv" width="400" height="400">该浏览器不支持画布</canvas></td>
  </tr>
</table>
</div>
</div>
</body>
<script type="text/javascript">
<?php
    $data = $hy->exe_sql_one("select date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8,kfv2,kfv2cnt,kfv2p1,kfv2p2,kfv2p3,kfv2p4,kfv2p5,kfv2p6,kfv2p7,kfv2p8,bfv2,bfv2cnt,bfv2p1,bfv2p2,bfv2p3,bfv2p4,bfv2p5,bfv2p6,bfv2p7,bfv2p8,mfv2,mfv2cnt,mfv2p1,mfv2p2,mfv2p3,mfv2p4,mfv2p5,mfv2p6,mfv2p7,mfv2p8 from iknow.ik_next where code='".$code."' order by date desc limit 1");
    $vol5 = $hy->exe_sql_batch("select vol5 from ik_attr where code='".$code."' and date<='".$data[0]."' order by date desc limit 2");
    $mas = $hy->exe_sql_one("select ik_data.close,ik_data.volwy,ik_attr.zdf,ik_attr.ma5,ik_attr.ma10,ik_attr.mid,ik_attr.ma30,ik_attr.ma60 from ik_data,ik_attr where ik_data.code='".$code."' and ik_data.date='".$data[0]."' and ik_attr.code='".$code."' and ik_attr.date='".$data[0]."'");
    $names = $hy->exe_sql_one("select name,industry from ik_rt where code='".$code."'");
    $vr = round(floatval($mas[1])/(floatval($vol5[1][0])/5.0),2);
    echo "var name = '".$names[0]."(".$code.")';\n";
    echo "var industry = '".$names[1]."';\n";
    echo "var date = '".$data[0]."';\n";
    echo "var zdf = ".(100*(floatval($mas[2]))).";\n";
    echo "var vr = ".$vr.";\n";
    echo "var volwy = ".$mas[1].";\n";
    echo "var mas = new Array(".$mas[7].",".$mas[6].",".$mas[5].",".$mas[4].",".$mas[3].",".$mas[0].");\n"
?>
var machart = echarts.init(document.getElementById("ma"));
var fvchart = echarts.init(document.getElementById("fv"));
var kfvchart = echarts.init(document.getElementById("kfv"));
var bfvchart = echarts.init(document.getElementById("bfv"));
var mfvchart = echarts.init(document.getElementById("mfv"));
document.getElementById('name').innerHTML = name;
document.getElementById('industry').innerHTML = industry;
document.getElementById('date').innerHTML = date;
var zdfnode = document.getElementById('zdf');
zdfnode.innerHTML = String(zdf)+"%";
if (zdf>0){
    zdfnode.style.color = 'red';
}else{
    zdfnode.style.color = 'green';
}
document.getElementById('volwy').innerHTML = volwy;
var vrnode = document.getElementById('vr');
vrnode.innerHTML = vr;
if (vr>1){
    vrnode.style.color = 'red';
}else{
    vrnode.style.color = 'green';
}
var up = Math.ceil(Math.max.apply(Math,mas));
var dn = Math.floor(Math.min.apply(Math,mas));
machart.setOption({
     title: {
         text: 'MA',
         left: 'center',
         top: 20,
         textStyle: {
             color: '#ccc'
         }
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
    series: [{
        data: mas,
        type: 'line',
        areaStyle: {}
    }]
});
fvchart.setOption({
    backgroundColor: 'white',
    title: {
        text: 'FV prob',
        left: 'center',
        top: 20,
        textStyle: {
            color: '#ccc'
        }
    },
    tooltip : {
        trigger: 'item',
        formatter: "{a} <br/>{b} : {d}%"
    },
    visualMap: {
        show: false,
        min: 500,
        max: 600,
        inRange: {
            colorLightness: [0, 1]
        }
    },
    series : [
        {
            name:'课程内容分布',
            type:'pie',
            clockwise:'true',
            startAngle:'0',
            radius : '60%',
            center: ['50%', '50%'],
            data:[
                {
                    value:70,
                    name:'P1',
                    itemStyle:{
                        normal:{
                            color:'rgb(255,192,0)',
                            shadowBlur:'90',
                            shadowColor:'rgba(0,0,0,0.8)',
                            shadowOffsetY:'30'
                        }
                    }
                },
                {
                    value:10,
                    name:'P2',
                    itemStyle:{
                        normal:{
                            color:'rgb(1,175,80)'
                        }
                    }
                },
                {
                    value:20,
                    name:'P3',
                    itemStyle:{
                        normal:{
                            color:'rgb(122,48,158)'
                        }
                    }
                }
 
            ],
        }
    ]
});
</script>
</html>