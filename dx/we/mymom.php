<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">

<title>冬夏科技</title>
</head>

<body>

<!--<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
-->
<h2 align="center"></h2>
<?php
    require 'welib.php';
    $iklib = new ikwelib();

    $app = $iklib->dxapp();
    $appid = $app[0];
    $secret = $app[1];
    $code = $_GET["code"];
    $appid = "wx8b7a4a089c2395c1";
    $appsecret = "016b3ae90b12b5e5c33ca5451337dcd1";
    $get_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=".$appid."&secret=".$secret."&code=".$code."&grant_type=authorization_code";

    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$get_token_url);
    curl_setopt($ch,CURLOPT_HEADER,0);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
    $res = curl_exec($ch);
    curl_close($ch);
    $iklib->logger($res);
    $json_obj = json_decode($res,true);

    //根据openid和access_token查询用户信息
    $access_token = $json_obj['access_token'];
    $openid = $json_obj['openid'];
    $get_user_info_url = "https://api.weixin.qq.com/sns/userinfo?access_token=".$access_token."&openid=".$openid."&lang=zh_CN";

    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$get_user_info_url);
    curl_setopt($ch,CURLOPT_HEADER,0);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
    $res = curl_exec($ch);
    $iklib->logger($res);
    curl_close($ch);

    //解析json
    $user_obj = json_decode($res,true);
    $_SESSION['user'] = $user_obj;

    //进行业务逻辑操作
    echo "<div align=\"center\">";
    echo "MYMOM 主页";
    echo "</div>";

?>
</body>

</html>