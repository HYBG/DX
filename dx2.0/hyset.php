<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<script src="./js/echarts.min.js"></script>
<script src="./js/hy.js"></script>
<?php
require "../phplib/hylib.php";
parse_str($_SERVER["QUERY_STRING"]);
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("hy")){
        if (!isset($date) or !isset($tag)){
            echo "无相应数据";
            exit;
        }
        echo "<title>".$tag."</title>";
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
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<div id="more">
<a href="index.php" target=\"_blank\">Home</a>&nbsp;&nbsp;<a href="hyma.php" target=\"_blank\">MA</a>&nbsp;&nbsp;<a href="hymore.php" target=\"_blank\">More</a>
</div>
<?php
    $prev = $hy->exe_sql_one("select date from iknow_data where date<'".$date."' order by date desc limit 1");
    $next = $hy->exe_sql_one("select date from iknow_data where date>'".$date."' order by date limit 1");
    echo "<div>";
    if (count($prev)>0){
        echo "<h2><a href=\"hyset.php?date=".$prev[0]."&tag=".$tag."\">prev</a></h2>";
    }
    echo "<h2>".$tag."</h2>";
    if (count($next)>0){
        echo "<h2><a href=\"hyset.php?date=".$next[0]."&tag=".$tag."\">next</a></h2>";
    }
    echo "</div>";
?>
<div id="chartmain1" style="width:1600px; height: 400px;"></div>
<div id="chartmain2" style="width:1600px; height: 400px;"></div>
<script type="text/javascript">
<?php
    echo "var tagtext = '".$tag."'";
?>
        //指定图标的配置和数据
        var option0 = {
            legend: {},
            tooltip: {},
            dataset: {
                source: [
                    ['product', '上破', '下破', '收盘'],
                    ['银行', 43.3, 85.8, 93.7],
                    ['煤炭', 83.1, 73.4, 55.1],
                    ['计算机', 86.4, 65.2, 82.5],
                    ['有色', 72.4, 53.9, 39.1],
                    ['食品', 43.3, 85.8, 93.7],
                    ['化工', 83.1, 73.4, 55.1],
                    ['钢铁', 86.4, 65.2, 82.5],
                    ['证券', 72.4, 53.9, 39.1],
                    ['医药', 43.3, 85.8, 93.7],
                    ['新材料', 83.1, 73.4, 55.1],
                    ['农业', 86.4, 65.2, 82.5],
                    ['养殖业', 72.4, 53.9, 39.1]
                    ['航空', 43.3, 85.8, 93.7],
                    ['港口', 83.1, 73.4, 55.1],
                    ['汽车制造', 86.4, 65.2, 82.5],
                    ['保险', 72.4, 53.9, 39.1],
                    ['石油开采', 43.3, 85.8, 93.7],
                    ['家用轻工', 83.1, 73.4, 55.1],
                    ['零售', 86.4, 65.2, 82.5]
                ]
            },
            xAxis: {type: 'category'},
            yAxis: {},
            // Declare several bar series, each will be mapped
            // to a column of dataset.source by default.
            series: [
                {type: 'bar'},
                {type: 'bar'},
                {type: 'bar'}
            ]
        };
        //初始化echarts实例
        var myChart0 = echarts.init(document.getElementById('chartmain1'));
        //使用制定的配置项和数据显示图表
        myChart0.setOption(option0);

        /*var option = {
            title:{
                text:tagtext
            },
            tooltip:{},
            legend:{
                data:['涨跌幅分布']
            },
            xAxis:{
                data:["-9","-8","-7","-6","-5","-4","-3","-2","-1","0","1","2","3","4","5","6","7","8","9"]
            },
            yAxis:{

            },
            series:[{
                name:'数量',
                type:'bar',
                data:[500,200,360,100,20,20,20,20,20,20,120,20,420,20,20,20,20,20,20]
            }]
        };
        //初始化echarts实例
        var myChart = echarts.init(document.getElementById('chartmain2'));
        //使用制定的配置项和数据显示图表
        myChart.setOption(option);*/
    </script>
</body>
</html>