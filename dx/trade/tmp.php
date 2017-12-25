<?php

$ikt = new iktrader();
$ikt->fillcode();

class iktrader{
    private $db;

    function __construct(){
        $this->db = mysqli_connect('localhost', 'root', '123456');
        if (!$this->db){
            echo "iktradelib",IK_LOG_ERROR,"cannot connect db";
        }
        $selected = mysqli_select_db($this->db, "trader");
        if (!$selected){
            echo "iktradelib",IK_LOG_ERROR,"db not found";
        }
    }

    function __destruct(){
        mysqli_close($this->db);
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

    private function exe_sql_one($sql){
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
            echo "exe_sql_one:execute sql[".$sql."] failed\n";
        }
        return $a;
    }

    private function exe_sql_batch($sql){
        $a = array();
        $result = mysqli_query($this->db, $sql);
        if ($result){
            while($ret=mysqli_fetch_row($result)){
                array_push($a,$ret);
            }
        }
        else{
            echo "exe_sql_batch:execute sql[".$sql."] failed\n";
        }
        return $a;
    }

    private function task($sqls,$commi=true){
        foreach($sqls as $sql){
            $r = mysqli_query($this->db, $sql);
            if (!$r){
                mysql_query("ROLLBACK");
                echo "task:execute sql[".$sql."] failed,task rollback\n";
                return 1;
            }
            echo "task:execute sql[".$sql."] successfully\n";
        }
        if ($commi){
            mysql_query("COMMIT");
        }
        return 0;
    }
    
    public function fillcode(){
        $codes = $this->exe_sql_batch("select code,name,bdcode,bdname from hy.ikbill_name order by code");
        $sqls = array();
        foreach($codes as $row){
            array_push($sqls,"insert into trader_code(code,name,boardcode,boardname,status) values('".$row[0]."','".$row[1]."','".$row[2]."','".$row[2]."',1)");
        }
        $this->task($sqls);
    }

}


?>