<?php
    require_once dirname(__file__)."/hylib.php";
    
    class lrroles{
        private $roles;
        private $banzi;
        private $hasthief;
        function __construct($confstr){
            $this->hasthief = false;
            $this->banzi = array();
            $this->roles = array();
            $this->roles["0"] = "上帝";
            $this->roles["1"] = "狼人";
            $this->roles["2"] = "村民";
            $this->roles["3"] = "盗贼";
            $this->roles["4"] = "丘比特";
            $this->roles["5"] = "混子";
            $this->roles["6"] = "野孩子";
            $this->roles["20"] = "白狼王";
            $this->roles["21"] = "狼美人";
            $this->roles["22"] = "狼枪";
            $this->roles["23"] = "梦魇";
            $this->roles["24"] = "恶灵骑士";
            $this->roles["25"] = "隐狼";
            $this->roles["26"] = "大野狼";
            $this->roles["50"] = "预言家";
            $this->roles["51"] = "女巫";
            $this->roles["52"] = "猎人";
            $this->roles["53"] = "守卫";
            $this->roles["54"] = "白痴";
            $this->roles["55"] = "骑士";
            $this->roles["56"] = "驯熊师";
            $this->roles["57"] = "狐狸";
            $this->roles["58"] = "魔术师";
            $this->roles["59"] = "摄梦人";
            $this->convert($confstr);
        }

        public function getname($key){
            return $this->roles[$key];
        }
        
        public function banzi(){
            return $this->banzi;
        }
        
        public function hasthief(){
            return $this->hasthief;
        }

        private function convert($strconf){
            $data = explode("|",$strconf);
            foreach($data as $item){
                //echo $item.",";
                if (!array_key_exists($item,$this->roles)){
                    array_splice($this->banzi,0,count($this->banzi));
                    return;
                }
                if ($item=="3"){
                    $this->hasthief = true;
                }
                //echo $this->roles[$item].",";
                array_push($this->banzi,$this->roles[$item]);
            }
            return;
        }
    }
    
    class lrutil{
        const SUCCESS = 0;
        const ACTION_UNKNOWN=10000;
        const DB_ERROR=10001;
        const POST_DATA_ERROR=10002;
        const PARAM_MISSING=10003;
        const SYSTEM_ERROR=10004;
        const THIRDPART_ERROR=10005;

        public static function to_json($retcode){
            return json_encode(array("retcode"=>$retcode));
        }

        public static function to_json_msg($retcode,$retmsg){
            return json_encode(array("retcode"=>$retcode,"retmsg"=>$retmsg));
        }

        public static function to_json_array($retcode,$data){
            $response = array("retcode"=>$retcode,"data"=>$data);
            return json_encode($response);
        }
    }

    class hylrlib{
        private $lib;
        private $init;
        private $eventhandler = array("get_info"=>"handle_get_info","create_game"=>"handle_create_game","enter_room"=>"handle_enter_room");

        function __construct(){
            $this->lib = new hylib('root','123456');
            //$this->lib->setmode("debug");
            $this->init = false;
            if ($this->lib->isok()){
                if ($this->lib->select_db("langren")){
                    $this->init = true;
                }
            }
        }

        function __destruct(){
        }

        public function handle(){
            $qarr = array();
            //echo $_SERVER["QUERY_STRING"];
            parse_str($_SERVER["QUERY_STRING"],$qarr);
            if (!$this->init){
                echo lrutil::to_json_msg(lrutil::DB_ERROR,"database error");
            }
            elseif (array_key_exists($qarr["action"],$this->eventhandler)){
                echo call_user_func(array($this,$this->eventhandler[$qarr["action"]]),$qarr);
            }
            else{
                echo lrutil::to_json_msg(lrutil::ACTION_UNKNOWN,"action type[".$qarr["action"]."] wrong");
            }
        }

        private function handle_get_info($qarr){
            if (array_key_exists("code",$qarr)){
                $code = $qarr["code"];
                $appid = "wxe0a4963819cbba76";
                $secret = "b862a81d0456077ab16bafc6a55fa339";
                $url = "https://api.weixin.qq.com/sns/jscode2session?appid=".$appid."&secret=".$secret."&js_code=".$code."&grant_type=authorization_code";
                $curl = curl_init();
                curl_setopt($curl, CURLOPT_URL, $url);
                curl_setopt($curl, CURLOPT_HEADER, 0);
                curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
                curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);//这个是重点。
                $data = curl_exec($curl);
                curl_close($curl);
                $data = json_decode($data);
                if (array_key_exists("errcode",$data)){
                    return lrutil::to_json_msg(lrutil::THIRDPART_ERROR,"code:".$data["errcode"].",msg:".$data["errmsg"]);
                }
                elseif(array_key_exists("openid",$data) and array_key_exists("session_key",$data)){
                    return lrutil::to_json_array(lrutil::SUCCESS,$data);
                }
                else{
                    return lrutil::to_json_msg(lrutil::THIRDPART_ERROR,"unknown error");
                }
            }
            return lrutil::to_json_msg(lrutil::PARAM_MISSING,"code parameter missing");
        }

        private function handle_create_game($qarr){
            if (array_key_exists("id",$qarr) and array_key_exists("roles",$qarr)){
                $openid = $qarr["id"];
                $roles = new lrroles($qarr["roles"]);
                $rs = $roles->banzi();
                $hasthief = $roles->hasthief();
                $roomgame = $this->get_room();
                shuffle($rs);
                $sqls = array();
                $data = array();
                $gameid = $roomgame[1];
                $roomid = $roomgame[0];
                array_push($sqls,"insert into lr_seats(gameid,seatno,role) values('".$gameid."',0,'".$roles->getname("0")."')");
                $howmany = count($rs);
                if ($hasthief){
                    $howmany = $howmany-2;
                    array_push($sqls,"insert into lr_seats(gameid,seatno,role,status) values('".$gameid."',".($howmany+1).",'".$rs[$howmany]."',3)");
                    array_push($sqls,"insert into lr_seats(gameid,seatno,role,status) values('".$gameid."',".($howmany+2).",'".$rs[$howmany+1]."',3)");
                    $data[strval($howmany+1)] = $rs[$howmany];
                    $data[strval($howmany+2)] = $rs[$howmany+1];
                }
                for($i=1;$i<=$howmany;$i++){
                    array_push($sqls,"insert into lr_seats(gameid,seatno,role) values('".$gameid."',".($i).",'".$rs[$i-1]."')");
                    $data[strval($i)] = $rs[$i-1];
                }
                if ($this->lib->task($sqls)){
                    return lrutil::to_json_array(lrutil::SUCCESS,$data);
                }
                else{
                    return lrutil::to_json_msg(lrutil::SYSTEM_ERROR,"system error");
                }
            }
            else{
                return lrutil::to_json_msg(lrutil::PARAM_MISSING,"parameter missing");
            }
        }

        private function handle_enter_room($qarr){
        }

        private function get_room(){
            while(true){
                $roomid = mt_rand(1000,9999);
                $gameid = date('Ymdhis').$roomid.mt_rand(100000,999999);
                $has = $this->lib->exe_sql_one("select count(*) from lr_room where roomid='".$roomid."'");
                if (intval($has[0])==0){
                    $sqls = array();
                    array_push($sqls,"insert into lr_room(roomid,gameid,created) values('".$roomid."','".$gameid."',".time().")");
                    if ($this->lib->task($sqls)){
                        return array($roomid,$gameid);
                    }
                }
            }
        }
    }

?>