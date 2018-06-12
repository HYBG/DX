<?php
    class hylib{
        private $db;
        private $mode;

        function __construct($user='root',$passwd){
            $this->db = mysqli_connect('localhost', $user, $passwd);
            $this->mode = "release";
            $this->user = $user;
            $this->passwd = $passwd;
        }

        function __destruct(){
            mysqli_close($this->db);
        }
        
        function setmode($mode){
            $this->mode = $mode;
        }
        
        function isok(){
            if (!$this->db){
                return False;
            }
            return True;
        }
        
        function select_db($dbname){
            $selected = mysqli_select_db($this->db, $dbname);
            if (!$selected){
                return False;
            }
            return True;
        }
        
        function exe_sql_batch($sql){
            if ($this->mode=="debug"){
                echo $sql."\n";
            }
            $a = array();
            $result = mysqli_query($this->db, $sql);
            while($ret=mysqli_fetch_row($result)){
                array_push($a,$ret);
            }
            return $a;
        }
        
        function exe_sql_one($sql){
            if ($this->mode=="debug"){
                echo $sql."\n";
            }
            $a = array();
            $result = mysqli_query($this->db, $sql);
            if($ret=mysqli_fetch_row($result)){
                foreach($ret as $item){
                    array_push($a,$item);
                }
            }
            return $a;
        }

        function task($sqls){
            foreach($sqls as $sql){
                $r = mysqli_query($this->db, $sql);
                if (!$r){
                    if ($this->mode=="debug"){
                        echo "task:execute sql[".$sql."] failed";
                    }
                    mysql_query("ROLLBACK");
                    return False;
                }
            }
            mysql_query("COMMIT");
            return True;
        }
        
        function dump($sql,$filename){
            if ($this->mode=="debug"){
                echo $sql."\n";
            }
            $result = mysqli_query($this->db, $sql);
            while($ret=mysqli_fetch_row($result)){
                $line = "";
                foreach($ret as $item){
                    $line = $line.$item.",";
                }
                $line = substr($line,0,-1);
                file_put_contents($filename,$line."\n",FILE_APPEND);
            }
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
        function rtprices($codes){
            $url = "";
            foreach($codes as $code){
                $bd = "sz";
                if ($code[0]=='6'){
                    $bd = "sh";
                }
                $url = $url.$bd.$code.",";
            }
            $url = "http://hq.sinajs.cn/list=".substr($url,0,-1);
            $data = file_get_contents($url);
            $lines = explode("\n",$data);
            $hq = array();
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
                    $volwy = $ps[9];
                    $lastclose = $ps[2];
                    $dt = $ps[30];
                    $time = $ps[31];
                    array_push($hq,array($codes[$i],$open,$high,$low,$close,$volwy,$buy,$sell,$lastclose,$dt,$time));
                }
                $i++;
            }
            return $hq;
        }
        
        function importcsv($data,$dbname,$tablename){
            $csvfn = "";
            if (is_file($csvfn)){
                unlink($csvfn);
            }
            foreach($data as $row){
                $line = "";
                foreach($row as $item){
                    $line = $line.$item.",";
                }
                $line = substr($line,0,-1);
                file_put_contents($csvfn,$line."\n",FILE_APPEND);
            }
            $cwd = getcwd();
            chdir("");
            $sqlfile = fopen("", "w") or die("Unable to open file!");
            fwrite($sqlfile, "");
            fclose($sqlfile);
            exec("mysql -u ".$this->user." ".$dbname."<".$sqlfile." -p\"".$this->passwd."\"");
            chdir($cwd);
        }
    }
?>