<?php
define ("IK_LOG_TRACE",0);
define ("IK_LOG_DEBUG",1);
define ("IK_LOG_INFO",2);
define ("IK_LOG_WARNING",3);
define ("IK_LOG_ERROR",4);
define ("IK_LOG_CRITICAL",5);
define ("IK_BUYIN",1);
define ("IK_SELLOUT",2);
class ikresult{
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

class ikmomlib{
    private $db;
    private $loglevel = 2; //0:trace,1:debug,2:info,3:warning,4:error,5:critical
    private $typehandler = array("text"=>"handle_text","event"=>"handle_event");
    private $eventhandler = array("subscribe"=>"handle_subscribe","unsubscribe"=>"handle_unsubscribe");
    private $cmdhandler = array("101"=>"handle_buy_rt","102"=>"handle_sell_rt","301"=>"handle_create");
    private $clickhandler = array("V2003_TERMINNATE"=>"handle_close");
    
    function __construct(){
        $this->db = mysqli_connect('localhost', 'root', '123456');
        if (!$this->db){
            $this->logger("welib",IK_LOG_ERROR,"cannot connect db");
        }
        $selected = mysqli_select_db($this->db, "hy");
        if (!$selected){
            $this->logger("welib",IK_LOG_ERROR,"db not found");
        }
        $lev = $this->exe_sql_one("select value from iknow_global where name='loglevel'");
        if (count($lev)>0){
            $this->loglevel = intval($lev[0]);
        }
    }

    function __destruct(){
        mysqli_close($this->db);
    }

    private function transmit_text($from,$to,$content){
        $texttpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content></xml>";
        $result = sprintf($texttpl,$from,$to,time(),$content);
        return $result;
    }

    private function rtprice($code){
        $mk = "sh";
        if ((substr($code,0,1)!="6") and ((substr($code,0,1)!="5"))){
            $mk = "sz";
        }
        $url = "http://hq.sinajs.cn/list=".$mk.$code;
        $line = file_get_contents($url);
        $its = explode("\n",$line);
        $con = explode("\"",$its[0]);
        $ps = explode(",",$con[1]);
        return $ps;
    }

    private function buildid($pre){ //$pre长度4,uid:U_IK,pid:P_IK,order:O_IK,seq:S_IK
        list($msec, $sec) = explode(' ',microtime());
        $id = date('YmdHis').sprintf('%.0f', floatval($msec)*100000000).mt_rand(100000,999999);
        return $pre.$id;
    }

    public function exe_sql_one($sql){
        $a = array();
        $result = mysqli_query($this->db, $sql);
        if ($result){
            if($ret=mysqli_fetch_row($result)){
                foreach($ret as $item){
                    array_push($a,$item);
                }
            }
        }
        else{
            $this->logger_db("welib",IK_LOG_ERROR,"exe_sql_one:execute sql[".$sql."] failed");
        }
        return $a;
    }

    public function exe_sql_batch($sql){
        $a = array();
        $result = mysqli_query($this->db, $sql);
        if ($result){
            while($ret=mysqli_fetch_row($result)){
                array_push($a,$ret);
            }
        }
        else{
            $this->logger_db("welib",IK_LOG_ERROR,"exe_sql_batch:execute sql[".$sql."] failed");
        }
        return $a;
    }

    public function task($sqls,$commi=true){
        foreach($sqls as $sql){
            $r = mysqli_query($this->db, $sql);
            if (!$r){
                mysql_query("ROLLBACK");
                $this->logger_db("welib",IK_LOG_ERROR,"task:execute sql[".$sql."] failed,task rollback");
                return 1;
            }
            $this->logger_db("welib",IK_LOG_DEBUG,"task:execute sql[".$sql."] successfully");
        }
        if ($commi){
            mysql_query("COMMIT");
        }
        return 0;
    }
    
    private function synonym($name){
        $val = $this->exe_sql_one("select value from iknow_synonym where name='".$name."'");
        if (count($val)>0){
            return $val[0];
        }
        return "";
    }
    
    public function logger_db($mod,$lev,$log){
        if ($lev>=$this->loglevel){
            $this->logger($mod,$lev,$log);
            //$this->task(array("insert into iknow_log(timestamp,module,level,log) values('".$this->timestamp()."','".$mod."',".$lev.",'".$log."')"));
        }
    }

