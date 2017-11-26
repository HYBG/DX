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
        $momlib->recallall($pid);
        $w = date("w");
        $h = date("H");
        if ($w>=1 and $w<=5 and $h>9 and $h<15){
            $hold = $momlib->exe_sql_batch("select code,amount from ikmom_project_hold_v where pid='".$pid."'");
            $val = 0.0;
            foreach($hold as $row){
                $pc = $momlib->rtprice($row[0]);
                $val = $val + $pc*floatval($row[1]);
            }
            $my = $momlib->exe_sql_one("select cash from ikmom_invest_account_v where pid='".$pid."'");
            $all = $val+floatval($my[0]);
            $bl = $momlib->exe_sql_one("select baseline from ikmom_project_v where pid='".$pid."'");
            $inf = $momlib->exe_sql_one("select settlemin,sharerate from ikmom_user where uid = (select manager from ikmom_project_v where pid='".$pid."')");
            $rate = ($all-floatval($bl[0]))/floatval($bl[0]);
            if ($rate>floatval($inf[0])){
                $momlib->sellall($pid);
                $cash = $momlib->exe_sql_one("select cash from ikmom_invest_account_v where pid='".$pid."'");
                $ben = (floatval($cash[0])-floatval($bl[0]))*floatval($inf[1]);
                $sqls = array();
                $seq = $momlib->buildid("A");
                $td = date('Y-m-d');
                $tm = date('H:i:s');
                $uid = $momlib->exe_sql_one("select manager from ikmom_project_v where pid='".$pid."'");
                array_push($sqls,"insert into ikmom_account_detail(seqnum,uid,date,time,mtype,inout,amount,mark) values('".$seq."','".$uid[0]."','".$td."','".$tm."',0,1,".sprintf("%.2f",$ben).",'主动计提')");
                array_push($sqls,"update ikmom_account set money_v=money_v+".sprintf("%.2f",$ben)." where uid='".$uid[0]."'");
                $r = $momlib->task($sqls);
                if ($r->code()==0){
                    header('Location: ' . "/mom/project.php?".$dat);
                    exit();
                }
                else{
                    echo "<p>".$r->message()."</p>";
                }
            }
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
