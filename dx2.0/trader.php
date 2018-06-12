<?php
require "../phplib/dx.php";

$ikt = new hytrader();
$ikt->handle_msg();

class traderreturncode{
    const SUCCESS = 0;
    const ACTION_UNKNOWN=10000;
    const USERID_IS_NOT_SET=10001;
    const CODE_IS_NOT_SET=10002;
    const AMOUNT_IS_NOT_SET=10003;
    const ACTION_IS_NOT_SET=10004;
    const PRICE_IS_NOT_SET=10005;
    const ORDERID_IS_NOT_SET=10006;
    const LIST_IS_NOT_SET=10007;
    const USER_NOT_EXIST=11001;
    const ORDER_NOT_EXIST=11002;
    const MARKET_CLOSE=12000;
    const SYSTEM_ERROR=90000;
    
    public static function to_json($retcode){
        return json_encode(array("retcode"=>$retcode));
    }
    
    public static function to_json_msg($retcode,$retmsg){
        return json_encode(array("retcode"=>$retcode,"retmsg"=>$retmsg));
    }
}

class hytrader{
    private $dx;
    private $msghandler = array();

    function __construct(){
        $this->dx = new dxlib();
        if ($this->dx->isok() and $this->dx->select_db("trader")){
            $this->register_handler("start","handle_start");
            $this->register_handler("flush","handle_flush");
        }
    }

    function __destruct(){
    }
    
    private function register_handler($action,$handler){
        $this->msghandler[$action]=$handler;
    }

    public function handle_msg(){
        parse_str($_SERVER["QUERY_STRING"],$param);
        //$poststr = $GLOBALS["HTTP_RAW_POST_DATA"];//json or xml
        //$obj = json_decode($poststr);
        if (array_key_exists($param["action"],$this->msghandler)){
            $response = call_user_func(array($this,$this->msghandler[$param["action"]]),$param);
        }
        else{
            $response = traderreturncode::to_json_msg(traderreturncode::ACTION_UNKNOWN,"operation[".$param["action"]."] invalid");
        }
        echo $response;
    }
    
    /****************
    return value
    0：股票名字；
    1：今日开盘价；
    2：昨日收盘价；
    3：当前价格；
    4：今日最高价；
    5：今日最低价；
    6：竞买价，即“买一”报价；
    7：竞卖价，即“卖一”报价；
    8：成交的股票数，由于股票交易以一百股为基本单位，所以在使用时，通常把该值除以一百；
    9：成交金额，单位为“元”，为了一目了然，通常以“万元”为成交金额的单位，所以通常把该值除以一万；
    10：“买一”申请量 11：“买一”报价
    12：“买二申请量” 13：”26.90″，“买二”报价
    14：“买三申请量” 15：”26.89″，“买三”报价
    16：“买四申请量” 17：”26.88″，“买四”报价
    18：“买五申请量” 19：”26.87″，“买五”报价
    20：“卖一”申报3100股，即31手；21：“卖一”报价
    (22, 23), (24, 25), (26,27), (28, 29)分别为“卖二”至“卖四的情况”
    30：”2008-01-11″，日期；
    31：”15:05:32″，时间；
    ****************/
    private function rtprice($codes){
        $url = "";
        foreach($codes as $code){
            $url = $url.$code.",";
        }
        $url = "http://hq.sinajs.cn/list=".substr($url,0,-1);
        //echo "URL:".$url;
        $data = file_get_contents($url);
        $lines = explode("\n",$data);
        $hq = array();
        //$today = date("Y-m-d");
        $i = 0;
        foreach($lines as $line){
            $con = explode("\"",$line);
            $ps = explode(",",$con[1]);
            if (floatval($ps[8])>0){
                $open = $ps[1];
                $high = $ps[4];
                $low = $ps[5];
                $close = $ps[3];
                $buy = $ps[7];
                $sell = $ps[6];
                $lastclose = $ps[2];
                $dt = $ps[30];
                $time = $ps[31];
                array_push($hq,array(substr($codes[$i],2),$open,$high,$low,$close,$buy,$sell,$lastclose,$dt,$time));
            }
            $i++;
        }
        return $hq;
    }
    
