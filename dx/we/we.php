<?php
define ("TOKEN", "dx2017");
require 'welib.php';
$ik = new iknowwe();
if(isset($_GET['echostr'])){
    $ik->valid();
}
else{
    $ik->response();
}

class iknowwe{
    public function valid(){
        $echostr = $_GET["echostr"];
        if($this->checksign()){
            echo $echostr;
            exit;
        }
    }

    private function checksign(){
        $signature = $_GET["signature"];
        $timestamp = $_GET["timestamp"];
        $nonce = $_GET["nonce"];
        $token = TOKEN;
        $tmparr = array($token, $timestamp, $nonce);
        sort($tmparr, SORT_STRING);
        $tmpstr = implode($tmparr);
        $tmpstr = sha1($tmpstr);
        if($tmpstr == $signature){
            return true;
        }else{
            return false;
        }
    }

    public function response(){
        $iklib = new ikwelib();
        $poststr = $GLOBALS["HTTP_RAW_POST_DATA"];
        $result = $iklib->handle_msg($poststr);
        echo $result;
    }
}
?>
