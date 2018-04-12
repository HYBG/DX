<?php
    class dxlib{
        private $db;
        private $mode;
        
        function __construct(){
            $this->db = mysqli_connect('localhost', 'root', '123456');
            $this->mode = "release";
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
                $r = mysqli_query($db, $sql);
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
    }
?>