    private function check_para($param,$force){
        foreach($force as $val){
            if (!isset($param[$val])){
                return false;
            }
        }
        return true;
    }
    
    private function handle_start($param){
        $date = "";
        if (isset($param["date"])){
            $date = $param["date"];
        }
        $json = null;
        $dt = $this->dx->exe_sql_one("select date from trader_stockset order by date desc limit 1");
        if (count($dt)>0 and $date!=$dt[0]){
            $ja = array();
            $setdate = $dt[0];
            $ssdata = $this->dx->exe_sql_batch("select code,name,pinyin from trader_stockset where date='".$setdate."'");
            $sset = array();
            foreach($ssdata as $row){
                array_push($sset,array("code"=>$row[0],"name"=>$row[1],"pinyin"=>$row[2]));
            }
            $ja["retcode"] = traderreturncode::SUCCESS;
            if (count($sset)>0){
                $ja["setdate"] = $setdate;
                $ja["sset"] = $sset;
            }
            $json = json_encode($ja);
        }
        else{
            $json = traderreturncode::to_json(traderreturncode::SUCCESS);
        }
        return $json;
    }

    private function handle_flush($param){
        $json = null;
        if (isset($param["list"])){
            $codes = explode(",",$param["list"]);
            $hq = $this->rtprice($codes);
            $ja = array();
            $hqay = array();
            foreach($hq as $row){
                array_push($hqay,array("code"=>$row[0],"open"=>$row[1],"high"=>$row[2],"low"=>$row[3],"close"=>$row[4],"buy"=>$row[5],"sell"=>$row[6],"lastclose"=>$row[7],"date"=>$row[8],"time"=>$row[9]));
            }
            $ja["retcode"] = traderreturncode::SUCCESS;
            if (count($hqay)>0){
                $ja["hq"] = $hqay;
            }
            $json = json_encode($ja);
        }
        else{
            $json = traderreturncode::to_json(traderreturncode::LIST_IS_NOT_SET);
        }
        return $json;
    }

