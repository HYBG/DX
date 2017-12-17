<?php
define ("BG_LOG_TRACE",0);
define ("BG_LOG_DEBUG",1);
define ("BG_LOG_INFO",2);
define ("BG_LOG_WARNING",3);
define ("BG_LOG_ERROR",4);
define ("BG_LOG_CRITICAL",5);
define ("MENU_DEFAULT","输入\"角色\"查看所有特殊角色,输入\"狼人杀\"创建新游戏,输入\"重置\"恢复初始状态");
define ("LADYW","狼美人:身份【狼】,阵营【狼人】,技能【晚上魅惑一名玩家，白天狼美人被投票放逐时，该玩家一同被放逐】");
define ("HUNTERW","狼枪:身份【狼】,阵营【狼人】,技能【符合死亡条件时,可以射杀一名玩家,无特殊情况该玩家死亡】");
define ("SPY","间谍:身份【神】,阵营【狼人】,技能【针对狼人身份的技能对间谍均无效,夜晚间谍和狼人一起睁眼杀人】");
define ("HACKER","黑客:身份【狼】,阵营【狼人】,技能【每天晚上可以篡改一名玩家的身份,狼变为神,神/民变为狼,白天自动恢复】");
define ("KINGW","狼王:身份【狼】,阵营【狼人】,技能【白天归票或投票前自爆,可以同时杀死一名玩家】");
define ("NIGHTMARE","梦魇:身份【狼】,阵营【狼人】,技能【每晚可以指定一名玩家,如果其拥有夜晚技能,则失效】");
define ("TELLER","预言家:身份【神】,阵营【人类】,技能【每晚查验一名玩家的身份】");
define ("WITCH","女巫:身份【神】,阵营【人类】,技能【有一瓶毒药,晚上可以毒杀一名玩家,一瓶解药,晚上可以解救一名玩家,同一天最多使用一瓶药，不能给自己用药】");
define ("HUNTERH","猎人:身份【神】,阵营【人类】,技能【符合死亡条件时,可以射杀一名玩家,无特殊情况该玩家死亡】");
define ("KEEPER","守卫:身份【神】,阵营【人类】,技能【每晚可以指定一名玩家,该玩家当晚可以免于狼刀】");
define ("FOOL","白痴:身份【神】,阵营【人类】,技能【被放逐之后,还可以发言,但不能投票】");
define ("KNIGHT","骑士:身份【神】,阵营【人类】,技能【白天归票或投票前,可以选择一名玩家决斗,如果该玩家身份是狼,该玩家死,进入黑夜,否则骑士死，继续发言或投票】");
define ("DREAMTAKER","摄梦人:身份【神】,阵营【人类】,技能【晚上指定一名玩家处于梦游状态,该玩家晚上狼刀和毒药均无效,摄梦人如果晚上死亡,该玩家一同死亡,摄梦人连续两晚摄梦同一人,则该玩家死亡】");
define ("MAGICIAN","魔术师:身份【神】,阵营【人类】,技能【晚上指定两名玩家交换号码牌,针对其中一名玩家的夜间技能均视为对另一名使用,除特殊情况,此信息对其他玩家均为未知】");
define ("KINGH","国王:身份【神】,阵营【人类】,技能【在放逐发言阶段,国王可以选择亮明身份,身份亮明以后可以二选一行使王权,1、特赦一名玩家,该玩家在当天所有的放逐阶段得票均计算为0.2、在所有投票阶段的票权为2.国王死后,如果场上有警长,可以选择罢免警长或任命一个警长以外的玩家为摄政王,摄政王的票权为1.6,摄政王不能接受警徽,如果场上没有警长,可以任命一个警长.如果国王死在夜里,且任命了警长,警长当天白天可以进行一次临时查牌,查验一名玩家的底牌,如果摄政王死在夜里,且有警长在场,警长当天白天也获得一次临时查牌权力.临时查牌是查看玩家身份,上帝报出所有角色,给出精确身份】");
define ("GUARD","侍卫:身份【神】,阵营【人类】,技能【夜里如果国王被狼刀,如果侍卫还活着,侍卫代替国王死亡并且国王右手边方向第一个狼身份的玩家同时死亡,如果侍卫被狼刀,侍卫死亡并且自己左手边方向的第一个狼身份玩家同时死亡】");
define ("SPIRITIST","招魂师:身份【神】,阵营【人类】,技能【每天晚上可以选择一名已知的死去玩家,令其借用另一玩家肉身还魂,被借用肉身的玩家称为“尸”,还魂玩家称为“魂”,白天“尸”不能发言不能投票,“魂”正常发言投票,“魂”如果死在白天,视为“尸”死,“魂”进入也夜晚前自动死去.移魂师无论死活均可发动技能,可以移魂自己,但不能连续2晚移魂同一名玩家,也不能连续2晚借用同一玩家肉身.白天的“尸”死后,当晚可以还魂.“尸”与“魂”不改变身份,即不影响胜负结果,举个例子,场上剩三名玩家一狼,一神，一民,狼被借“尸”,“魂”是民,游戏继续,必须把“魂”放逐,人类阵营才获得胜利】");
define ("VICTIM","冤死鬼:身份【神】,阵营【人类】,技能【当冤死鬼白天死亡时,将立刻再进行一次投票,没有讨论发言,直接投票,票高者死亡,平票或无人投票则投票阶段结束.当冤死鬼死夜里死亡时,可以指定一名玩家发起一次决斗,如果该玩家身份为狼人,则该玩家一同死亡,否则冤死鬼自己死亡】");
define ("AGENT","特工:身份【神】,阵营【人类】,技能【首夜特工指定一名玩家,该玩家死亡后,特工觉醒,觉醒后的特工每晚可以选择1.杀死一名玩家\n2.查看一名玩家是否与自己是同一阵营\n特工夜里死亡不能发动技能】");
define ("WORKER","工作狂:身份【神】,阵营【人类】,技能【每晚选择一个玩家,如果该玩家在白天投票阶段还活着,加班狂的票必须投给该玩家,否则必须弃票,加班狂晚上被刀,被毒,被枪击均无效】");
define ("HERO","义士:身份【神】,阵营【人类】,技能【每晚可以选定一个角色,如果此人晚上死去,则义士代替其死去,在白天投票结束时,如果出现被放逐的玩家后,义士可以代替其被放逐,无论白天夜间义士死时都可以发表遗言】");
define ("DETECTIVE","侦探:身份【神】,阵营【人类】,技能【每天晚上可以选择向上帝下列问题中的一个,上帝给出相应的手势\n1.他的身份是否是狼人?\n2.他是否拥有特殊技能?\n3.他是不是间谍?\n4.刚刚过去的白天里死的人是否有狼?\n5.场上还有几个狼阵营的玩家?\n侦探在招魂师之后醒来,如果“魂”是狼阵营,计算在问题5内】");
define ("MUGWUMP","混子:身份【民】,阵营【未知】,技能【首夜选择一名玩家,本局游戏混子的阵营与该玩家相同,但没有其他任何技能】");
define ("CUPID","丘比特:身份【神】,阵营【未知】,技能【丘比特在第一天晚上指定任意两名玩家，使他们成为情侣,丘比特和情侣为同一阵营,情侣本身为不同阵营时形成第三方阵营,胜利目标为其他玩家全部死亡】");
define ("THIEF","盗贼:身份【神】,阵营【未知】,技能【首夜睁眼,在上帝提供的两个其他身份里面选择一个替换盗贼身份,如果上帝提供的身份里有狼阵营身份,必选之.之后盗贼身份及阵营均由选择后身份确定】");
define ("BEAR","熊:身份【神】,阵营【人类】,技能【每天早上睁眼,如果熊身边两边的玩家里有狼身份玩家,则熊会咆哮,熊死后每天依然要宣布熊不会咆哮】");
define ("FOX","狐狸:身份【神】,阵营【人类】,技能【每晚狐狸选择三个连续的活着的玩家,上帝将告知狐狸这三个玩家中是否有有人有狼人属性.若有,则狐狸在下一晚仍然可以使用此技能;若没有,则狐狸将失去此能力.】");