    public function logger($mod,$lev,$log){
        if(isset($_SERVER['HTTP_APPNAME'])){   //SAE
            sae_set_display_errors(false);
            sae_debug($log_content);
            sae_set_display_errors(true);
        }
        elseif($_SERVER['REMOTE_ADDR'] != "127.0.0.1"){ //LOCAL
            $max_size = 100000;
            $log_filename = "/var/www/html/we/log/we.log";
            if(file_exists($log_filename) and (abs(filesize($log_filename)) > $max_size)){
                unlink($log_filename);
            }
            file_put_contents($log_filename, $this->timestamp()." ".$mod." ".$lev." ".$log."\n", FILE_APPEND);
        }
    }

    private function timestamp(){
        $dt = date('Y-m-d H:i:s');
        list($msec, $sec) = explode(' ',microtime());
        $dt = $dt." ".sprintf('%.0f', floatval($msec)*100000000);
        return $dt;
    }

    private function uservalid($from){
        $ct = $this->exe_sql_one("select count(*) from iknow_user where extid='".$from."'");
        if (intval($ct[0])==1){
            return true;
        }
        return false;
    }

    private function is_open(){
        $td = date('Y-m-d');
        $offday = $this->exe_sql_one("select date from iknow_rest where date='".$td."'");
        if (count($offday)==0){
            $w = date('w');
            if (intval($w)>=1 and intval($w)<=5){
                $tm = date('H:i:s');
                if (($tm>"09:30:00" and $tm<"11:30:00") or ($tm>"13:00:00" and $tm<"15:00:00")){
                    return true;
                }
            }
        }
        return false;
    }

    public function dxapp(){
        $appid = $this->exe_sql_one("select value from iknow_global where name='appid'");
        $secret = $this->exe_sql_one("select value from iknow_global where name='appsecret'");
        if (count($appid)>0 and count($secret)>0){
            return array($appid[0],$secret[0]);
        }
        else{
            $this->logger_db("welib",IK_LOG_WARNING,"dxapp: appid or appsecret missing!");
            return array();
        }
    }
    
    private function createroot($baseline){
        $pid = $this->buildid("P_IK");
        $uid = $this->buildid("R_IK");
        if (0 == $this->task(array("insert into iknow_project_info_v(pid,uid,baseline,edate) values('".$ppid."','".$uid."','".$baseline.",'".date('Y-m-d')."')"))){
            return $pid;
        }
        return "";
    }

