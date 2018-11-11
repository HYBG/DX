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
$limt = 40;
if (isset($count)){
    $limt = intval($count);
    if ($limt<40){
        $limt = 40;
    }
}
$hy = new hylib('root','123456');
if ($hy->isok()){
    if ($hy->select_db("iknow")){
        echo "<title>HY</title>";
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
<?php
echo "<h2><a href=\"ikrt.php\" target=\"_blank\">关注</a>&nbsp;&nbsp;<a href=\"ikk.php\" target=\"_blank\">K线</a>&nbsp;&nbsp;<a href=\"ikc.php\" target=\"_blank\">收盘</a></h2>";
?>
<div id='table'>
   <table style="margin:0 auto;width:80%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th style="width:10%;">日期</th>
          <th style="width:40%;">K线分布</th>
          <th style="width:40%;">收盘分布</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $dic = array('k'=>array(),'c'=>array());
    $dts = $hy->exe_sql_batch("select distinct date from iknow.ik_attr order by date desc limit ".$limt);
    foreach($dts as $dt){
        echo '<tr><th><a href="http://www.boardgame.org.cn/ikwatch.php?date='.$dt[0].'" target="_blank">'.$dt[0].'</a></th>';
        echo '<th><canvas id="k'.$dt[0].'" width="500" height="400">该浏览器不支持画布</canvas></th>';
        echo '<th><canvas id="c'.$dt[0].'" width="400" height="400">该浏览器不支持画布</canvas></th></tr>';
        $fvcnt1 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=1");
        $fvcnt2 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=2");
        $fvcnt3 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=3");
        $fvcnt4 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=4");
        $fvcnt5 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=5");
        $fvcnt6 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=6");
        $fvcnt7 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=7");
        $fvcnt8 = $hy->exe_sql_one("select count(*) from ik_deri where date='".$dt[0]."' and fv=8");
        $csrccnt1 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.2");
        $csrccnt2 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.4");
        $csrccnt3 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.6");
        $csrccnt4 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."' and csrc<=0.8");
        $csrccnt5 = $hy->exe_sql_one("select count(*) from ik_attr where date='".$dt[0]."'");
        $csrccnt1 = intval($csrccnt1[0]);
        $csrccnt2 = intval($csrccnt2[0])-$csrccnt1;
        $csrccnt3 = intval($csrccnt3[0])-$csrccnt2-$csrccnt1;
        $csrccnt4 = intval($csrccnt4[0])-$csrccnt3-$csrccnt2-$csrccnt1;
        $csrccnt5 = intval($csrccnt5[0])-$csrccnt4-$csrccnt3-$csrccnt2-$csrccnt1;
        $dic['date'] = $dt[0];
        $dic['k'][$dt[0]] = array(intval($fvcnt1[0]),intval($fvcnt2[0]),intval($fvcnt3[0]),intval($fvcnt4[0]),intval($fvcnt5[0]),intval($fvcnt6[0]),intval($fvcnt7[0]),intval($fvcnt8[0]));
        $dic['c'][$dt[0]] = array($csrccnt1,$csrccnt2,$csrccnt3,$csrccnt4,$csrccnt5);
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
    echo "var cdic = new Array();\n";
    foreach($dic['k'] as $key=>$val){
        echo 'kdic["'.$key.'"] = ['.$val[0].','.$val[1].','.$val[2].','.$val[3].','.$val[4].','.$val[5].','.$val[6].','.$val[7].'];';
    }
    foreach($dic['c'] as $key=>$val){
        echo 'cdic["'.$key.'"] = ['.$val[0].','.$val[1].','.$val[2].','.$val[3].','.$val[4].'];';
    }
?>
for (var key in kdic) {
    var machart = echarts.init(document.getElementById('k'+key));
    machart.setOption({
        title: {
            text: key,
            subtext: 'K线分布',
            x:'center'
        },
        xAxis: {
            type: 'category',
            boundaryGap: true,
            data: ['上阳','上阴','下阳','下阴','双阳','双阴','内阳','内阴']
        },
        yAxis: {
            type: 'value',
            name: '数量'
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
                "name": "K",
                "type": "bar",
                "barWidth" : 20,
                "data": kdic[key],
                itemStyle:{
                    normal:{
                        color:function (params){
                            var colorList = ['#FF3030','#228B22','#FF3030','#228B22','#FF3030','#228B22','#FF3030','#228B22'];
                            return colorList[params.dataIndex];
                        }
                    }
                }
            }
        ]
    });
}
for (var key in cdic) {
    var fvchart = echarts.init(document.getElementById('c'+key));
    var option = {
        title: {
            text: key,
            subtext: '收盘分布',
            x:'center'
        },
        tooltip: {
            show: true
        },
        toolbox: {
            show: true,
            feature: {
                mark: { show: true },
                saveAsImage: { show: true }
            }
        },
        xAxis: [
            {
                type: 'category',
                data: ['0-20','20-40','40-60','60-80','80-100']
            }
        ],
        yAxis: [
            {
                type: 'value',
                name: '数量'
            }
        ],
        series: [
            {
                "name": "K",
                "type": "bar",
                "barWidth" : 20,
                "data": cdic[key],
                itemStyle:{
                    normal:{
                        color:function (params){
                            var colorList = ['#228B22','#66CD00','#B03060','#B03060','#FF3030'];
                            return colorList[params.dataIndex];
                        }
                    }
                }
            }
        ]
    };
    fvchart.setOption(option);
}
</script>
</html>