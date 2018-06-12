<?php
    require dirname(__file__)."/hylib.php";
    $lr = new hylib('root','123456');
    if ($lr->isok()){
        if ($lr->select_db('langren')){
            while (true){
                $data = $lr->exe_sql_batch("select roomid,created from lr_room");
                $time = time();
                $sqls = array();
                foreach($data as $row){
                    if ($time-intval($row[1])>20*60){
                        array_push($sqls,"delete from lr_room where roomid='".$row[0]."'");
                    }
                }
                if (count($sqls)!=0){
                    $lr->task($sqls);
                    array_splice($sqls,0,count($sqls));
                }
                sleep(3);
            }
        }
        echo "select db langren error";
    }
?>