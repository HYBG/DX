<?php
    define ("SUCC",0);
    define ("DB_CONN_ERR",10001);
    define ("DB_NOT_FOUND",10002);
    define ("DB_TASK_FAILED",20001);
    define ("UNAME_NOT_FOUND",30001);
    define ("PROJECT_INVEST_ACCOUNT_ERROR",30101);
    define ("PROJECT_STATUS_ERROR",30102);
    define ("STOCK_STILL_HOLD",30103);
    define ("STOCK_NOT_ENOUGH",30104);
    define ("CASH_NOT_ENOUGH",30105);
    define ("STOCK_NOT_HOLD",30106);
    define ("USER_NOT_IN_CHARGE",30107);
    define ("ORDER_STATUS_ERROR",30108);
    define ("ORDER_SEQ_ERROR",30109);
    define ("OPER_NOT_EXIST",30110);
    define ("TIME_NOT_GOOD",30111);
    define ("OPERATE_NOT_SUPPORT",30112);
    class momerr{
        private $errcode;
        private $errmsg;
        function __construct($code,$msg){
            $this->errcode = $code;
            $this->errmsg = $msg;
        }
        function __destruct(){
        }

        function code(){
            return $this->errcode;
        }
        
        function message(){
            return $this->errmsg;
        }
    }

    class momlib{
        private $db;
        private $home = "/var/data/iknow";
        function __construct(){
            $this->db = mysqli_connect('localhost', 'root', '123456');
            if (!$this->db){
                echo "1001|cannot connect db\n";
                exit;
            }
            $selected = mysqli_select_db($this->db, "hy");
            if (!$selected){
                echo "1002|db not found\n";
                exit;
            }
        }
        function __destruct(){
            mysqli_close($this->db);
        }
        
        function exe_sql_one_non_return($sql){
            //echo $sql."\n";
            $result = mysqli_query($this->db, $sql);
            if (!$result){
                return 1;
                //echo "exe sql[".$sql."] failed\n";
            }
            else{
                return 0;
                //echo "exe sql[".$sql."] success\n";
            }
        }
        
        function exe_sql_one($sql){
            //echo $sql."\n";
            $a = array();
            $result = mysqli_query($this->db, $sql);
            if($ret=mysqli_fetch_row($result)){
                foreach($ret as $item){
                    array_push($a,$item);
                }
            }
            return $a;
        }
        
        function exe_sql_batch($sql){
            //echo $sql."\n";
            $a = array();
            $result = mysqli_query($this->db, $sql);
            while($ret=mysqli_fetch_row($result)){
                array_push($a,$ret);
            }
            return $a;
        }
        
        function task($sqls){
            foreach($sqls as $sql){
                $r = mysqli_query($this->db, $sql);
                if (!$r){
                    //echo $sql." failed\n";
                    mysql_query("ROLLBACK");
                    return new momerr(DB_TASK_FAILED,$sql);
                }
            }
            mysql_query("COMMIT");
            return new momerr(SUCC,"");
        }
        
        function rtprice($code){
            $mk = "sh";
            if ((substr($code,0,1)!="6") and ((substr($code,0,1)!="5"))){
                $mk = "sz";
            }
            $url = "http://hq.sinajs.cn/list=".$mk.$code;
            $line = file_get_contents($url);
            $its = explode("\n",$line);
            $con = explode("\"",$its[0]);
            $ps = explode(",",$con[1]);
            return floatval($ps[3]);
        }
        
        function buildid($prefix){
            return substr($prefix,0,1).date('YmdHis').mt_rand(10000,99999);
        }

        function check($uname,$passwd){
            $pd = $this->exe_sql_one("select passwd,uid from ikmom_user where uname='".$uname."'");
            if ($pd[0]==$passwd){
                return new momerr(SUCC,$pd[1]);
            }
            return new momerr(UNAME_NOT_FOUND,"user[".$uname."],password[".$passwd."]");
        }

        function createuser($name,$passwd,$rdate){
            $uid = "U10".substr($rdate,0,4).substr($rdate,5,2).substr($rdate,8,2).date("His").mt_rand(100,999);
            $sqls = array();
            array_push($sqls,"insert into ikmom_user(uname,uid,rdate,passwd) values('".$name."','".$uid."','".$rdate."','".$passwd."')");
            array_push($sqls,"insert into ikmom_account(uid) values('".$uid."')");
            $pid = $this->buildid("P");
            array_push($sqls,"insert into ikmom_project_v(pid,manager,edate) values('".$pid."','".$uid."','".$rdate."')");
            array_push($sqls,"insert into ikmom_invest_account_v(pid,owner) values('".$pid."','".$uid."')");
            array_push($sqls,"update ikmom_user set status=1 where uid='".$uid."'");
            return $this->task($sqls);
        }

        function signproject_v($uid){
            $td = date('Y-m-d');
            $sqls = array();
            array_push($sqls,"UPDATE ikmom_project_v SET status=0,edate='".$td."' WHERE manager='".$uid."'");
            array_push($sqls,"update ikmom_invest_account_v set status=2");
            return $this->task($sqls);
        }

        function withdraw_v($pid,$flag){
            $hold = $this->exe_sql_one("select count(*) from ikmom_project_hold_v where pid='".$pid."'");
            if ($hold[0]!=0){
                return new momerr(STOCK_STILL_HOLD,$pid);
            }
            $have = $this->exe_sql_one("select cash+freeze from ikmom_invest_account_v where pid='".$pid."'");
            if (count($have)<=0){
                return new momerr(PROJECT_INVEST_ACCOUNT_ERROR,$pid);
            }
            $pinf = $this->exe_sql_one("select manager,status,baseline from ikmom_project_v where pid='".$pid."'");
            if (intval($pinf[1])!=3){
                return new momerr(PROJECT_STATUS_ERROR,"pid[".$pid."],status[".$pinf[1]."]");
            }
            $sr = $this->exe_sql_one("select sharerate from ikmom_user where uid='".$pinf[0]."'");
            $bonus = (floatval($have[0])-floatval($pinf[2]))*floatval($sr[0]);
            $sqls = array();
            $td = date('Y-m-d');
            $tm = date('H:i:s');
            $seq = $this->buildid("A");
            array_push($sqls,"update ikmom_account set money_v=money_v+".$bonus." where uid='".$pinf[0]."'");
            array_push($sqls,"insert into ikmom_account_detail(seqnum,uid,date,time,mtype,inout,amount,mark) values('".$seq."','".$uid."','".$td."','".$tm."',1,1,'".$bonus."','结算分红')");
            array_push($sqls,"update ikmom_project_v set status=1,cdate='".$td."' where pid='".$pid."'");
            array_push($sqls,"update ikmom_invest_account_v set status=3 where pid='".$pid."'");
            if ($flag==1){
                $pid = $this->buildpid();
                array_push($sqls,"insert into ikmom_project_v(pid,manager,edate) values('".$pid."','".$pinf[0]."','".$td."')");
                array_push($sqls,"insert into ikmom_invest_account_v(pid,owner) values('".$pid."','".$pinf[0]."')");
            }
            return $this->task($sqls);
        }

        function snapshot_v(){
            $pids = $this->exe_sql_one("select pid from ikmom_project_v where status=0 or status=3");
            $sqls = array();
            foreach($pids as $pid){
                $data = $this->exe_sql_batch("select code,name,amount from ikmom_project_hold_v where pid='".$pid[0]."'");
                $td = date('Y-m-d');
                $tm = date('H:i:s');
                foreach($data as $row){
                    array_push($sqls,"insert into ikmom_hold_snapshot_v(pid,date,time,code,name,amount) values('".$pid[0]."','".$td."','".$tm."','".$row[0]."','".$row[1]."',".$row[2].")");
                }
            }
            return $this->task($sqls);
        }

        function buysell_v($pid,$bs,$code,$amount,$price){
            if ($bs==0){
                $need = sprintf("%.2f",$price*$amount*1.0003);
                $have = $this->exe_sql_one("select cash from ikmom_invest_account_v where pid='".$pid."'");
                if (floatval($have[0])>floatval($need)){
                    $seq = $this->buildid("O");
                    $oseq = $this->buildid("S");
                    $td = date('Y-m-d');
                    $tm = date('H:i:s');
                    $sqls = array();
                    array_push($sqls,"insert into ikmom_order_seq_v(seqnum,pid,date,time,otype,orderseq) values('".$oseq."','".$pid."','".$td."','".$tm."',0,'".$seq."')");
                    array_push($sqls,"insert into ikmom_order_v(seqnum,pid,buysell,code,amount,price,status) values('".$seq."','".$pid."',0,'".$code."',".$amount.",".$price.",0)");
                    array_push($sqls,"update ikmom_invest_account_v set cash=cash-".$need.",freeze=freeze+".$need." where pid='".$pid."'");
                    return $this->task($sqls);
                }
                else{
                    return new momerr(CASH_NOT_ENOUGH,"pid[".$pid."]");
                }
            }
            elseif($bs==1){
                $have = $this->exe_sql_one("select amount from ikmom_project_hold_v where pid='".$pid."' and code='".$code."'");
                if (count($have)>0){
                    if (floatval($have[0])>=$amount){
                        $seq = $this->buildid("O");
                        $oseq = $this->buildid("S");
                        $td = date('Y-m-d');
                        $tm = date('H:i:s');
                        $sqls = array();
                        array_push($sqls,"insert into ikmom_order_seq_v(seqnum,pid,date,time,otype,orderseq) values('".$oseq."','".$pid."','".$td."','".$tm."',1,'".$seq."')");
                        array_push($sqls,"insert into ikmom_order_v(seqnum,pid,buysell,code,amount,price,status) values('".$seq."','".$pid."',1,'".$code."',".$amount.",".$price.",0)");
                        array_push($sqls,"update ikmom_project_hold_v set amount=amount-".$amount.",freeze=freeze+".$amount." where pid='".$pid."' and code='".$code."'");
                        return $this->task($sqls);
                    }
                    else{
                        return new momerr(STOCK_NOT_ENOUGH,"pid[".$pid."],code[".$code."],amount[".$amount."]"); //stock not enough
                    }
                }
                else{
                    return new momerr(STOCK_NOT_HOLD,"pid[".$pid."],code[".$code."]"); //stock not hold
                }
            }
            return new momerr(OPERATE_NOT_SUPPORT,"pid[".$pid."],code[".$code."],oper[".$bs."]");
        }
        
        function sellall($pid){
            $hold = $this->exe_sql_batch("select code,amount from ikmom_project_hold_v where pid='".$pid."'");
            foreach($hold as $row){
                $pc = $this->rtprice($row[0]);
                $this->buysell_v($pid,1,$row[0],$row[1],$pc);              
            }
        }

        function recall($seq){
            $data = $this->exe_sql_one("select pid,buysell,amount,price,status,code from ikmom_order_v where seqnum='".$seq."'");
            if (count($data)>0){
                $pid = $data[0];
                if (intval($data[4])==0){
                    $amount = floatval($data[2]);
                    $price = floatval($data[3]);
                    $code = $data[5];
                    $oseq = $this->buildid("S");
                    $td = date('Y-m-d');
                    $tm = date('H:i:s');
                    if (intval($data[1])==0){
                        $need = sprintf("%.2f",$price*$amount*1.0003);
                        $sqls = array();
                        array_push($sqls,"insert into ikmom_order_seq_v(seqnum,uid,date,time,otype,orderseq) values('".$oseq."','".$uid."','".$td."','".$tm."',2,'".$seq."')");
                        array_push($sqls,"update ikmom_order_v set status=2 where seqnum='".$seq."'");
                        array_push($sqls,"update ikmom_invest_account_v set cash=cash+".$need.",freeze=freeze-".$need." where pid='".$pid."'");
                        return $this->task($sqls);
                    }
                    else{
                        $sqls = array();
                        array_push($sqls,"insert into ikmom_order_seq_v(seqnum,pid,date,time,otype,orderseq) values('".$oseq."','".$pid."','".$td."','".$tm."',2,'".$seq."')");
                        array_push($sqls,"update ikmom_order_v set status=2 where seqnum='".$seq."'");
                        array_push($sqls,"update ikmom_project_hold_v set amount=amount+".$amount.",freeze=freeze-".$amount." where pid='".$pid."' and code='".$code."'");
                        return $this->task($sqls);
                    }
                }
                else{
                    return new momerr(ORDER_STATUS_ERROR,""); //order status error
                }
            }
            else{
                return new momerr(ORDER_SEQ_ERROR,"seq[".$seq."]"); //invalid order or order not exist
            }
        }
        
        function recallall($pid){
            $all = $this->exe_sql_batch("select seqnum from ikmom_order_v where pid='".$pid."' and status=0");
            foreach($all as $seq){
                $this->recall($seq[0]);
            }
        }

        function clearorders(){
            $all = $this->exe_sql_batch("select seqnum from ikmom_order_v where status=0");
            foreach($all as $seq){
                $this->recall($seq[0]);
            }
        }

        function clearfreeze(){
            $pids = $this->exe_sql_batch("select distinct pid from ikmom_project_hold_v");
            $sqls = array();
            foreach($pids as $pid){
                $codes = $this->exe_sql_batch("select code from ikmom_project_hold_v where pid='".$pid[0]."'");
                foreach($codes as $code){
                    array_push($sqls,"update ikmom_project_hold_v set amount=amount+freeze,freeze=0 where pid='".$pid[0]."' and code='".$code[0]."'");
                }
            }
            return $this->task($sqls);
        }
    }
?>

