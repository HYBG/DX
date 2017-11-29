<?php
define ("TOKEN", "dx2017");
require 'welib.php';
$ik = new iknowwe();
if (!isset($_GET['echostr'])) {
    $ik->response();
}else{
    $ik->valid();
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

    private function logger($log_content)
    {
        if(isset($_SERVER['HTTP_APPNAME'])){   //SAE
            sae_set_display_errors(false);
            sae_debug($log_content);
            sae_set_display_errors(true);
        }else if($_SERVER['REMOTE_ADDR'] != "127.0.0.1"){ //LOCAL
            $max_size = 10000;
            $log_filename = "log.xml";
            if(file_exists($log_filename) and (abs(filesize($log_filename)) > $max_size)){unlink($log_filename);}
            file_put_contents($log_filename, date('H:i:s')." ".$log_content."\r\n", FILE_APPEND);
        }
    }

    public function response(){
        $poststr = $GLOBALS["HTTP_RAW_POST_DATA"];
        $this->logger("R ".$poststr);
        $iklib = new ikwelib();
        $result = $iklib->handle_msg($poststr);
        echo $result;
    }
}
?>