class bglib{
    private $db;
    private $loglevel = 2; //0:trace,1:debug,2:info,3:warning,4:error,5:critical
    private $typehandler = array("text"=>"handle_text","event"=>"handle_event");
    private $eventhandler = array("subscribe"=>"handle_subscribe","unsubscribe"=>"handle_unsubscribe");
    private $texthandler = array("handle_0","handle_1","handle_2","handle_100","handle_101","handle_102","handle_default");
    private $roles = array("狼王"=>KINGW,"梦魇"=>NIGHTMARE,"狼美人"=>LADYW,"狼枪"=>HUNTERW,"间谍"=>SPY,"黑客"=>HACKER,"预言家"=>TELLER,"女巫"=>WITCH,"猎人"=>HUNTERH,"守卫"=>KEEPER,"白痴"=>FOOL,"骑士"=>KNIGHT,"摄梦人"=>DREAMTAKER,"魔术师"=>MAGICIAN,"国王"=>KINGH,"侍卫"=>GUARD,"招魂师"=>SPIRITIST,"冤死鬼"=>VICTIM,"特工"=>AGENT,"工作狂"=>WORKER,"义士"=>HERO,"侦探"=>DETECTIVE,"混子"=>MUGWUMP,"丘比特"=>CUPID,"盗贼"=>THIEF,"熊"=>BEAR,"狐狸"=>FOX);
    private $shortcut = array();

