<?php
define ("IK_LOG_TRACE",0);
define ("IK_LOG_DEBUG",1);
define ("IK_LOG_INFO",2);
define ("IK_LOG_WARNING",3);
define ("IK_LOG_ERROR",4);
define ("IK_LOG_CRITICAL",5);
define ("IK_BUYIN",1);
define ("IK_SELLOUT",2);
define ("IK_ROOT_UID","R_IK1982090412000010000000010000");
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

class ikwelib{
    private $db;
    private $loglevel = 2; //0:trace,1:debug,2:info,3:warning,4:error,5:critical
    private $texthandler = array("handle_trade","handle_key");

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

    private function builduid(){
        list($msec, $sec) = explode(' ',microtime());
        $id = date('YmdHis').sprintf('%.0f', floatval($msec)*100000000).mt_rand(100000,999999);
        return array("I_IK".$id,"A_IK".$id);
    }

    private function buildpid($isreal){
        list($msec, $sec) = explode(' ',microtime());
        $pre = "V";
        if ($isreal){
            $pre = "R";
        }
        return $pre.date('YmdHis').sprintf('%.0f', floatval($msec)*10).mt_rand(100,999);
    }
    
    private function buildcomid(){
        list($msec, $sec) = explode(' ',microtime());
        return date('YmdHis').sprintf('%.0f', floatval($msec)*100).mt_rand(100,999);
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
    
    private function is_oper($input,&$oper,&$stock,&$amount){
        $its = explode(' ',$input);
        if (count($its)>=3){
            if ($its[0]=="buy" or $its[0]=="买入"){
                $oper = IK_BUYIN;
            }
            elseif ($its[0]=="sell" or $its[0]=="卖出"){
                $oper = IK_SELLOUT;
            }
            else{
                return 1;
            }
            $cc = $this->exe_sql_one("select code from iknow_name where code='".$its[1]."'");
            if (count($cc)>0){
                $stock = $its[1];
            }
            else{
                $nc = $this->exe_sql_one("select code from iknow_name where name='".$its[1]."'");
                if (count($nc)>0){
                    $stock = $nc[0];
                }
                else{
                    return 1;
                }
            }
            $amt = intval(intval($its[2])/100);
            if ($amt != 0){
                $amount = $amt*100;
            }
            else{
                return 1;
            }
            return 0;
        }
        return 1;
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

    public function handle_msg($poststr){
        if (!empty($poststr)){
            $this->logger_db("welib",IK_LOG_DEBUG,$poststr);
            $obj = simplexml_load_string($poststr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $RX_TYPE = trim($obj->MsgType);
            switch ($RX_TYPE){
                case "text":
                    return $this->handle_text($obj);
                case "event":
                    return $this->handle_event($obj);
                default:
                    return $this->transmit_text($obj, "暂不支持[".$RX_TYPE."]类型消息");
            }
        }
        else{
            return "";
        }
    }

    private function handle_text($object){
        foreach($this->texthandler as $handler){
            $content = call_user_func(array($this,$handler),$object->Content,$object->FromUserName);
            if ("" != $content){
                break;
            }
        }
        $result = $this->transmit_text($object->FromUserName, $object->ToUserName,$content);
        return $result;
    }

    private function handle_trade($key,$from){
        $content = "";
        if ($this->is_oper($key,$oper,$stock,$amount)==0){
            if ($this->is_open()){ //交易时间
                $content = $this->trade($from,$oper,$stock,$amount);
            }
            else{
                $content = "非交易时间";
            }
        }
        return $content;
    }

    private function buyin($pid,$uid_i,$stock,$amount){
        $have = $this->exe_sql_one("select cash from iknow_invest_account_v where uid_i='".$uid_i."'");
        $ps = $this->rtprice($stock);
        $need = ceil(100*round($ps[7]*$amount*1.0003,3))/100;
        if (floatval($have[0])>$need){
            $sqls = array();
            array_push($sqls,"update iknow_invest_account_v set cash=cash-".$need." where uid_i='".$uid_i."'");
            array_push($sqls,"insert into iknow_order_v(seqid,orderid,timestamp,pid,oper,typ,code,amount,price,status) values('".$this->buildcomid()."','".$this->buildcomid()."','".$this->timestamp()."','".$pid."',1,0,'".$stock."',".$amount.",".$ps[7].",1)");
            $hv = $this->exe_sql_one("select count(*) from iknow_project_hold_v where pid='".$pid."' and code='".$stock."'");
            if (intval($hv[0])>0){
                array_push($sqls,"update iknow_project_hold_v set freeze=freeze+".$amount." where pid='".$pid."' and code='".$stock."'");
            }
            else{
                array_push($sqls,"insert into iknow_project_hold_v(pid,code,freeze) values('".$pid."','".$stock."',".$amount.")");
            }
            if (0!=$this->task($sqls)){
                $ret = new ikresult(1,"买入".$name[0].$amount."股交易失败");
                $this->logger_db("welib",IK_LOG_ERROR,"trade[".$pid.",".$oper.",".$stock.",".$amount."] failed");
            }
            else{
                $ret = new ikresult(0,"买入".$name[0].$amount."股交易成功");
            }
        }
        else{
            $ret = new ikresult(2,"买入".$name[0].$amount."股资金不足");
        }
        return $ret;
    }

    private function sellout($pid,$uid_i,$stock,$amount,$comi=true){
        $have = $this->exe_sql_one("select amount from iknow_project_hold_v where pid='".$pid."' and code='".$stock."'");
        if (intval($have[0])>=$amount){
            $ps = $this->rtprice($stock);
            $got = ceil(100*round($ps[6]*$amount*(1-0.0013)))/100;
            $sqls = array();
            array_push($sqls,"update iknow_project_hold_v set amount=amount-".$amount." where pid='".$pid."' and code='".$stock."'");
            array_push($sqls,"update iknow_invest_account_v set cash=cash+".$got." where uid_i='".$uid_i."'");
            array_push($sqls,"insert into iknow_order_v(seqid,orderid,timestamp,pid,oper,typ,code,amount,price,status) values('".$this->buildcomid()."','".$this->buildcomid()."','".$this->timestamp()."','".$pid."',2,0,'".$stock."',".$amount.",".$price.",1)");
            if (0!=$this->task($sqls,$comi)){
                $ret = new ikresult(1,"卖出".$name[0].$amount."股交易失败");
                $this->logger_db("welib",IK_LOG_ERROR,"trade[".$pid.",".$oper.",".$stock.",".$amount."] failed");
            }
            else{
                $ret = new ikresult(0,"卖出".$name[0].$amount."股交易成功");
            }
        }
        else{
            $ret = new ikresult(2,"卖出".$name[0].$amount."股持仓数量不足");
        }
        return $ret;
    }

    private function trade($from,$oper,$stock,$amount){
        $ids = $this->exe_sql_one("select iknow_project_v.pid,iknow_user.uid_i from iknow_project_v,iknow_user where iknow_user.extid='".$from."' and iknow_user.uid_i=iknow_project_v.uid_i");
        if (count($ids)>0){
            $name = $this->exe_sql_one("select name from iknow_name where code='".$stock."'");
            if ($oper==IK_BUYIN){
                $ret = $this->buyin($ids[0],$ids[1],$stock,$amount);
            }
            elseif ($oper==IK_SELLOUT){
                $ret = $this->sellout($ids[0],$ids[1],$stock,$amount);
            }
            else{
                $ret = new ikresult(1,"指令错误");
            }
        }
        else{
            $ret = new ikresult(2,"用户非法");
        }
        return $ret.message();
    }

    private function handle_key($key,$from){
        $content = $key." 是什么意思？";
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
        switch ($object->Event){
            case "subscribe":
                $content = $this->handle_subscribe($object->FromUserName);
                break;
            case "unsubscribe":
                $content = $this->handle_unsubscribe($object->FromUserName);
                break;
            case "SCAN":
                $content = $this->handle_scan($object->EventKey,$object->Ticket,$object->FromUserName);
                break;
            case "CLICK":
                $content = $this->handle_click($object->EventKey,$object->FromUserName);
                break;
            case "LOCATION":
                $content = $this->handle_location($object->Latitude,$object->Longitude,$object->Precision,$object->FromUserName);
                break;
            case "VIEW":
                $content = $this->handle_view($object->EventKey,$object->FromUserName);
                $this->logger_db("welib",IK_LOG_DEBUG,"view event[".$content."]");
                break;
            default:
                $content = $object->Event." 是什么？";
                break;
        }
        $result = $this->transmit_text($object->FromUserName,$object->ToUserName,$content);
        return $result;
    }

    private function handle_view($url,$from){
        $this->logger_db("welib",IK_LOG_DEBUG,"view event[".$url."]");
        $content = $url;
        return $content;
    }

    private function handle_subscribe($from){
        $status = $this->exe_sql_one("select status from iknow_user where extid='".$from."'");
        if (count($status)>0){
            $this->task(array("update iknow_user_we set status=1 where extid='".$from."'"));
            $content = "欢迎回到冬夏科技";
        }
        else{
            $this->create_user($from);
            $content = "欢迎关注冬夏科技";
        }
        return $content;
    }

    private function create_user($openid){
        $des = "微信公众平台";
        $uid = $this->builduid();
        $rdt = date('Y-m-d');
        $sqls = array();
        array_push($sqls,"insert into iknow_user(extid,entrance,description,uid_i,uid_a,rdate,status) values('".$openid."',3,'".$des."','".$uid[0]."','".$uid[1]."','".$rdt."',1)");
        array_push($sqls,"insert into iknow_invest_account_v(uid_i) values('".$uid[0]."')");
        array_push($sqls,"insert into iknow_account_info(uid_i,uid_a,status) values('".$uid[0]."','".$uid[1]."',0)");
        if (0 != $this->task($sqls)){
            $this->logger_db("welib",IK_LOG_ERROR,"create user[".$openid."] from entrance 3 failed");
        }
    }

    private function handle_unsubscribe($from){
        $content = "取消关注";
        $status = $this->exe_sql_one("select status from iknow_user_we where openid='".$from."'");
        if (count($status)>0){
            $this->task(array("update iknow_user_we set status=0 where openid='".$from."'"));
        }
        else{
            $this->logger_db("welib",IK_LOG_WARNING,"handle_unsubscribe user[".$from."] not exist");
        }
        return $content;
    }

    private function handle_scan($scenev,$ticket,$from){
        $content = "扫描场景 ".$scenev." ".$ticket;
        return $content;
    }

    private function handle_location($latitude,$longitude,$precision,$from){
        $content = "上传位置：纬度 ".$latitude.";经度 ".$longitude.";精度 ".$precision;
        return $content;
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
    
    private function project_v_info($from){
        $uid = $this->exe_sql_one("select uid_i from iknow_user where extid='".$from."'");
        $pinf = $this->exe_sql_one("select pid,cash,freeze from iknow_invest_account_v where uid_i='".$uid[0]."'");
        $holds = $this->exe_sql_batch("select code,amount+freeze from iknow_project_hold_v where pid='".$pinf[0]."'");
        $holdinf = "";
        $dttm = "";
        $sval = 0;
        foreach($holds as $hold){
            $nm = $this->exe_sql_one("select name from iknow_name where code='".$hold[0]."'");
            $ps = $this->rtprice($hold[0]);
            $holdinf = $holdinf.$nm[0]."[".$hold[0]."] ".$ps[3]." ".$hold[1]."\n";
            $sval = $sval + floatval($ps[3])*floatval($hold[1]);
            if (count($dttm)==0){
                $dttm = $ps[30]." ".$ps[31];
            }
        }
        $content = "项目[".$pinf[0]."] ".$dttm."\n";
        $content = $content."资金(总):".sprintf("%.2f",floatval($pinf[1])+floatval($pinf[2]))."\n";
        $content = $content."资金(可用):".$pinf[1]."\n";
        $content = $content."持仓信息\n";
        $content = $content.$holdinf."\n";
        $content = $content."股票价值:".sprintf("%.2f",round($sval,2))."\n";
        $content = $content."总价值:".sprintf("%.2f",round(floatval($pinf[1])+floatval($pinf[2])+$sval,2))."\n";
        return $content;
    }

    private function project_r_info($from){
        $uid = $this->exe_sql_one("select uid_a from iknow_user where extid='".$from."'");
        $pinf = $this->exe_sql_one("select pid,cash,freeze from iknow_invest_account_r where uid_a='".$uid[0]."'");
        $holds = $this->exe_sql_batch("select code,amount+freeze from iknow_project_hold_r where pid='".$pinf[0]."'");
        $holdinf = "";
        $dttm = "";
        $sval = 0;
        foreach($holds as $hold){
            $nm = $this->exe_sql_one("select name from iknow_name where code='".$hold[0]."'");
            $ps = $this->rtprice($hold[0]);
            $holdinf = $holdinf.$nm[0]."[".$hold[0]."] ".$ps[3]." ".$hold[1]."\n";
            $sval = $sval + floatval($ps[3])*floatval($hold[1]);
            if (count($dttm)==0){
                $dttm = $ps[30]." ".$ps[31];
            }
        }
        $content = "项目[".$$pinf[0]."] ".$dttm."\n";
        $content = $content."资金(总):".sprintf("%.2f",floatval($pinf[1])+floatval($pinf[2]))."\n";
        $content = $content."资金(可用):".sprintf("%.2f",floatval($pinf[1]))."\n";
        $content = $content."持仓信息\n";
        $content = $content.$holdinf."\n";
        $content = $content."股票价值:".sprintf("%.2f",round($sval,2))."\n";
        $content = $content."总价值:".sprintf("%.2f",round(floatval($pinf[1])+floatval($pinf[2])+$sval,2))."\n";
    }

    private function handle_info($from){
        if (!$this->uservalid($from)){
            $this->create_user($from);
        }
        $st = $this->exe_sql_one("select iknow_account_info.status from iknow_account_info,iknow_user where iknow_user.extid='".$from."' and iknow_account_info.uid_i=iknow_user.uid_i");
        if ($st[0]=="1"){
            $content = $this->project_v_info($from);
        }
        elseif ($st[0]=="2"){
            $content = $this->project_r_info($from);
        }
        else{
            $content = "还没有在管理中的项目,去申请一个吧!";
        }
        return $content;
    }

    private function handle_dx($from){
        return "冬夏科技[".$from."]";
    }

    private function handle_create($from){
        if (!$this->uservalid($from)){
            $this->create_user($from);
        }
        $st = $this->exe_sql_one("select iknow_account_info.status from iknow_account_info,iknow_user where iknow_user.extid='".$from."' and iknow_account_info.uid_i=iknow_user.uid_i");
        if ($st[0]=="0"){
            if (0 == $this->create_project_v($from)){
                return "项目创建成功,请在\"我的信息\"中查看";
            }
            else{
                return "项目创建失败";
            }
        }
        else{
            return "项目正在进行中,请在\"我的信息\"中查看";
        }
    }

    private function create_project_v($from){
        $pid = $this->buildpid(false);
        $td = date('Y-m-d');
        $uinf = $this->exe_sql_one("select uid_i,limper,retmax,settlemin from iknow_user where extid='".$from."'");
        $rl = floatval($uinf[1])*(1-floatval($uinf[2]));
        $sl = floatval($uinf[1])*(1+floatval($uinf[3]));
        $sqls = array();
        array_push($sqls,"insert into iknow_project_v(pid,uid_i,edate,retline,settleline,baseline,peak) values('".$pid."','".$uinf[0]."','".$td."',".$rl.",".$sl.",".$uinf[1].",".$uinf[1].")");
        array_push($sqls,"update iknow_invest_account_v set pid='".$pid."',cash=".$uinf[1]);
        array_push($sqls,"update iknow_account_info set status=1");
        return $this->task($sqls);
    }

    private function handle_close($from){
        $ids = $this->exe_sql_one("select iknow_project_v.pid,iknow_user.uid_i from iknow_project_v,iknow_user where iknow_user.extid='".$from."' and iknow_user.uid_i=iknow_project_v.uid_i");
        $fz = $this->exe_sql_one("select avg(freeze) from iknow_project_hold_v where pid='".$ids[0]."'");
        if (intval($fz[0])>0){
            $content = "持仓中有不可卖股票,不能关闭项目";
        }
        else{
            $content = "项目[".$ids[0]."]关闭操作成功";
            $hold = $this->exe_sql_batch("select code,amount from iknow_project_hold_v where pid='".$ids[0]."'");
            foreach($hold as $item){
                $ret = $this->sellout($ids[0],$ids[1],$item[0],intval($item[1]),false);
                if ($ret.errcode()!=0){
                    return $ret.errmsg();
                }
            }
            $cash = $this->exe_sql_one("select cash from iknow_invest_account_v where uid_i='".$uid_i."'");
            $sr = $this->exe_sql_one("select sharerate from iknow_user where extid='".$from."'");
            $ls = $this->exe_sql_one("select settleline,baseline from iknow_project_v where pid='".$ids[0]."'");
            $bl = floatval($ls[1]);
            $sl = floatval($ls[0]);
            $cash = floatval($cash[0]);
            $sr = floatval($sr[0]);
            $ben = $cash-$bl;
            $sben = $sl-$bl;
            $sqls = array();
            if ($ben>0){
                if ($ben>=$sben){
                    $got = round($ben*$sr,2);
                    $left = $ben-$got;
                }
                else{
                    $left = round($ben*$sr,2);
                    $got = $ben-$left;
                }
                $allv = $this->exe_sql_one("select value from iknow_global where name='money_v'");
                $allv = floatval($allv[0])+$ben;
                array_push($sqls,"update iknow_global set value=".$allv." where name='money_v'");
                array_push($sqls,"update iknow_user set money_v=money_v+".$got." where extid='".$from."'");
                array_push($sqls,"update iknow_user set money_v=money_v+".$left." where extid='root'");
                array_push($sqls,"insert into iknow_money_record(seqid,timestamp,tag,currency,amount,toid) values('".$this->buildcomid()."','".$this->timestamp()."',1,1,".$got.",".$ids[1]."')");
                array_push($sqls,"insert into iknow_money_record(seqid,timestamp,tag,currency,amount,toid) values('".$this->buildcomid()."','".$this->timestamp()."',1,1,".$left.",'".IK_ROOT_UID."')");
                array_push($sqls,"update iknow_invest_account_v set cash=0,freeze=0,worth=0,pid='".$ids[0]."' where uid_i='".$ids[1]."'");
                array_push($sqls,"update iknow_account_info set status=0 where uid_i='".$ids[1]."'");
            }
            else{
                array_push($sqls,"update iknow_invest_account_v set cash=0,freeze=0,worth=0,pid='".$ids[0]."' where uid_i='".$ids[1]."'");
                array_push($sqls,"update iknow_account_info set status=0 where uid_i='".$ids[1]."'");
            }
            if (0 != $this->task($sqls)){
                $this->logger_db("welib",IK_LOG_ERROR,"close project[".$ids[0]."] failed");
                $content = "项目[".$ids[0]."]关闭操作失败";
            }
        }
        return $content;
    }
}
?>
