<?php

class ikwelib{
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
        
    public function handle_msg($poststr){
        if (!empty($poststr)){
            $obj = simplexml_load_string($poststr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $RX_TYPE = trim($obj->MsgType);
            switch ($RX_TYPE){
                case "text":
                    return $this->receive_text($obj);
                case "event":
                    return $this->receive_event($obj);
                default:
                    return "暂不支持[".$RX_TYPE."]类型消息";
            }
        }
        else{
            return "";
        }
    }
    
    private function handle_click($object){
        return "";
    }

    private function receive_text($object){
        switch ($object->Content){
            case "文本":
                $content = "这是个文本消息";
                break;
            default:
                $content = date("Y-m-d H:i:s",time());
                break;
        }
        $result = $this->transmit_text($object, $content);
        return $result;
    }

    private function receive_event($object){
        switch ($object->Event){
            case "subscribe":
                $content = "欢迎关注冬夏科技";
                break;
            case "unsubscribe":
                $content = "取消关注";
                break;
            case "SCAN":
                $content =  "扫描场景 ".$object->EventKey;
                break;
            case "CLICK":
                $content = $this->handle_click($object);
                break;
            case "LOCATION":
                $content =  "上传位置：纬度 ".$object->Latitude.";经度 ".$object->Longitude;
                break;
            case "VIEW":
                $content = "跳转链接 ".$object->EventKey;
                break;
            default:
                $content = "receive a new event: ".$object->Event;
                break;
        }
        $result = $this->transmit_text($object, $content);
        return $result;
    }

    private function transmit_text($object, $content){
        $textTpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content></xml>";
        $result = sprintf($textTpl, $object->FromUserName, $object->ToUserName, time(), $content);
        return $result;
    }
}
?>