    function __construct(){
        $this->db = mysqli_connect('localhost', 'root', '123456');
        if (!$this->db){
            $this->logger("bglib",BG_LOG_ERROR,"cannot connect db");
        }
        $selected = mysqli_select_db($this->db, "bg");
        if (!$selected){
            $this->logger("bglib",BG_LOG_ERROR,"db not found");
        }
        $this->shortcut["9a"] = array(array("预言家","女巫","猎人"),3,3,false);
        $this->shortcut["9b"] = array(array("预言家","女巫","猎人","丘比特","盗贼"),3,3,true);
        $this->shortcut["10a"] = array(array("预言家","女巫","猎人","混子"),3,3,false);
        $this->shortcut["10b"] = array(array("预言家","女巫","猎人","混子","丘比特","盗贼"),3,3,true);
        $this->shortcut["11a"] = array(array("预言家","女巫","猎人","工作狂","丘比特","盗贼"),4,3,true);
        $this->shortcut["12a"] = array(array("预言家","女巫","猎人","白痴"),4,4,false);
        $this->shortcut["12b"] = array(array("预言家","女巫","国王","侍卫","间谍"),3,4,false);
        $this->shortcut["12c"] = array(array("预言家","女巫","国王","侍卫","间谍","丘比特","盗贼"),3,4,true);
    }

    function __destruct(){
        mysqli_close($this->db);
    }

