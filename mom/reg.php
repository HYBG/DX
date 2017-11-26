<html>

<head>
<meta http-equiv="Content-Language" content="zh-cn">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>注册结果</title>
<head>
<?php
    require 'momlib.php';
    $momlib = new momlib();

    if (isset($_POST["USER"]) and isset($_POST["PASSWD"]) and isset($_POST["REPASSWD"])){
        $user = $_POST["USER"];
        $passwd = $_POST["PASSWD"];
        $repasswd = $_POST["REPASSWD"];
        if ($passwd!=$repasswd){
            header('Location: ' . "/mom/result.php?1");
            exit();
        }
        $rename = $momlib->exe_sql_one("select count(*) from ikmom_user where uname='".$user."'");
        if (intval($rename[0])!=0){
            header('Location: ' . "/mom/result.php?2");
            exit();
        }
    }
    else{
        header('Location: ' . "/mom/result.php?3");
        exit();
    }
    
    
?>
</head>
<body>
<?php
    $r = $momlib->createuser($user,$passwd,date('Y-m-d'));
    if ($r->code()==0){
        //echo "注册成功";
        header('Location: ' . "/mom/result.php?4");
    }
    else{
        $_SESSION['message'] = $r->message();
        header('Location: ' . "/mom/result.php?3");
    }
?>

</body>

</html>