    public function handle_msg($poststr){
        $content = "";
        if (!empty($poststr)){
            $this->logger("bglib",BG_LOG_DEBUG,$poststr);
            $obj = simplexml_load_string($poststr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $RX_TYPE = trim($obj->MsgType);
            if (array_key_exists($RX_TYPE,$this->typehandler)){
                $content = call_user_func(array($this,$this->typehandler[$RX_TYPE]),$obj);
            }
            else{
                $content = "消息类型【".$RX_TYPE."】不支持";
            }
            $content = $this->transmit_text($obj->FromUserName,$obj->ToUserName,$content);
            $this->logger("bglib",BG_LOG_DEBUG,$content);
        }
        return $content;
    }

    private function handle_text($object){
        $content = $this->handle_key($object->Content,$object->FromUserName);
        if ($content == ""){
            $lis = explode(' ',trim($object->Content));
            if (array_key_exists($lis[0],$this->cmdhandler)){
                $content = call_user_func(array($this,$this->cmdhandler[$lis[0]]),array($object->FromUserName,array_slice($lis,1)));
            }
            else{
                $content = "无效指令";
            }
        }
        return $content;
    }
    
    private function getpid($from){
        $pid = $this->exe_sql_one("select pid from iknow_project_info_v where uid in (select uid from iknow_user where extid='".$from."')");
        if (count($pid)>0){
            return $pid[0];
        }
        return "";
    }

    private function getppid($from){
        $ppid = $this->exe_sql_one("select ppid from iknow_project_info_v where uid in (select uid from iknow_user where extid='".$from."')");
        if (count($ppid)>0){
            return $ppid[0];
        }
        return "";
    }

    private function handle_create($para){
        $from = $para[0];
        $enddate = $para[1][0];
        $uinf = $this->exe_sql_one("select uid,limper from iknow_user where extid='".$from."'");
        $left = $this->exe_sql_one("select pid,amount from iknow_account_hold_v where length(ppid)=0 and code='0' and amount>".$uinf[0]." order by hvalue desc limit 1");
        $sqls = array();
        if (count($left)==0){
            $ppid = $this->createroot(10000000000);
        }
        else{
            $ppid = $left[1];
        }
        $pid = $this->buildid("P_IK");
        array_push($sqls,"insert into iknow_project_info_v(pid,ppid,uid,baseline,edate,ddate) values('".$pid."','".$ppid."','".$uinf[0]."',".$uinf[1].",'".date('Y-m-d')."','".$enddate."')");
        array_push($sqls,"insert into iknow_account_hold_v(pid,code,amount,price,hvalue) values('".$pid."','0',".$uinf[1].",1,".$uinf[1].")");
        array_push($sqls,"update iknow_account_hold_v set amount=amount-".$uinf[1]." where pid='".$ppid."' and code='0'");
        if(0 == $this->task($sqls)){
            return "项目创建完成";
        }
        return "项目创建失败";
    }

    private function handle_buy_rt($para){
        if (!$this->is_open()){
            return "非交易时间";
        }
        $from = $para[0];
        $code = $this->synonym($para[1][0]);
        $amount = intval($para[1][1]);
        $pid = $this->getpid($from);
        if ($pid != ""){
            $have = $this->exe_sql_one("select amount from iknow_account_hold_v where pid='".$pid."' and code='0'");
            $ps = $this->rtprice($code);
            $need = ceil(100*round($ps[7]*$amount*1.0003,3))/100;
            if (floatval($have[0])>$need){
                $sqls = array();
                array_push($sqls,"update iknow_account_hold_v set amount=amount-".$need." where pid='".$pid."' and code='0'");
                $hold = $this->exe_sql_one("select count(*) from iknow_account_hold_v where pid='".$pid."' and code='".$code."'");
                if ($hold[0]=="0"){
                    $ppid = $this->getppid($from);
                    array_push($sqls,"insert into iknow_account_hold_v(pid,ppid,code,amount,freeze,price,hvalue) values('".$pid."','".$ppid."','".$code."',0,".$amount.",".$ps[7].",".sprintf("%.2f",$amount*$ps[7]).")");
                }
                else{
                    array_push($sqls,"update iknow_account_hold_v set amount=amount+".$amount." where pid='".$pid."' and code='".$code."'");
                }
                array_push($sqls,"insert into iknow_order_v(seqid,orderid,timestamp,pid,oper,typ,code,amount,price,status) values('".$this->buildid("S_IK")."','".$this->buildid("O_IK")."','".$this->timestamp()."','".$pid."',1,0,'".$code."',".$amount.",".$ps[7].",1)");
                if (0!=$this->task($sqls)){
                    $ret = new ikresult(1,"买入".$para[1][0].$amount."股交易失败");
                    $this->logger_db("momlib",IK_LOG_ERROR,"trade[".$pid.",buy,".$stock.",".$amount."] failed");
                }
                else{
                    $ret = new ikresult(0,"买入".$para[1][0].$amount."股交易成功");
                }
            }
            else{
                $ret = new ikresult(2,"买入".$para[1][0].$amount."股资金不足");
            }
        }
        else{
            $ret = new ikresult(3,"没有在管理的项目");
        }
        return $ret.message();
    }

    private function handle_sell_rt($para){
        if (!$this->is_open()){
            return "非交易时间";
        }
        $from = $para[0];
        $code = $this->synonym($para[1][0]);
        $amount = intval($para[1][1]);
        $pid = $this->getpid($from);
        if ($pid != ""){
            $have = $this->exe_sql_one("select amount from iknow_account_hold_v where pid='".$pid."' and code='".$code."'");
            if (intval($have[0])>=$amount){
                $ps = $this->rtprice($code);
                $got = ceil(100*round($ps[6]*$amount*(1-0.0013)))/100;
                $sqls = array();
                array_push($sqls,"update iknow_account_hold_v set amount=amount-".$amount." where pid='".$pid."' and code='".$code."'");
                array_push($sqls,"update iknow_account_hold_v set amount=amount+".$got." where pid='".$pid."' and code='0'");
                array_push($sqls,"insert into iknow_order_v(seqid,orderid,timestamp,pid,oper,typ,code,amount,price,status) values('".$this->buildid("S_IK")."','".$this->buildid("O_IK")."','".$this->timestamp()."','".$pid."',2,0,'".$code."',".$amount.",".$ps[6].",1)");
                if (0!=$this->task($sqls)){
                    $ret = new ikresult(1,"卖出".$para[1][0].$amount."股交易失败");
                    $this->logger_db("momlib",IK_LOG_ERROR,"trade[".$pid.",sell,".$code.",".$amount."] failed");
                }
                else{
                    $ret = new ikresult(0,"卖出".$para[1][0].$amount."股交易成功");
                }
            }
            else{
                $ret = new ikresult(2,"卖出".$para[1][0].$amount."股持仓数量不足");
            }
        }
        else{
            $ret = new ikresult(3,"没有在管理的项目");
        }
        return $ret.message();
    }

    private function handle_key($key,$from){
        $content = "";
        $call = $this->exe_sql_one("select callback from iknow_keys where keyword='".$key."'");
        if (count($call)>0){
            $content = call_user_func(array($this,$call[0]),$key,$from);
        }
        return $content;
    }

    private function handle_stock($stock,$from){
        $nm = $this->exe_sql_one("select name from ikbill_name where code='".$stock."'");
        if (count($nm)>0){
            $code = $stock;
            $name = $nm[0];
        }
        else{
            $cd = $this->exe_sql_one("select code from ikbill_name where name='".$stock."'");
            $code = $cd[0];
            $name = $stock;
        }
        $ps = $this->rtprice($code);
        $content = $ps[30]." ".$ps[31]."\n";
        $content = $content.$name."[".$code."]\n";
        $zdf = 100*((floatval($ps[3])-floatval($ps[2]))/floatval($ps[2]));
        $content = $content."涨跌幅：".sprintf("%.2f",$zdf)."%\n";
        $content = $content."开盘价：".$ps[1]."\n";
        $content = $content."昨收价：".$ps[2]."\n";
        $content = $content."当前价：".$ps[3]."\n";
        $content = $content."最高价：".$ps[4]."\n";
        $content = $content."最低价：".$ps[5]."\n";
        $content = $content."买一价：".$ps[6]."\n";
        $content = $content."卖一价：".$ps[7]."\n";
        $content = $content."成交量(手)：".intval(floatval($ps[8])/100)."\n";
        $content = $content."成交量(万元)：".sprintf("%.2f",floatval($ps[9])/10000)."\n";
        return $content;
    }

    private function handle_board($board,$from){
        $nm = $this->exe_sql_one("select bdname from iknow_name where bdcode='".$board."' limit 1");
        if (count($nm)>0){
            $code = $board;
            $name = $nm[0];
        }
        else{
            $cd = $this->exe_sql_one("select bdcode from iknow_name where bdname='".$board."' limit 1");
            $code = $cd[0];
            $name = $board;
        }
        $binf = $this->exe_sql_one("select date,volwy,weight,hbr,lbr,score,zdlead,zdf,vollead,volyy from ikbill_board order by date desc limit 1");
        $zdleadname = $this->exe_sql_one("select name from iknow_name where code='".$binf[6]."'");
        $volleadname = $this->exe_sql_one("select name from iknow_name where code='".$binf[8]."'");
        $content = $name."[".$code."] ".$binf[0]."\n";
        $content = $content."成交量(亿元):".sprintf("%.4f",10000*floatval($binf[1]))."\n";
        $content = $content."成交量当日占比(%):".$binf[2]."\n";
        $content = $content."高点突破率(%):".$binf[3]."\n";
        $content = $content."低点突破率(%):".$binf[4]."\n";
        $content = $content."收盘平均得分:".$binf[5]."\n";
        $content = $content."领涨股票:".$zdleadname."[".$binf[6]."]\n";
        $content = $content."涨幅(%):".$binf[7]."\n";
        $content = $content."成交最多:".$volleadname."[".$binf[8]."]\n";
        $content = $content."成交量(亿元):".$binf[9]."\n";
        return $content;
    }
    
    private function handle_event($object){
        if (array_key_exists($RX_TYPE,$this->eventhandler)){
            $content = call_user_func(array($this,$this->eventhandler[$object->Event]),$object);
        }
        else{
            $content = "";
        }
        return $content;
    }

    private function handle_subscribe($from){
        $status = $this->exe_sql_one("select status from iknow_user where extid='".$from."'");
        if (count($status)>0){
            $content = "欢迎回到冬夏科技";
        }
        else{
            $this->create_user($from);
            $content = "欢迎关注冬夏科技";
        }
        return $content;
    }

    private function handle_unsubscribe($from){
        $content = "取消关注";
        return $content;
    }

    private function create_user($openid){
        $des = "微信公众平台";
        $uid = $this->buildid('U_IK');
        $rdt = date('Y-m-d');
        $sqls = array();
        array_push($sqls,"insert into iknow_user(extid,entrance,description,uid,rdate) values('".$openid."',2,'".$des."','".$uid."','".$rdt."')");
        if (0 != $this->task($sqls)){
            $this->logger_db("momlib",IK_LOG_ERROR,"create user[".$openid."] from entrance 2 failed");
        }
    }

    private function handle_click($key,$from){
        if ($key == 'V2001_MYINFO'){
            $content = $this->handle_info($from);
        }
        elseif ($key == 'V2002_START'){
            $content = $this->handle_create($from);
        }
        elseif ($key == 'V2003_TERMINNATE'){
            $content = $this->handle_close($from);
        }
        elseif ($key == 'V1002_ABOUT_DX'){
            $content = $this->handle_dx($from);
        }
        return $content;
    }

}
?>
