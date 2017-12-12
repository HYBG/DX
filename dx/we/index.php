<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">

<title>冬夏科技</title>
</head>

<body>

<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>

<h2 align="center"></h2>
<?php
    require 'welib.php';
    $iklib = new ikwelib();
    if(!isset($_SESSION['uid'])){
        $app = $iklib->dxapp();
        if (count($app)>0){
            $appid = $app[0];
            $appsecret = $app[1];
            file_put_contents("/var/www/html/we/log/test.log", date('H:i:s')." appid[".$appid."],appsecret[".$appsecret."]\n", FILE_APPEND);
            //$iklib->logger("appid[".$appid."],appsecret[".$appsecret."]");
            $callback = "https://www.boardgame.org.cn/we/mymom.php";
            $state = "login";
            $appid = "wx8b7a4a089c2395c1";
            $appsecret = "016b3ae90b12b5e5c33ca5451337dcd1";
            $url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=".$appid."&redirect_uri=".urlencode($callback)."&response_type=code&scope=snsapi_userinfo&state=".$state."#wechat_redirect";
            //$iklib->logger($url);
            file_put_contents("/var/www/html/we/log/test.log", date('H:i:s')." ".$url."\n", FILE_APPEND);
            header("Location: ".$url);
        }
        else{
            echo "appid or appsecret missing </br>";
        }
    }
    else{
        echo "<div align=\"center\">";
        echo "MOM 主页";
        echo "</div>";
    }
?>
</body>

</html>