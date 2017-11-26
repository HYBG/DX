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
        header('Location: ' . "/mom/result.php?7");
        exit();
    }
    $qstr = $_SERVER["QUERY_STRING"];
    $its = explode("&",$qstr);
    if (count($its)==2){
        $bs = $its[0];
        $dat = $its[1];
    }
    if ($bs=="4"){
        $pid = $dat;
        $hold = $momlib->exe_sql_one("select count(*) from ikmom_project_hold_v where pid='".$pid."'");
        if ($hold[0]!="0"){
            header('Location: ' . "/mom/result.php?8");
            exit();
        }
        
    }
    if (isset($_POST["CODE"]) and isset($_POST["AMOUNT"]) and isset($_POST["PRICE"])){
        $code = $_POST["CODE"];
        $amount = intval($_POST["AMOUNT"]);
        $price = floatval($_POST["PRICE"]);
        $r = new momerr(OPER_NOT_EXIST,"para error");
        $w = date("w");
        $h = date("H");
        if (($w>=1 and $w<=5) and $h<15){
            if ($bs=="1"){
                $r = $momlib->buysell_v($dat,0,$code,$amount,$price);
            }
            elseif ($bs=="2"){
                $r = $momlib->buysell_v($dat,1,$code,$amount,$price);
            }
            elseif ($bs=="3"){
                $r = $momlib->recall($dat);
            }
        }
        else{
            $r = new momerr(TIME_NOT_GOOD,"对账时间,请稍后下单");
        }
        if ($r->code()==0){
            header('Location: ' . "/mom/project.php?".$dat);
            exit();
        }
        else{
            echo "<p>".$r->message()."</p>";
        }
    }
    elseif($bs=="3"){
        $r = $momlib->recall($dat);
        if ($r->code()==0){
            header('Location: ' . "/mom/project.php?".$dat);
            exit();
        }
        else{
            echo "<p>".$r->message()."</p>";
        }
    }
    else{
        echo "<p>交易信息不完整</p>";
    }
?>

</body>

</html>