    private function transmit_text($from,$to,$content){
        $texttpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content></xml>";
        $result = sprintf($texttpl,$from,$to,time(),$content);
        return $result;
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
            $this->logger("bglib",BG_LOG_ERROR,"exe_sql_one:execute sql[".$sql."] failed");
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
            $this->logger("bglib",BG_LOG_ERROR,"exe_sql_batch:execute sql[".$sql."] failed");
        }
        return $a;
    }

    public function task($sqls,$commi=true){
        foreach($sqls as $sql){
            $r = mysqli_query($this->db, $sql);
            if (!$r){
                mysql_query("ROLLBACK");
                $this->logger("bglib",BG_LOG_ERROR,"task:execute sql[".$sql."] failed,task rollback");
                return 1;
            }
            $this->logger("bglib",BG_LOG_DEBUG,"task:execute sql[".$sql."] successfully");
        }
        if ($commi){
            mysql_query("COMMIT");
        }
        return 0;
    }

    private function timestamp(){
        $dt = date('Y-m-d H:i:s');
        list($msec, $sec) = explode(' ',microtime());
        $dt = $dt." ".sprintf('%.0f', floatval($msec)*100000000);
        return $dt;
    }

    public function logger($mod,$lev,$log){
        if(isset($_SERVER['HTTP_APPNAME'])){   //SAE
            sae_set_display_errors(false);
            sae_debug($log_content);
            sae_set_display_errors(true);
        }
        elseif($_SERVER['REMOTE_ADDR'] != "127.0.0.1"){ //LOCAL
            $max_size = 100000;
            $log_filename = "/var/www/html/bg/log/bg.log";
            if(file_exists($log_filename) and (abs(filesize($log_filename)) > $max_size)){
                unlink($log_filename);
            }
            file_put_contents($log_filename, $this->timestamp()." ".$mod." ".$lev." ".$log."\n", FILE_APPEND);
        }
    }

    public function bgapp(){
        $appid = $this->exe_sql_one("select value from bg_global where name='appid'");
        $secret = $this->exe_sql_one("select value from bg_global where name='appsecret'");
        if (count($appid)>0 and count($secret)>0){
            return array($appid[0],$secret[0]);
        }
        else{
            $this->logger("bglib",BG_LOG_WARNING,"dxapp: appid or appsecret missing!");
            return array();
        }
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
                $content = MENU_DEFAULT;
            }
            $content = $this->transmit_text($obj->FromUserName,$obj->ToUserName,$content);
            $this->logger("bglib",BG_LOG_DEBUG,$content);
        }
        return $content;
    }

    private function handle_text($object){
        $st = $this->exe_sql_one("select status from bg_user where extid='".$object->FromUserName."'");
        $content = $this->handle_key($object->Content,$object->FromUserName,$st);
        if ($content == ""){
            if (count($st)>0){
                $st = intval($st[0]);
                foreach($this->texthandler as $handler){
                    $content = call_user_func(array($this,$handler),$object->Content,$object->FromUserName,$st);
                    if ("" != $content){
                        break;
                    }
                }
            }
            else{
                $this->task(array("insert into bg_user(extid) values('".$object->FromUserName."')"));
                $content = "请输入您的昵称....(输入'我是XX')";
            }
        }
        return $content;
    }

    private function handle_key($key,$from,$status){
        $content = "";
        if ($key=="reset" or $key=="重置"){
            $content = $this->reinit($key,$from);
        }
        elseif ($key=="角色"){
            $ks = array_keys($this->roles);
            sort($ks);
            $content = "所有特殊角色\n";
            for($i=0;$i<count($ks);$i++){
                $content = $content.($i+1).".".$ks[$i]."\n";
            }
            $content = $content."\n输入角色名查看角色描述\n";
        }
        elseif(mb_substr($key,0,2,'utf-8')=="改名"){
            $nick = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
            $ct = $this->exe_sql_one("select count(*) from bg_user where nickname='".$nick."'");
            if ($ct[0]=="1"){
                $content = "昵称已被占用,请换个昵称....";
            }
            else{
                $this->task(array("update bg_user set nickname='".$nick."',status=1 where extid='".$from."'"));
                $content = "hello ".$nick."\n";
                $content = $content.MENU_DEFAULT;
            }
        }
        elseif (isset($this->roles[trim($key)])){
            $content = $this->roles[trim($key)];
        }
        return $content;
    }
    
    private function handle_0($key,$from,$status){
        $content = "";
        if ($status==0){
            if (mb_substr($key,0,2,'utf-8')=="我是"){
                $nick = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
                $ct = $this->exe_sql_one("select count(*) from bg_user where nickname='".$nick."'");
                if ($ct[0]=="1"){
                    $content = "昵称已被占用,请换个昵称....(输入'我是XX')";
                }
                else{
                    $this->task(array("update bg_user set nickname='".$nick."',status=1 where extid='".$from."'"));
                    $content = "hello ".$nick."\n";
                    $content = $content.MENU_DEFAULT;
                }
            }
            else{
                $content = "请输入您的昵称....(输入'我是XX')";
            }
        }
        return $content;
    }

    private function handle_1($key,$from,$status){
        $content = "";
        if ($status==1){
            if ($key=="狼人杀"){
                $content = "请选择角色\n";
                $rs = array_keys($this->roles);
                sort($rs);
                for($i=0;$i<count($rs);$i++){
                    $content = $content.($i+1).":".$rs[$i]."\n";
                }
                $content = $content."\n";
                $content = $content."选择格式:a.b.c-d.e\n";
                $content = $content."a,b,c为特殊角色的序号,d为普通狼人数量,e为村民数量\n\n";
                $content = $content."快捷方式\n";
                foreach($this->shortcut as $k=>$shcut){
                    $content = $content.$k.":";
                    foreach($shcut[0] as $god){
                        $content = $content.$god.",";
                    }
                    $content = $content."狼人".$shcut[1].",村民".$shcut[2]."\n";
                }
                $tm = time();
                $this->task(array("update bg_user set status=2,expire=".($tm+2*60)." where extid='".$from."'"));
            }
            else{
                $rc = $this->exe_sql_one("select count(*) from bg_room where roomid='".$key."' and status=1");
                if ($rc[0]=="1"){ //
                    $srs = $this->exe_sql_batch("select seatid,role from bg_game where roomid='".$key."' and status=0");
                    if (count($srs)==0){
                        $content = "房间已满员\n";
                    }
                    else{
                        $nm = $this->exe_sql_one("select nickname from bg_user where extid='".$from."'");
                        shuffle($srs);
                        $popped = array_pop($srs);
                        $status = 101;
                        if($popped[1]=="盗贼"){
                            $status = 100;
                        }
                        $sqls = array();
                        $tm = time();
                        if (count($srs)==0){
                            array_push($sqls,"update bg_room set status=2,expire=".($tm+4*60*60)." where roomid='".$key."'");
                        }
                        array_push($sqls,"update bg_game set status=1,player='".$nm[0]."' where roomid='".$key."' and seatid=".$popped[0]);
                        array_push($sqls,"update bg_user set status=".$status.",expire=".($tm+4*60*60).",roomid='".$key."',seatid=".$popped[0].",role='".$popped[1]."' where extid='".$from."'");
                        if (0 == $this->task($sqls)){
                            $content = "玩家:".$nm[0]."\n角色:".$popped[1]."\n座位号:".$popped[0]."\n\n";
                            if ($status==100){
                                $leftrs = $this->exe_sql_batch("select seatid,role from bg_game where roomid='".$key."' and status=2");
                                $content = $content."置换身份候选(输入序号选择):\n";
                                $content = $content.$leftrs[0][0].".".$leftrs[0][1]."\n";
                                $content = $content.$leftrs[1][0].".".$leftrs[1][1]."\n\n";
                            }
                            $content = $content."输入\"配置\"查看本局角色列表,上帝宣布投票后可输入要投的玩家的座位号进行投票,上帝宣布投票结束后可输入\"查看投票\"查看投票结果\n";
                        }
                        else{
                            $content = "进入房间失败\n";
                        }
                    }
                }
                else{
                    $content = "房间已解散或不存在\n";
                }
            }
        }
        return $content;
    }
    
    private function handle_100($key,$from,$status){
        $content = "";
        if ($status==100){
            $rid = $this->exe_sql_one("select roomid,nickname,seatid from bg_user where extid='".$from."'");
            $switch = $this->exe_sql_batch("select seatid,role from bg_game where roomid='".$rid[0]."' and status=2");
            $drop = $this->exe_sql_one("select seatid,role from bg_game where roomid='".$rid[0]."' and seatid!=".$key." and status=2");
            $sqls = array();
            $sid = $rid[2];
            array_push($sqls,"update bg_game set role='".$drop[1]."|埋' where roomid='".$rid[0]."' and seatid='".$drop[0]."'");
            if ($key==$switch[0][0]){
                array_push($sqls,"update bg_game set role='".$switch[0][1]."|换' where roomid='".$rid[0]."' and seatid='".$sid."'");
                array_push($sqls,"update bg_game set role='盗贼|换' where roomid='".$rid[0]."' and seatid='".$key."'");
                array_push($sqls,"update bg_user set role='".$switch[0][1]."',status=101 where extid='".$from."'");
                $this->task($sqls);
                $content = "玩家:".$rid[1]."\n新角色:".$switch[0][1]."\n座位号:".$sid."\n\n";
            }
            elseif ($key==$switch[1][0]){
                array_push($sqls,"update bg_game set role='".$switch[1][1]."|换' where roomid='".$rid[0]."' and seatid='".$sid."'");
                array_push($sqls,"update bg_game set role='盗贼|换' where roomid='".$rid[0]."' and seatid='".$key."'");
                array_push($sqls,"update bg_user set role='".$switch[1][1]."',status=101 where extid='".$from."'");
                $this->task($sqls);
                $content = "玩家:".$rid[1]."\n新角色:".$switch[1][1]."\n座位号:".$sid."\n\n";
            }
            else{
                $content = "输入无效";
            }
        }
        return $content;
    }

    private function fill($roles,$langs,$mins){
        $rs = array();
        $desc = "配置:\n";
        foreach($roles as $role){
            $desc = $desc.$role.":1\n";
            array_push($rs,$role);
        }
        $desc = $desc."狼人:".$langs."\n";
        $desc = $desc."村民:".$mins."\n";
        for($i=0;$i<$langs;$i++){
            array_push($rs,"狼人");
        }
        for($i=0;$i<$mins;$i++){
            array_push($rs,"村民");
        }
        return array($rs,$desc);
    }

    private function handle_parse($key){
        list($gods,$comm) = explode('-',$key);
        $glis = explode('.',$gods);
        list($lang,$min) = explode('.',$comm);
        $langct = intval($lang);
        $minct = intval($min);
        $rs = array();
        $roles = array_keys($this->roles);
        sort($roles);
        $desc = "配置:\n";
        $hasthief = false;
        foreach($glis as $god){
            if (isset($roles[intval($god)-1])){
                array_push($rs,$roles[intval($god)-1]);
                $desc = $desc.$roles[intval($god)-1].":1\n";
                if ($roles[intval($god)-1]=="盗贼"){
                    $hasthief = true;
                }
            }
        }
        $desc = $desc."狼人:".$langct."\n";
        $desc = $desc."村民:".$minct."\n";
        for($i=0;$i<$langct;$i++){
            array_push($rs,"狼人");
        }
        for($i=0;$i<$minct;$i++){
            array_push($rs,"村民");
        }
        return array($rs,$desc,$hasthief);
    }

    private function confroles($key){
        $conf = array();
        $cut = trim($key);
        $this->logger("bglib",BG_LOG_DEBUG,"confroles key:[".$key."]");
        if (isset($this->shortcut[$cut])){
            $conf = $this->fill($this->shortcut[$cut][0],$this->shortcut[$cut][1],$this->shortcut[$cut][2]);
            array_push($conf,$this->shortcut[$cut][3]);
        }
        else{
            $conf = $this->handle_parse($key);
        }
        return $conf;
    }

    private function handle_2($key,$from,$status){
        $content = "";
        if ($status==2){
            $conf = $this->confroles($key);
            $roles = $conf[0];
            if (count($roles)==0){
                $content = "角色配置错误";
            }
            else{
                $content = $conf[1];
                $hasthief = $conf[2];
                shuffle($roles);
                $ids = $this->exe_sql_batch("select roomid from bg_room where status=0");
                if (count($ids)==0){
                    $content = "房间已满";
                }
                else{
                    shuffle($ids);
                    $roomid = array_pop($ids);
                    $roomid = $roomid[0];
                    if ($hasthief){
                        $role1 = array_pop($roles);
                        $role2 = array_pop($roles);
                    }
                    $sqls = array();
                    $tm = time();
                    $nm = $this->exe_sql_one("select nickname from bg_user where extid='".$from."'");
                    array_push($sqls,"insert into bg_global(name,value) values('".$roomid."','".$content."')");
                    array_push($sqls,"insert into bg_game(roomid,seatid,role,status,player) values('".$roomid."',0,'上帝',1,'".$nm[0]."')");
                    array_push($sqls,"update bg_user set roomid='".$roomid."',seatid=0,role='上帝',status=102,expire=".($tm+4*60*60)." where extid='".$from."'");
                    array_push($sqls,"update bg_room set status=1,expire=".($tm+30*60)." where roomid='".$roomid."'");
                    for($i=0;$i<count($roles);$i++){
                        array_push($sqls,"insert into bg_game(roomid,seatid,role) values('".$roomid."',".($i+1).",'".$roles[$i]."')");
                    }
                    if ($hasthief){
                        array_push($sqls,"insert into bg_game(roomid,seatid,role,status) values('".$roomid."',".($i+1).",'".$role1."',2)");
                        array_push($sqls,"insert into bg_game(roomid,seatid,role,status) values('".$roomid."',".($i+2).",'".$role2."',2)");
                    }
                    if (0 == $this->task($sqls)){
                        $content = $content."房间号:".$roomid."\n\n";
                        $content = $content."输入\"检查座位\"查看座位占用情况\n";
                        $content = $content."输入\"开始投票\"等待玩家投票\n";
                        $content = $content."输入\"结束投票xx\"查看投票结果,xx为投票备注(比如:上警)\n";
                        $content = $content."输入\"N:xxx\"记录游戏进程\n";
                        $content = $content."输入\"摘要\"获取游戏全记录\n";
                        $content = $content."输入\"退出\"退出游戏,退出游戏后可创建新游戏";
                    }
                    else{
                        $content = $content."房间创建失败";
                    }
                }
            }
            
        }
        return $content;
    }

    private function handle_101($key,$from,$status){
        $content = "";
        if ($status==101){
            $ids = $this->exe_sql_one("select voteid,roomid,seatid from bg_user where extid='".$from."'");
            if (($key=="退出") or ($key=="exit")){
                $content = $this->reinit($key,$from);
            }
            elseif ($key=="查看投票"){
                $content = "投票结果\n";
                $content = $content.$this->lastvote($from);
            }
            elseif ($key=="配置"){
                /*$roles = $this->exe_sql_batch("select role from bg_game where roomid='".$ids[1]."' and seatid!=0");
                $content = "配置:\n";
                shuffle($roles);
                foreach($roles as $role){
                    $content = $content.$role[0]."\n";
                }*/
                $content = $this->exe_sql_one("select value from bg_global where name='".$ids[1]."'");
                $content = $content[0]."\n";
            }
            else{
                if (!empty($ids[0])){
                    $maxst = $this->exe_sql_one("select max(seatid) from bg_game where roomid='".$ids[1]."'");
                    if (intval($key)>=0 and intval($key)<=intval($maxst)){
                        $this->task(array("insert into bg_vote(voteid,seatid,vote) values('".$ids[0]."',".$ids[2].",".$key.")"));
                        $content = "投票完成,等待上帝宣布投票结束，输入\"查看投票\"查看投票结果";
                    }
                    else{
                        $content = "投票无效";
                    }
                }
                else{
                    $content = "稍等";
                }
            }
            
        }
        return $content;
    }
    
    private function handle_102($key,$from,$status){
        $content = "";
        if ($status==102){
            $sqls = array();
            $ids = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
            if (($key=="vote") or ($key=="开始投票")){
                $vid = $this->buildid();
                $pls = $this->exe_sql_batch("select extid from bg_user where roomid='".$ids[0]."'");
                foreach($pls as $pl){
                    array_push($sqls,"update bg_user set voteid='".$vid."' where extid='".$pl[0]."'");
                }
                array_push($sqls,"update bg_user set status=101 where roomid='".$ids[0]."' and extid!='".$from."'");
                $this->task($sqls);
                $content = "等待玩家投票";
            }
            elseif(mb_substr($key,0,4,'utf-8')=="结束投票"){
                $votefor = mb_substr($key,4,mb_strlen($key)-4,'utf-8');
                $vstr = $this->lastvote($from);
                $content = "投票结果\n".$vstr;
                $seqid = $this->buildid();
                $this->task(array("insert into bg_votedetail(idseq,roomid,vfor,vstring,timestamp) values('".$seqid."','".$ids[0]."','".$votefor."','".$vstr."','".date('Y-m-d H:i:s')."')"));
            }
            elseif(($key=="检查座位") or ($key=="check")){
                $ss = $this->exe_sql_batch("select seatid,role,player from bg_game where roomid='".$ids[0]."'");
                $content = "房间情况:\n";
                foreach($ss as $st){
                    $content = $content.$st[0]." ".$st[1]." ".$st[2]."\n";
                }
            }
            elseif($key=="摘要"){
                $content = $this->abst($from);
            }
            elseif(($key=="exit") or ($key=="退出")){
                $content = $this->reinit($key,$from);
            }
            elseif((substr($key,0,2)=="N:") or (substr($key,0,2)=="n:") or (mb_substr($key,0,2,'utf-8')=="注 ")){
                $id = $this->buildid();
                $note = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
                $this->task(array("INSERT INTO bg_process(idseq,roomid,notes,timestamp) VALUES('".$id."','".$ids[0]."','".$note."','".date('Y-m-d H:i:s')."')"));
                $content = "笔记写入";
            }
            else{
                $content = "无效输入";
            }
        }
        return $content;
    }

    private function handle_event($object){
        if (array_key_exists($RX_TYPE,$this->eventhandler)){
            $content = call_user_func(array($this,$this->eventhandler[$object->Event]),$object);
        }
        else{
            $content = MENU_DEFAULT;
        }
        return $content;
    }

    private function handle_subscribe($from){
        $ct = $this->exe_sql_one("select count(*) from bg_user where extid='".$from."'");
        if ($ct[0]=="0"){
            $this->task(array("insert into bg_user(extid) values('".$from."')"));
            $content = "欢迎关注桌游俱乐部,请输入您的昵称....(输入'我是XX'),输入昵称后才能进行游戏";
        }
        else{
            $nlen = $this->exe_sql_one("select length(nickname),nickname from bg_user where extid='".$from."'");
            if (intval($nlen[0])>0){
                $content = "欢迎".$nlen[1]."回到桌游俱乐部";
            }
            else{
                $content = "欢迎回到桌游俱乐部,请输入您的昵称....(输入'我是XX'),输入昵称后才能进行游戏";
            }
            $this->task(array("update bg_user set status=1,expire=0 where extid='".$from."'"));
        }
        return $content;
    }

    private function handle_unsubscribe($from){
        $nlen = $this->exe_sql_one("select length(nickname) from bg_user where extid='".$from."'");
        $sqls = array();
        if ($nlen[0]=="0"){
            array_push($sqls,"update bg_user set status=0,expire=0 where extid='".$from."'");
        }
        else{
            array_push($sqls,"update bg_user set status=1,expire=0 where extid='".$from."'");
        }
        $this->task($sqls);
        return "";
    }

    private function handle_default($key,$from,$status){
        return MENU_DEFAULT;
    }
    
    private function buildid(){
        list($msec, $sec) = explode(' ',microtime());
        return date('YmdHis').sprintf('%.0f', floatval($msec)*100).mt_rand(100,999);
    }

    private function abst($from){
        $content = "演员表\n";
        $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
        $infs = $this->exe_sql_batch("select seatid,role,player,status from bg_game where roomid='".$rid[0]."' order by seatid");
        foreach($infs as $inf){
            $content = $content.$inf[0].".".$inf[1];
            $content = $content." ".$inf[2]."\n";
        }
        $content = $content."\n";
        $content = $content."过程摘要\n";
        $process = $this->exe_sql_batch("select notes from bg_process where roomid='".$rid[0]."'");
        foreach($process as $po){
            $content = $content.$po[0]."\n";
        }
        $content = $content."\n";
        $content = $content."投票信息\n";
        $vdetail = $this->exe_sql_batch("select vfor,vstring from bg_votedetail where roomid='".$rid[0]."' order by timestamp");
        foreach($vdetail as $vt){
            $content = $content.$vt[0].":\n";
            $content = $content.$vt[1]."\n";
        }
        return $content;
    }

    private function lastvote($from){
        $vid = $this->exe_sql_one("select voteid from bg_user where extid='".$from."'");
        $vinfs = $this->exe_sql_batch("select seatid,vote from bg_vote where voteid='".$vid[0]."'");
        foreach($vinfs as $inf){
            $content = $content.$inf[0]."=>".$inf[1]."\n";
        }
        return $content;
    }

    private function reinit($key,$from){
        $content = "重置完成";
        $inf = $this->exe_sql_one("select roomid,seatid,role,voteid,status,expire from bg_user where extid='".$from."'");
        $sqls = array();
        array_push($sqls,"update bg_user set roomid='',seatid=0,role='',voteid='',status=1,expire=0 where extid='".$from."'");
        if ($inf[2]=="上帝"){
            array_push($sqls,"update bg_user set roomid='',seatid=0,role='',voteid='',status=1,expire=0 where roomid='".$inf[0]."'");
            array_push($sqls,"DELETE FROM bg_game where roomid='".$inf[0]."'");
            array_push($sqls,"DELETE FROM bg_process where roomid='".$inf[0]."'");
            array_push($sqls,"DELETE FROM bg_vote where voteid='".$inf[3]."'");
            array_push($sqls,"DELETE FROM bg_votedetail where roomid='".$inf[0]."'");
            array_push($sqls,"DELETE FROM bg_global where name='".$inf[0]."'");
        }
        else{
            array_push($sqls,"DELETE FROM bg_game where roomid='".$inf[0]."' and seatid=".$inf[1]);
        }
        $this->task($sqls);
        return $content;
    }
}
?>
