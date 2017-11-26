<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>冬夏科技</title>
</head>

<body>

<h1 align="center"><span lang="en-us">&nbsp;</span><span style="background-color: #FFFFFF"><font size="7" color="#FF3300">冬</font><font size="7" color="#FFFF00">夏</font></span><a href="index.php"><img border="0" src="dxhome.png" width="400" height="200"></a><font size="7" color="#FFFF00">科</font><font size="7" color="#FF3300">技</font></h1>

<?php
    require 'momlib.php';
    $momlib = new momlib();
    session_start();
    if (!isset($_SESSION['uid'])){
?>

<form method="POST" action="reg.php">
    <p>用户名<input type="text" name="USER" size="20">密码&nbsp; <input type="password" name="PASSWD" size="20">确认密码&nbsp; <input type="password" name="REPASSWD" size="20"><input type="submit" value="提交注册" name="REG"></p>
</form>
<form method="POST" action="user.php">
    <p>用户名<input type="text" name="USER" size="20">密码&nbsp; <input type="password" name="PASSWD" size="20"><input type="submit" value="用户登录" name="LOGON"></p>
</form>

<?php
    }
    else{
        echo "<p><a href=\"user.php\" target=\"_blank\">我的冬夏</a></p>";
    }

    echo "<p>项目信息</p>";
    $sa = array("0"=>"不可计提","3"=>"可计提");
    $data = $momlib->exe_sql_batch("select pid,manager,status,retmax,edate,rate,baseline,peak from ikmom_project_v where status=0 or status=3 order by rate desc");
    echo "<table border=\"1\" width=\"80%\">";
    echo "<tr><td width=\"150\">项目ID</td>";
    echo "<td width=\"150\">管理人</td>";
    echo "<td width=\"150\">状态</td>";
    echo "<td width=\"150\">回撤限制</td>";
    echo "<td width=\"150\">生效日期</td>";
    echo "<td width=\"150\">收益率</td>";
    echo "<td width=\"150\">业绩基线</td>";
    echo "<td width=\"150\">最近峰值</td></tr>";
    foreach($data as $row){
        $uname = $momlib->exe_sql_one("select uname from ikmom_user where uid='".$row[1]."'");
        echo "<tr><td width=\"150\">".$row[0]."</td>";
        echo "<td width=\"150\">".$uname[0]."</td>";
        echo "<td width=\"150\">".$sa[$row[2]]."</td>";
        echo "<td width=\"150\">".$row[3]."</td>";
        echo "<td width=\"150\">".$row[4]."</td>";
        echo "<td width=\"150\">".$row[5]."</td>";
        echo "<td width=\"150\">".$row[6]."</td>";
        echo "<td width=\"150\">".$row[7]."</td></tr>";
    }
    echo "</table>";

?>

</body>

</html>