    private function handle_create($obj){
        if (!property_exists($obj,"userid")){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $uname = $obj->userid;
        $ext = $this->exe_sql_one("select count(*) from trader_user where userid='".$uname."'");
        if (count($ext)>0){
            return array("retcode"=>"10010","retmsg"=>"user".$uname."] has been exist");
        }
        if ($this->task(array("insert into trader_user(userid,nickname,rdate) values('".$uname."','".$obj->nickname."',".date('Y-m-d')."')"))==0){
            return array("retcode"=>"0","retmsg"=>"successfully");
        }
        return array("retcode"=>"10002","retmsg"=>"create user failed[SYSTEM ERROR]");
    }

    private function handle_deposit($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"amount"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        if (floatval($obj->amount)<=0){
            return array("retcode"=>"10003","retmsg"=>"parameter error");
        }
        $uname = $obj->userid;
        $ext = $this->exe_sql_one("select count(*) from trader_user where userid='".$uname."'");
        if (count($ext)==0){
            return array("retcode"=>"10011","retmsg"=>"user[".$uname."] not exist");
        }
        if ($this->task(array("update trader_user set cash=cash+".$obj->amount." where userid='".$uname."'"))==0){
            return array("retcode"=>"0","retmsg"=>"successfully");
        }
        return array("retcode"=>"10002","retmsg"=>"deposit failed[SYSTEM ERROR]");
    }

    private function handle_draw($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"amount"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $uname = $obj->userid;
        $have = $this->exe_sql_one("select cash from trader_user where userid='".$uname."'");
        if (count($have)==0){
            return array("retcode"=>"10003","retmsg"=>"user[".$uname."] not exist");
        }
        else{
            if (intval($have[0])<intval($obj->amount)){
                return array("retcode"=>"10004","retmsg"=>"user[".$uname."] cash not enough");
            }
            else{
                if ($this->task(array("update trader_user set cash=cash-".$obj->amount." where userid='".$uname."'"))==0){
                    return array("retcode"=>"0","retmsg"=>"successfully");
                }
            }
        }
        return array("retcode"=>"10002","retmsg"=>"draw failed[SYSTEM ERROR]");
    }

    private function handle_put($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"otype") and property_exists($obj,"code") and property_exists($obj,"amount") and property_exists($obj,"price"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $st = $this->exe_sql_one("select value from trader_global where name='market'");
        if ($st[0]=="4"){ //扎帐时间不能挂单
            return array("retcode"=>"10020","retmsg"=>"current time user cannot put order");
        }
        $st = $this->exe_sql_one("select status from trader_code where code='".$obj->code."'");
        if ($st[0]!="1"){ //股票停牌或注销
            return array("retcode"=>"10021","retmsg"=>"user cannot put order for code[".$obj->code."]");
        }
        $uname = $obj->userid;
        $have = $this->exe_sql_one("select cash from trader_user where userid='".$uname."'");
        if (count($have)>0){
            $need = floatval($obj->price)*floatval($obj->amount)*100;//amount单位:手
            if (intval($have[0])<$need){
                return array("retcode"=>"10004","retmsg"=>"user[".$uname."] cash not enough");
            }
            else{
                $oid = $this->buildid("O_TD");
                $attrs = "orderid,userid,putdate,puttime,otype,code,amount,putprice,freeze";
                $attrv = "'".$oid."','".$uname."','".date('Y-m-d')."','".date('H:i:s')."',".$obj->otype.",".$obj->code.",".($obj->amount*100).",".$obj->price.",".$need;
                if (property_exists($obj,"win")){
                    $attrs = $attrs.",win";
                    $attrv = $attrv.",".$obj->win;
                }
                if (property_exists($obj,"lose")){
                    $attrs = $attrs.",lose";
                    $attrv = $attrv.",".$obj->lose;
                }
                $sqls = array();
                array_push($sqls,"insert into trader_order_put(".$attrs.") values(".$attrv.")");
                array_push($sqls,"update trader_user set cash=cash-".$need." where userid='".$userid."'");
                if (0 == $this->task($sqls)){
                    return array("retcode"=>"0","retmsg"=>"successfully");
                }
                return array("retcode"=>"10002","retmsg"=>"put failed userid[".$uname."]");
            }
        }
        return array("retcode"=>"10003","retmsg"=>"user[".$uname."] not exist");
    }

    private function handle_cancel($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"userid"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $st = $this->exe_sql_one("select value from trader_global where name='market'");
        if ($st[0]=="4"){ //扎帐时间不能撤单
            return array("retcode"=>"10020","retmsg"=>"current time user cannot put order");
        }
        $uname = $obj->userid;
        $putorder = $this->exe_sql_one("select userid,putdate,puttime,otype,code,amount,putprice,freeze from trader_order_put where orderid='".$obj->orderid."'");
        if (count($putorder)>0){
            $sqls = array();
            array_push($sqls,"insert into trader_order_cancel(orderid,userid,putdate,puttime,canceldate,canceltime,otype,code,amount,putprice) values('".$obj->orderid."','".$uname."','".$putorder[1]."','".$putorder[2]."','".date('Y-m-d')."','".date('H:i:s')."',".$putorder[3].",'".$putorder[4]."',".$putorder[5].",".$putorder[6].")");
            array_push($sqls,"delete from trader_order_put where orderid='".$obj->orderid."'");
            array_push($sqls,"update trader_user set cash=cash+".$putorder[7]." where userid='".$uname."'");
            if (0 == $this->task($sqls)){
                return array("retcode"=>"0","retmsg"=>"successfully");
            }
            return array("retcode"=>"10002","retmsg"=>"cancel failed,order[".$obj->orderid."]");
        }
        return array("retcode"=>"10004","retmsg"=>"order[".$obj->orderid."] not exist");
    }
    
    private function handle_open($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"otype") and property_exists($obj,"code") and property_exists($obj,"amount"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $st = $this->exe_sql_one("select value from trader_global where name='market'");
        if ($st[0]!="1" and $st[0]!="2"){ //非交易时间
            return array("retcode"=>"10020","retmsg"=>"current time user cannot open order");
        }
        $st = $this->exe_sql_one("select status from trader_code where code='".$obj->code."'");
        if ($st[0]!="1"){ //股票停牌或注销
            return array("retcode"=>"10021","retmsg"=>"user cannot put order for code[".$obj->code."]");
        }
        $uname = $obj->userid;
        $have = $this->exe_sql_one("select cash from trader_user where userid='".$uname."'");
        if (count($have)>0){
            $ps = $this->rtprice($obj->code);
            if ($obj->otype=="1"){  //做多
                $need = floatval($ps[7])*floatval($obj->amount)*100;
                $price = $ps[7];
            }  // 做空
            else{
                $need = floatval($ps[6])*floatval($obj->amount)*100;
                $price = $ps[6];
            }
            if (floatval($have[0])>=$need){
                $oid = $this->buildid("O_TD");
                $attrs = "orderid,userid,putdate,puttime,opendate,opentime,otype,tag,code,amount,openprice";
                $attrv = "'".$oid."','".$uname."','".date('Y-m-d')."','".date('H:i:s')."','".date('Y-m-d')."','".date('H:i:s')."',".$obj->otype.",".$obj->tag.",".$obj->code.",".($obj->amount*100).",".$obj->price;
                if (property_exists($obj,"win")){
                    $attrs = $attrs.",win";
                    $attrv = $attrv.",".$obj->win;
                }
                if (property_exists($obj,"lose")){
                    $attrs = $attrs.",lose";
                    $attrv = $attrv.",".$obj->lose;
                }
                $sqls = array();
                array_push($sqls,"insert into trader_order_open(".$attrs.") values(".$attrv.")");
                array_push($sqls,"update trader_user set cash=cash-".$need." where userid='".$userid."'");
                if (0 == $this->task($sqls)){
                    return array("retcode"=>"0","retmsg"=>"successfully");
                }
                return array("retcode"=>"10002","retmsg"=>"open failed userid[".$uname."]");
            }
            return array("retcode"=>"10004","retmsg"=>"user[".$uname."] cash not enough");
        }
        return array("retcode"=>"10003","retmsg"=>"user[".$uname."] not exist");
    }
    
    private function handle_close($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"orderid"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $st = $this->exe_sql_one("select value from trader_global where name='market'");
        if ($st[0]!="1" and $st[0]!="2"){ //非交易时间
            return array("retcode"=>"10020","retmsg"=>"current time user cannot close order");
        }
        $uname = $obj->userid;
        $openorder = $this->exe_sql_one("select userid,opendate,opentime,otype,code,amount,openprice from trader_order_open where orderid='".$obj->orderid."'");
        if (count($openorder)>0){
            $ps = $this->rtprice($openorder[4]);
            if ($obj->otype=="1"){  //多单
                $gain = floatval($ps[6])*floatval($openorder[5]);
                $price = $ps[6];
            }  // 空单
            else{
                $gain = floatval($ps[7])*floatval($openorder[5]);
                $price = $ps[7];
            }
            $commission = $gain*0.0015;
            $earn = $gain-(floatval($openorder[5])*floatval($openorder[6]))-$commission;
            $sqls = array();
            array_push($sqls,"insert into trader_order_close(orderid,userid,opendate,opentime,closedate,closetime,otype,code,amount,openprice,closeprice,commission,earn) values('".$obj->orderid."','".$uname."','".$openorder[1]."','".$openorder[2]."','".date('Y-m-d')."','".date('H:i:s')."',".$openorder[3].",'".$openorder[4]."',".$openorder[5].",".$openorder[6].",".$price.",".sprintf("%.3f",$commission).",".$earn.")");
            array_push($sqls,"delete from trader_order_open where orderid='".$obj->orderid."'");
            if ($earn>0){
                array_push($sqls,"update trader_user set cash=cash+".sprintf("%.3f",$earn)." where userid='".$uname."'");
            }
            else{
                array_push($sqls,"update trader_user set cash=cash-".sprintf("%.3f",abs($earn))." where userid='".$uname."'");
            }
            if (0 == $this->task($sqls)){
                return array("retcode"=>"0","retmsg"=>"successfully");
            }
            return array("retcode"=>"10002","retmsg"=>"cancel failed,order[".$obj->orderid."]");
        }
        return array("retcode"=>"10003","retmsg"=>"order[".$obj->orderid."] not exist");
    }

    private function handle_set($obj){
        if (!(property_exists($obj,"userid") and property_exists($obj,"orderid") and (property_exists($obj,"win") or property_exists($obj,"lose")))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $st = $this->exe_sql_one("select value from trader_global where name='market'");
        if ($st[0]=="4"){ //扎帐时间不能设置止盈止损
            return array("retcode"=>"10020","retmsg"=>"current time user cannot set order");
        }
        $openorder = $this->exe_sql_one("select userid,win,lose from trader_order_open where userid='".$obj->orderid."'");
        if (count($openorder)>0){
            if ($openorder[0]==$obj->userid){
                $setv = "update trader_order_open set ";
                if (property_exists($obj,"win")){
                    $setv = $setv."win=".$obj->win;
                }
                if (property_exists($obj,"lose")){
                    if (property_exists($obj,"win")){
                        $setv = $setv.",";
                    }
                    $setv = $setv."lose=".$obj->lose;
                }
                $sql = $setv." where orderid='".$obj->orderid."'";
                if (0 == $this->task(array($sql))){
                    return array("retcode"=>"0","retmsg"=>"successfully");
                }
                return array("retcode"=>"10002","retmsg"=>"set failed,order[".$openorder[0]."]");
            }
            return array("retcode"=>"10005","retmsg"=>"order[".$openorder[0]."],user[".$obj->userid."] error");
        }
        return array("retcode"=>"10003","retmsg"=>"order[".$openorder[0]."] not exist");
    }
    
    private function handle_query($obj){
        if (!(property_exists($obj,"userid"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $acct = $this->exe_sql_one("select cash,value from trader_user where userid='".$obj->userid."'");
        if (count($acct)==0){
            return array("retcode"=>"10003","retmsg"=>"user[".$obj->userid."] not exist");
        }
        $freeze = $this->exe_sql_one("select sum(freeze) from trader_order_put where userid='".$obj->userid."'");
        if (count($freeze)==0){
            $freeze = "0";
        }
        else{
            $freeze = $freeze[0];
        }
        $data = $this->exe_sql_batch("select orderid,opendate,opentime,otype,win,lose,code,amount,openprice,benefit where userid='".$obj->userid."'");
        $hold = array();
        if (count($data)>0){
            foreach($data as $row){
                array_push($hold,$row);
            }
            return array("userid"=>$obj->userid,"cash"=>$acct[0],"value"=>$acct[1],"freeze"=>$freeze,"hold"=>$hold);
        }
        return array("userid"=>$obj->userid,"cash"=>$acct[0],"value"=>$acct[1],"freeze"=>$freeze);
    }
    
    private function handle_inquiry($obj){
        if (!(property_exists($obj,"userid"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        $data = $this->exe_sql_batch("select orderid,opendate,opentime,closedate,closetime,otype,code,amount,openprice,closeprice,commission,earn where userid='".$obj->userid."'");
        if (count($data)>0){
            return array("userid"=>$obj->userid,"history"=>$data);
        }
        return array("retcode"=>"10006","retmsg"=>"userid[".$obj->userid."] no data");
    }
    
    private function handle_calendar($obj){
        if (!(property_exists($obj,"future"))){
            return array("retcode"=>"10003","retmsg"=>"message not complete");
        }
        if (intval($obj->future)>100){
            return array("retcode"=>"10005","retmsg"=>"parameter out range");
        }
        $one = 24*60*60;
        $day = 1;
        $tday = array();
        $base = time();
        while (true){
            $day = $day+1;
            $tm = $base+$day*$one;
            $d = date("Y-m-d",$tm);
            $w = date('w',$tm);
            if ($w==0 or $w==6){
                continue;
            }
            $rest = $this->exe_sql_one("select count(*) from trader_global where name='".$d."'");
            if ($rest[0]!="0"){
                continue;
            }
            array_push($tday,$d);
            if (count($tday)==intval($obj->future)){
                break;
            }
        }
        return array("days"=>$tday);
    }
    
}


?>