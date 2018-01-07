<?php
define ("BG_LOG_TRACE",0);
define ("BG_LOG_DEBUG",1);
define ("BG_LOG_INFO",2);
define ("BG_LOG_WARNING",3);
define ("BG_LOG_ERROR",4);
define ("BG_LOG_CRITICAL",5);
define ("MENU_1","输入\"角色\"查看所有特殊角色,输入\"狼人杀\"创建新游戏,输入\"重置\"恢复初始状态,输入房间号进入游戏");
define ("GODMENU","输入\"检查座位\"查看座位占用情况\n输入\"结束投票xx\"查看投票结果,xx为投票备注(比如:上警)\n输入\"注 xxx\"记录游戏进程\n输入\"死 X Y\"备注死亡原因,X为座位号,Y为死因\n输入\"摘要\"获取游戏全记录\n输入\"退出\"退出游戏,退出游戏后可创建新游戏");

class bglib{
    private $db;
    private $loglevel = 2; //0:trace,1:debug,2:info,3:warning,4:error,5:critical
    private $typehandler = array("text"=>"handle_text","event"=>"handle_event");
    private $eventhandler = array("subscribe"=>"handle_subscribe","unsubscribe"=>"handle_unsubscribe");
    private $keyhandler = array("showroles","reinit");
    private $texthandler = array("handle_status_0","handle_status_1","handle_status_2","handle_status_100","handle_status_101","handle_status_102","handle_status_201");

