<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>logon</title>
</head>

<body>
<?php
    $qstr = $_SERVER["QUERY_STRING"];
    if ($qstr=="1"){
        echo "<p>注册成功</p>";
    }
    elseif ($qstr=="2"){
        echo "<p>密码错误</p>";
    }
    elseif ($qstr=="3"){
        session_destroy();
        echo "<p>安全退出</p>";
    }
?>

<form method="POST" action="user.php">
    <p>　</p>
    <p>用户名 <input type="text" name="USER" size="20"></p>
    <p>密码<input type="password" name="PASSWD" size="20"></p>
    <p><input type="submit" value="提交" name="B1"><input type="reset" value="重置" name="B2"></p>
</form>

</body>

</html>
