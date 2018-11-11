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
        $this->loglevel = 1;
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
        /*if (!empty($poststr)){
            $this->logger_db("welib",IK_LOG_DEBUG,$poststr);
            $this->logger_db("welib",IK_LOG_DEBUG,"before");
            $obj = simplexml_load_string($poststr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $this->logger_db("welib",IK_LOG_DEBUG,"after");
            $RX_TYPE = trim($obj->MsgType);
            $this->logger_db("welib",IK_LOG_DEBUG,"message type[".$obj->MsgType."]");
            switch ($RX_TYPE){
                case "text":
                    $res = $this->handle_text($obj);
                case "event":
                    $res = $this->handle_event($obj);
                default:
                    $res = $this->transmit_text($obj, "暂不支持[".$RX_TYPE."]类型消息");
            }
        }
        else{
            return "";
        }*/
        $res = "<xml><ToUserName><![CDATA[oOvJ0w3ypLp4xkgA2fV6EOhJDDwo]]></ToUserName><FromUserName><![CDATA[gh_29e07ff52189]]></FromUserName><CreateTime>".time()."</CreateTime><MsgType><![CDATA[link]]></MsgType><Title>< ![CDATA[方大炭素] ]></Title><Description>< ![CDATA[参考信息] ]></Description><Url>< ![CDATA[http://www.boardgame.org.cn/ikitem.php?code=600516] ]></Url></xml>";
        return $res;
    }

    private function handle_text($object){
        $result = "<xml><ToUserName><![CDATA[".$object->FromUserName."]]></ToUserName><FromUserName><![CDATA[".$object->ToUserName."]]></FromUserName><CreateTime>".time()."</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[http://www.boardgame.org.cn/ikitem.php?code=".$object->Content."]]></Content></xml>";
        /*$result = "<xml><ToUserName>< ![CDATA[".$object->FromUserName."] ]></ToUserName><FromUserName>< ![CDATA[".$object->ToUserName."] ]></FromUserName><CreateTime>".time()."</CreateTime><MsgType>< ![CDATA[link] ]></MsgType><Title>< ![CDATA[".$object->Content."] ]></Title><Description>< ![CDATA[参考信息] ]></Description><Url>< ![CDATA[http://www.boardgame.org.cn/ikitem.php?code=".$object->Content."] ]></Url></xml>";*/
        /*$result = sprintf($texttpl,$from,$to,time(),$content);
        return $result;
        foreach($this->texthandler as $handler){
            $content = call_user_func(array($this,$handler),$object->Content,$object->FromUserName);
            if ("" != $content){
                break;
            }
        }
        $result = $this->transmit_text($object->FromUserName, $object->ToUserName,$content);*/
        $this->logger_db("welib",IK_LOG_INFO,$result);
        return $result;
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
}
?>
