<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>冬夏科技</title>
<head>
<?php
    require 'momlib.php';
    $momlib = new momlib();
    $qstr = $_SERVER["QUERY_STRING"];
    session_start();
?>
</head>
<body>
<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>
<?php
    session_start();
    if ($qstr=="1"){
        echo "<p>密码不一致</p>";
    }
    elseif($qstr=="2"){
        echo "<p>用户名被占用</p>";
    }
    elseif($qstr=="3"){
        echo "<p>注册成功</p>";
    }
    elseif($qstr=="4"){
        if (isset($_SESSION['message'])){
            echo "<p>操作失败[".$_SESSION['message']."]</p>";
        }
        else{
            echo "<p>操作失败</p>";
        }
    }
    elseif($qstr=="5"){
        echo "<p>用户名被占用</p>";
    }
    elseif($qstr=="6"){
        session_destroy();
        echo "<p>退出成功</p>";
    }
    elseif($qstr=="7"){
        echo "<p>请先登录</p>";
    }
    echo "<p><a href=\"index.php\">返回首页</a></p>";
?>

</body>

</html>
