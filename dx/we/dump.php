<?php


require 'welib.php';
$ik = new ikwelib();
$data = $ik->exe_sql_batch("select code,name,bdcode,bdname from ikmom_name order by code");
$ofn = "name.csv";
foreach($data as $row){
    $line = trim($row[0]).",".trim($row[1]).",".trim($row[2]).",".trim($row[3])."\n";
    file_put_contents($ofn,$line,FILE_APPEND);
}

?>