    function __construct(){
        $this->db = mysqli_connect('localhost', 'root', '123456');
        if (!$this->db){
            $this->logger("bglib",BG_LOG_ERROR,"cannot connect db");
        }
        $selected = mysqli_select_db($this->db, "bg");
        if (!$selected){
            $this->logger("bglib",BG_LOG_ERROR,"db not found");
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

    public function exe_sql_one($sql){
        $a = array();
        $this->logger("bglib",BG_LOG_INFO,"exe_sql_one:execute sql[".$sql."]");
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

    public function handle_msg($poststr){
        $content = "";
        if (!empty($poststr)){
            //$this->logger("bglib",BG_LOG_DEBUG,$poststr);
            $obj = simplexml_load_string($poststr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $RX_TYPE = trim($obj->MsgType);
            if (array_key_exists($RX_TYPE,$this->typehandler)){
                $content = call_user_func(array($this,$this->typehandler[$RX_TYPE]),$obj);
            }
            else{
                $content = MENU_1;
            }
            $content = $this->transmit_text($obj->FromUserName,$obj->ToUserName,$content);
            //$this->logger("bglib",BG_LOG_DEBUG,$content);
        }
        return $content;
    }
    
    private function handle_common_key($key,$from){
        $content = "";
        $role = $this->exe_sql_one("select nature,bg_roles.group,skill,tips from bg_roles where bg_roles.name='".trim($key)."'");
        if (count($role)>0){
            $content = $key.":身份【".$role[0]."】,阵营【".$role[1]."】,技能【".$role[2]."】";
            if (isset($role[3])){
                $content = $content.",tips【".$role[3]."】";
            }
        }
        else{
            $kid = $this->exe_sql_one("select id from bg_keys where status='all' and id in (select id from bg_synonym where bg_synonym.key='".trim($key)."')");
            if (count($kid)>0){
                foreach($this->keyhandler as $handler){
                    $content = call_user_func(array($this,$handler),intval($kid[0]),$from);
                    if ("" != $content){
                        break;
                    }
                }
            }
        }
        return $content;
    }

    private function handle_text($object){
        $content = $this->handle_common_key($object->Content,$object->FromUserName);
        if ($content == ""){
            $st = $this->exe_sql_one("select status from bg_user where extid='".$object->FromUserName."'");
            $st = intval($st[0]);
            foreach($this->texthandler as $handler){
                $content = call_user_func(array($this,$handler),$object->Content,$object->FromUserName,$st);
                if ("" != $content){
                    break;
                }
            }
        }
        return $content;
    }
    
    private function handle_or_not($key,$status){
        $hand = $this->exe_sql_one("select bg_synonym.id from bg_synonym,bg_keys where bg_synonym.key='".trim($key)."' and bg_synonym.id=bg_keys.id and bg_keys.status=".$status);
        if (count($hand)>0){
            return array(true,intval($hand[0]));
        }
        return array(false,null);
    }
    
    private function handle_status_0($key,$from,$status){
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
                    $content = $content.MENU_1;
                }
            }
            else{
                $content = "请输入您的昵称....(输入'我是XX')";
            }
        }
        return $content;
    }
    
    //准备创建房间
    private function preparelrs($from){
        $content = "请根据游戏人数选择角色\n";
        $roles = $this->exe_sql_batch("select id,name from bg_roles order by id");
        foreach($roles as $role){
            $content = $content.$role[0].":".$role[1]."\n";
        }
        $content = $content."\n";
        $content = $content."选择格式:a.b.c-d.e\n";
        $content = $content."a,b,c为特殊角色的序号,d为普通狼人数量,e为村民数量,常用板子的创建可以使用前面的快捷方式\n";
        $content = $content."输入\"N人局\"(例如:九人局),查看对应玩家人数的快捷方式";
        $tm = time();
        $this->task(array("update bg_user set status=2,expire=".($tm+2*60)." where extid='".$from."'"));
        return $content;
    }

    private function handle_status_1($key,$from,$status){
        $content = "";
        if ($status==1){
            $hand = $this->handle_or_not($key,1);
            $handlers = array(1=>"preparelrs");
            if ($hand[0]){
                $kid = $hand[1];
                if (array_key_exists($kid,$handlers)){
                    $content = call_user_func(array($this,$handlers[$kid]),$from);
                }
            }
            elseif(mb_substr($key,0,2,'utf-8')=="改名"){
                $nick = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
                $ct = $this->exe_sql_one("select count(*) from bg_user where nickname='".$nick."'");
                if ($ct[0]=="1"){
                    $content = "昵称已被占用,请换个昵称....";
                }
                else{
                    $this->task(array("update bg_user set nickname='".$nick."' where extid='".$from."'"));
                    $content = "hello ".$nick."\n";
                    $content = $content.MENU_1;
                }
            }
            else{ //进入房间
                $rid = trim($key);
                $rc = $this->exe_sql_one("select count(*) from bg_room where roomid='".$rid."' and status=1");
                if ($rc[0]=="1"){ //
                    $srs = $this->exe_sql_batch("select seatid,roleid from bg_game where roomid='".$rid."' and status=0");
                    if (count($srs)==0){
                        $content = "房间已满员\n";
                    }
                    else{
                        $nm = $this->exe_sql_one("select nickname from bg_user where extid='".$from."'");
                        shuffle($srs);
                        $popped = array_pop($srs);
                        $status = 101;
                        //10=="盗贼"
                        if($popped[1]=="10"){
                            $status = 100;
                        }
                        $sqls = array();
                        $tm = time();
                        if (count($srs)==0){
                            array_push($sqls,"update bg_room set status=2,expire=".($tm+4*60*60)." where roomid='".$rid."'");
                        }
                        array_push($sqls,"update bg_game set status=1,player='".$nm[0]."' where roomid='".$rid."' and seatid=".$popped[0]);
                        array_push($sqls,"update bg_user set status=".$status.",expire=".($tm+4*60*60).",roomid='".$rid."',seatid=".$popped[0].",roleid=".$popped[1]." where extid='".$from."'");
                        if (0 == $this->task($sqls)){
                            $rname = $this->exe_sql_one("select name from bg_roles where id=".$popped[1]);
                            $content = "玩家:".$nm[0]."\n角色:".$rname[0]."\n座位号:".$popped[0]."\n\n";
                            if ($status==100){
                                $leftrs = $this->exe_sql_batch("select seatid,roleid from bg_game where roomid='".$rid."' and status=2");
                                $content = $content."置换身份候选(输入序号选择):\n";
                                $rname1 = $this->exe_sql_one("select name from bg_roles where id=".$leftrs[0][1]);
                                $rname2 = $this->exe_sql_one("select name from bg_roles where id=".$leftrs[1][1]);
                                $content = $content.$leftrs[0][0].".".$rname1[0]."\n";
                                $content = $content.$leftrs[1][0].".".$rname2[0]."\n\n";
                            }
                            $content = $content."输入\"板子\"查看本局角色列表,上帝宣布投票后可输入要投的玩家的座位号进行投票,上帝宣布投票结束后可输入\"查看投票\"查看投票结果\n";
                        }
                        else{
                            $content = "进入房间失败\n";
                        }
                    }
                }
                else{
                    $content = MENU_1;
                }
            }
        }
        return $content;
    }
    
    private function handle_status_100($key,$from,$status){
        $content = "";
        if ($status==100){
            $rid = $this->exe_sql_one("select roomid,nickname,seatid from bg_user where extid='".$from."'");
            $switch = $this->exe_sql_batch("select seatid,roleid from bg_game where roomid='".$rid[0]."' and status=2");
            $drop = $this->exe_sql_one("select seatid,roleid from bg_game where roomid='".$rid[0]."' and seatid!=".$key." and status=2");
            $sqls = array();
            $sid = $rid[2];
            array_push($sqls,"update bg_game set status=4 where roomid='".$rid[0]."' and seatid='".$drop[0]."'");
            if ($key==$switch[0][0]){
                array_push($sqls,"update bg_game set roleid=".$switch[0][1]." and status=4 where roomid='".$rid[0]."' and seatid='".$sid."'");
                array_push($sqls,"update bg_game set roleid=10 where roomid='".$rid[0]."' and seatid='".$key."'");
                array_push($sqls,"update bg_user set roleid='".$switch[0][1]."',status=101 where extid='".$from."'");
                $this->task($sqls);
                $rname = $this->exe_sql_one("select name from bg_roles where id=".$switch[0][1]);
                $content = "玩家:".$rid[1]."\n新角色:".$rname[0]."\n座位号:".$sid."\n\n";
            }
            elseif ($key==$switch[1][0]){
                array_push($sqls,"update bg_game set roleid=".$switch[1][1]." and status=4 where roomid='".$rid[0]."' and seatid='".$sid."'");
                array_push($sqls,"update bg_game set roleid=10 where roomid='".$rid[0]."' and seatid='".$key."'");
                array_push($sqls,"update bg_user set roleid=".$switch[1][1].",status=101 where extid='".$from."'");
                $this->task($sqls);
                $rname = $this->exe_sql_one("select name from bg_roles where id=".$switch[1][1]);
                $content = "玩家:".$rid[1]."\n新角色:".$rname[0]."\n座位号:".$sid."\n\n";
            }
            else{
                $content = "请输入[".$switch[0][0]."]或者[".$switch[1][0]."]选择角色";
            }
        }
        return $content;
    }

    private function parse($confstr){
        list($gods,$comm) = explode('-',$confstr);
        $glis = explode('.',$gods);
        list($lang,$min) = explode('.',$comm);
        $langct = intval($lang);
        $minct = intval($min);
        return array($glis,array($langct,$minct));
    }
    
    private function convstr($gods,$langct,$minct){
        $desc = "配置:\n";
        foreach($gods as $gid){
            $rname = $this->exe_sql_one("select name from bg_roles where id=".$gid);
            if (count($rname)>0){
                $desc = $desc.$rname[0].":1\n";
            }
        }
        $desc = $desc."狼人:".$langct."\n";
        $desc = $desc."村民:".$minct."\n";
        return $desc;
    }

    private function handle_status_2($key,$from,$status){
        $content = "";
        if ($status==2){
            $hand = $this->handle_or_not($key,2);
            if ($hand[0]){
                $kid = $hand[1];
                $content = "输入快捷方式ID,直接创建房间\n";
                $shortcuts = $this->exe_sql_batch("select id,conf from bg_shortcut where kid=".$kid);
                foreach($shortcuts as $ss){
                    $content = $content.$ss[0].":";
                    $cf = $this->parse($ss[1]);
                    foreach($cf[0] as $gid){
                        $rname = $this->exe_sql_one("select name from bg_roles where id=".$gid);
                        if (count($rname)>0){
                            $content = $content.$rname[0].",";
                        }
                    }
                    $content = $content."狼人".$cf[1][0].",村民".$cf[1][1]."\n";
                }
            }
            else{
                $cstr = $this->exe_sql_one("select conf from bg_shortcut where id='".trim($key)."'");
                if (count($cstr)>0){
                    $confstr = $cstr[0];
                    $cf = $this->parse($confstr);
                }
                else{
                    $cf = $this->parse(trim($key));
                }
                $ids = $this->exe_sql_batch("select roomid from bg_room where status=0");
                if (count($ids)==0){
                    $content = "房间已满";
                }
                else{
                    shuffle($ids);
                    $roomid = array_pop($ids);
                    $roomid = $roomid[0];
                    $gids = $cf[0];
                    $langcnt = $cf[1][0];
                    $mincnt = $cf[1][1];
                    $desc = $this->convstr($gids,$langcnt,$mincnt);
                    $rids = array();
                    $hasthief = false;
                    foreach($gids as $gid){
                        array_push($rids,$gid);
                        if ($gid==10){
                            $hasthief = true;
                        }
                    }
                    for($i=0;$i<$langcnt;$i++){
                        array_push($rids,2);
                    }
                    for($i=0;$i<$mincnt;$i++){
                        array_push($rids,1);
                    }
                    shuffle($rids);
                    if ($hasthief){
                        $role1 = array_pop($rids);
                        $role2 = array_pop($rids);
                    }
                    $sqls = array();
                    $tm = time();
                    $nm = $this->exe_sql_one("select nickname from bg_user where extid='".$from."'");
                    array_push($sqls,"insert into bg_global(name,value) values('".$roomid."','".$desc."')");
                    array_push($sqls,"insert into bg_game(roomid,seatid,roleid,status,player,live) values('".$roomid."',0,0,1,'".$nm[0]."','永生')");
                    array_push($sqls,"update bg_user set roomid='".$roomid."',seatid=0,roleid=0,status=201,expire=".($tm+4*60*60)." where extid='".$from."'");
                    array_push($sqls,"update bg_room set status=1,expire=".($tm+30*60)." where roomid='".$roomid."'");
                    for($i=0;$i<count($rids);$i++){
                        array_push($sqls,"insert into bg_game(roomid,seatid,roleid,live) values('".$roomid."',".($i+1).",".$rids[$i].",'存活')");
                    }
                    if ($hasthief){
                        array_push($sqls,"insert into bg_game(roomid,seatid,roleid,status) values('".$roomid."',".($i+1).",".$role1.",2)");
                        array_push($sqls,"insert into bg_game(roomid,seatid,roleid,status) values('".$roomid."',".($i+2).",".$role2.",2)");
                    }
                    if (0 == $this->task($sqls)){
                        $content = $content."房间号:".$roomid."\n";
                        $content = $content.$desc."\n";
                        $content = $content."输入\"检查座位\"查看座位占用情况\n";
                        $content = $content."输入\"开始投票\"等待玩家投票\n";
                        $content = $content."输入\"结束投票xx\"查看投票结果,xx为投票备注(比如:上警)\n";
                        $content = $content."输入\"注 xxx\"记录游戏进程\n";
                        $content = $content."输入\"摘要\"获取游戏全记录\n";
                        $content = $content."输入\"退出\"退出游戏,退出游戏后可创建新游戏";
                    }
                    else{
                        $content = $content."房间创建失败,请重试";
                    }
                }
            }
        }
        return $content;
    }

    private function showgame($from){
        $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
        $content = $this->exe_sql_one("select value from bg_global where name='".$rid[0]."'");
        $content = $content[0]."\n";
        return $content;
    }

    private function showvote($from){
        $vstr = $this->lastvote($from);
        $content = "投票结果\n".$vstr;
        return $content;
    }

    //非上帝玩家游戏中
    private function handle_status_101($key,$from,$status){
        $content = "";
        if ($status==101){
            $hand = $this->handle_or_not($key,101);
            if ($hand[0]){
                $kid = intval($hand[1]);
                $handlers = array(201=>"showgame",202=>"showvote");
                if (array_key_exists($kid,$handlers)){
                    $content = call_user_func(array($this,$handlers[$kid]),$from);
                }
            }
            else{
                $content = "输入\"板子\"查看本局角色配置,输入\"查看投票\"查看最近一次投票结果";
            }
        }
        return $content;
    }

    private function checkseat($from){
        $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
        $ss = $this->exe_sql_batch("select seatid,roleid,player from bg_game where roomid='".$rid[0]."'");
        $content = "房间情况:\n";
        foreach($ss as $st){
            $rname = $this->exe_sql_one("select name from bg_roles where id=".$st[1]);
            $content = $content.$st[0]." ".$rname[0]." ".$st[2]."\n";
        }
        return $content;
    }

    private function startvote($from){
        $vid = $this->buildid();
        $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
        $pls = $this->exe_sql_batch("select extid from bg_user where roomid='".$rid[0]."'");
        $sqls = array();
        foreach($pls as $pl){
            array_push($sqls,"update bg_user set voteid='".$vid."' where extid='".$pl[0]."'");
        }
        array_push($sqls,"update bg_user set status=102 where roomid='".$rid[0]."' and extid!='".$from."'");
        $this->task($sqls);
        $content = "等待玩家投票";
        return $content;
    }

    private function abst($from){
        $content = "演员表\n";
        $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
        $infs = $this->exe_sql_batch("select seatid,roleid,player,live from bg_game where roomid='".$rid[0]."' order by seatid");
        foreach($infs as $inf){
            $rname = $this->exe_sql_one("select name from bg_roles where id=".$inf[1]);
            $content = $content.$inf[0].".".$inf[2]."-".$rname[0]."-".$inf[3]."\n";
        }
        $content = $content."\n";
        $content = $content."笔记\n";
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
    
    private function handle_status_201($key,$from,$status){
        $content = "";
        if ($status==201){
            $hand = $this->handle_or_not($key,201);
            if ($hand[0]){
                $kid = intval($hand[1]);
                $handlers = array(101=>"checkseat",102=>"startvote",103=>"abst");
                if (array_key_exists($kid,$handlers)){
                    $content = call_user_func(array($this,$handlers[$kid]),$from);
                }
            }
            elseif(mb_substr($key,0,4,'utf-8')=="结束投票"){
                $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
                $votefor = mb_substr($key,4,mb_strlen($key)-4,'utf-8');
                $vstr = $this->lastvote($from);
                $content = "投票结果\n".$vstr;
                $seqid = $this->buildid();
                $sqls = array();
                array_push($sqls,"insert into bg_votedetail(idseq,roomid,vfor,vstring) values('".$seqid."','".$rid[0]."','".$votefor."','".$vstr."')");
                array_push($sqls,"update bg_user set status=101 where roomid='".$rid[0]."' and extid!='".$from."'");
                $this->task($sqls);
            }
            elseif((substr($key,0,2)=="N:") or (substr($key,0,2)=="n:") or (mb_substr($key,0,2,'utf-8')=="注 ")){
                $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
                $id = $this->buildid();
                $note = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
                $this->task(array("INSERT INTO bg_process(idseq,roomid,notes,timestamp) VALUES('".$id."','".$rid[0]."','".$note."','".date('Y-m-d H:i:s')."')"));
                $content = "笔记写入";
            }
            elseif((mb_substr($key,0,2,'utf-8')=="死 ")){
                $rid = $this->exe_sql_one("select roomid from bg_user where extid='".$from."'");
                $note = mb_substr($key,2,mb_strlen($key)-2,'utf-8');
                list($sid,$dead) = explode(' ',$note);
                $sid = trim($sid);
                $dead = trim($dead);
                $this->task(array("update bg_game set live='".$dead."' where roomid='".$rid[0]."' and seatid=".$sid));
                $content = "死因写入".$sid." ".$dead;
            }
            else{
                $content = GODMENU;
            }
        }
        return $content;
    }
    
    private function handle_status_102($key,$from,$status){
        $content = "";
        if ($status==102){
            $ids = $this->exe_sql_one("select roomid,voteid,seatid from bg_user where extid='".$from."'");
            $maxst = $this->exe_sql_one("select max(seatid) from bg_game where roomid='".$ids[0]."'");
            $hasch = $this->exe_sql_one("select count(*) from bg_game where roomid='".$ids[0]."' and roleid=10");
            $maxst = intval($maxst[0]);
            if ($hasch[0]!="0"){
                $maxst = $maxst-2;
            }
            if(!is_numeric(trim($key))){
                $content = "投票请输入有效座位号";
            }
            else{
                if (intval($key)>=0 and intval($key)<=$maxst){
                    $this->task(array("insert into bg_vote(voteid,seatid,vote) values('".$ids[1]."',".$ids[2].",".$key.")"));
                    $content = "投票完成【".$key."】,等待上帝宣布投票结束，输入\"查看投票\"查看投票结果";
                }
                else{
                    $content = "座位号【".$key."】不存在";
                }
            }
        }
        return $content;
    }

    private function handle_event($object){
        if (array_key_exists($RX_TYPE,$this->eventhandler)){
            $content = call_user_func(array($this,$this->eventhandler[$object->Event]),$object);
        }
        else{
            $content = MENU_1;
        }
        return $content;
    }

    private function handle_subscribe($from){
        $ct = $this->exe_sql_one("select count(*) from bg_user where extid='".$from."'");
        $comments = "需要输入昵称才可以进行游戏,原因在于腾讯对API调用的权限问题,个人订阅号无法获得关注人的微信昵称等信息,所以建议使用微信昵称或易于识别的名字作为游戏昵称,便于小伙伴相认,改名可以输入\"改名XX\"";
        if ($ct[0]=="0"){
            $this->task(array("insert into bg_user(extid) values('".$from."')"));
            $content = "欢迎关注桌游俱乐部,请输入您的昵称....(输入'我是XX'),".$comments;
        }
        else{
            $nlen = $this->exe_sql_one("select length(nickname),nickname from bg_user where extid='".$from."'");
            if (intval($nlen[0])>0){
                $content = "欢迎".$nlen[1]."回到桌游俱乐部";
            }
            else{
                $content = "欢迎回到桌游俱乐部,请输入您的昵称....(输入'我是XX'),".$comments;
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
    
    private function buildid(){
        list($msec, $sec) = explode(' ',microtime());
        return date('YmdHis').sprintf('%.0f', floatval($msec)*100).mt_rand(100,999);
    }

    private function lastvote($from){
        $vid = $this->exe_sql_one("select voteid from bg_user where extid='".$from."'");
        $vinfs = $this->exe_sql_batch("select seatid,vote from bg_vote where voteid='".$vid[0]."'");
        foreach($vinfs as $inf){
            $content = $content.$inf[0]."=>".$inf[1]."\n";
        }
        return $content;
    }

    //处理重置和退出 key id=3
    private function reinit($kid,$from){
        $content = "";
        if ($kid==3){
            $content = "重置完成";
            $inf = $this->exe_sql_one("select roomid,seatid,roleid,voteid,status,expire from bg_user where extid='".$from."'");
            $sqls = array();
            array_push($sqls,"update bg_user set roomid='',seatid=0,roleid=-1,voteid='',status=1,expire=0 where extid='".$from."'");
            if ($inf[2]=="0"){
                $sg = $this->exe_sql_one("select stage from bg_room where roomid='".$inf[0]."'");
                if ($sg[0]!="0"){
                    $hmy = $this->exe_sql_one("select count(*) from bg_game where roomid='".$inf[0]."' and status=1");
                    $gm = $this->exe_sql_batch("select seatid,role,player,extid,live,stage from bg_game where roomid='".$inf[0]."'");
                    foreach($gm as $p){
                        $stg = $this->exe_sql_one("select name from bg_stage where id=".$p[5]);
                        if (strlen($p[3])!=0){
                            array_push($sqls,"insert into bg_archives(extid,seatid,amount,role,ending,stage) values('".$p[3]."',".$p[0].",".$hmy[0].",'".$p[1]."','".$p[4]."','".$stg[0]."')");
                        }
                    }
                }
                array_push($sqls,"update bg_user set roomid='',seatid=0,roleid=-1,voteid='',status=1,expire=0 where roomid='".$inf[0]."'");
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
        }
        return $content;
    }

    //查看所有角色 key id=2
    private function showroles($kid,$from){
        $content = "";
        if ($kid==2){
            $roles = $this->exe_sql_batch("select id,name from bg_roles where id>0 order by id");
            $content = "所有角色\n";
            foreach($roles as $role){
                $content = $content.$role[0].".".$role[1]."\n";
            }
            $content = $content."\n输入角色名查看角色描述\n";
        }
        return $content;
    }
}
?>
