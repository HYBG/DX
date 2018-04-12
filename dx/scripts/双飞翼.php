<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>汉尧科技</title>
<style type="text/css">
* {
    margin: 0;
    padding: 0;
}
body,
html {
    height: 100%;
    font: 20px/40px "microsoft yahei";
    color: white;
}
            
#container {
    width: 90%;
    margin: 0 auto;
    height: 100%;
}
            
#header,
#footer {
    height: 10%;
    background: #FFFFFF;
}
            
#main {
    height: 80%;
}
            
#center,
#left,
#right {
    height: 100%;
    float: left;
}
#center {
    width: 100%;
    background: white;
}
            
#right {
    background: lightblue;
    width: 15%;
    margin-left: -15%;
}
            
#left {
    background: lightcoral;
    width: 15%;
    margin-left: -100%;
}
            
#main-inner {
    padding-left: 20%;
}
</style>
</head>
<body>
<div id="container">
<div id="header"><h1 style="text-shadow:5px 5px 5px #FF8C00;color:#FF4500;padding:20px">汉尧科技</h1>
</div>
<div id="left" style="float:left;">
<table style="top:50%;margin:20px;color:#FF4500">
<tr><td style="text-align:center;">日期</td><td style=""></td></tr>
<tr><td>上突</td><td style=""></td></tr>
<tr><td>下突</td><td style=""></td></tr>
</table>
</div>

<div id="main" style="float:left;">
    <div id="center">
    <div id="main-inner">
    <table style="width=100%;color:#FF4500">
    <thead style="text-align: center">
    <tr><td>股票</td><td>高点概率</td><td>股票</td><td>低点概率</td></tr>
    </thead>
<tbody>
<tr><td>2018-04-06</td></tr>
<tr><td>2018-04-05</td></tr>
</tbody>
</table>
    </div>
</div>

<div id="right">right</div>
</div>
<div id="footer">footer</div>
</div>
</body>
</html>