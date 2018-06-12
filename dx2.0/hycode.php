<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<?php
require "../phplib/dx.php";
$code = $_POST['code'];
if (!isset($code)){
    parse_str($_SERVER["QUERY_STRING"]);
}
if (!isset($code)){
    echo "无相应数据";
}
else{
    $dx = new dxlib();
    if ($dx->isok()){
        if ($dx->select_db("dx")){
            $name = $dx->exe_sql_one("select name from dx.iknow_name where code='".$code."'");
            $mk = "SZ";
            if (substr($code,0,1)=="6"){
                $mk = "SH";
            }
            echo "<title>".$name[0]."(".$mk.$code.")</title>";
        }
    }
    $h2 = $name[0]."(".$mk.$code.")";
}
?>
<style type="text/css">
*{
    margin:0;
    padding:0;
}
h2{
    margin:20px;
    text-align:center;
}
tr{
    text-align:center;
}
td.sorted{
    background-color:#FFD000;
}
.columnname{
    width:10%;
    height:20px;
    cursor:pointer;
}
.columnno{
    width:5%;
    height:20px;
    cursor:pointer;
}
</style>
</head>
<body>
<div id="container" style="-webkit-box-orient:vertical;">
<div id="header"><h1 style="text-shadow:10px 10px 10px #FF8C00;color:#FF4500;padding:20px;text-align:center;font-size:400%;">汉尧科技</h1>
</div>
<?php
echo "<div><h2>".$h2."</h2></div>";
?>
<div id='table'>
   <table class="table table-striped" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnno">#</th>
          <th class="columnname">日期</th>
          <th class="columnname">样本</th>
          <th class="columnname">上破(%)</th>
          <th class="columnname">下破(%)</th>
          <th class="columnname">阳线(%)</th>
          <th class="columnname">高点(%)</th>
          <th class="columnname">低点(%)</th>
          <th class="columnname">今收</th>
        </tr>
      </thead>
      <tbody id="tbody">
<?php
    $data = $dx->exe_sql_batch("select date,count,100*hbp,100*lbp,100*kp,100*hpp,100*lpp from dx.iknow_tell2 where code='".$code."' order by date desc");
    for($i=0; $i<count($data); $i++){
        $close = $dx->exe_sql_one("select close from dx.iknow_data where code='".$code."' and date='".$data[$i][0]."'");
        echo "<tr><td>".($i+1)."</td><td>".$data[$i][0]."</td><td>".$data[$i][1]."</td><td>".$data[$i][2]."</td><td>".$data[$i][3]."</td><td>".$data[$i][4]."</td><td>".$data[$i][5]."</td><td>".$data[$i][6]."</td><td>".$close[0]."</td></tr>";
    }
?>
      </tbody>
    </table>
  </div>
<script type="text/javascript">

</script>
</body>
</html>