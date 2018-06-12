<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<?php
require "../phplib/dx.php";
parse_str($_SERVER["QUERY_STRING"]);
if (!isset($date)){
    echo "无相应数据";
}
else{
    $dx = new dxlib();
    if ($dx->isok()){
        if ($dx->select_db("dx")){
            echo "<title>汉尧科技(".$date.")</title>";
        }
    }
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
    $prev = $dx->exe_sql_one("select date from iknow_tell2 where date<'".$date."' order by date desc limit 1");
    $next = $dx->exe_sql_one("select date from iknow_tell2 where date>'".$date."' order by date limit 1");
    echo "<div><h2>";
    if (count($prev)>0){
        echo "<a href=\"hydxd.php?date=".$prev[0]."\">prev</a>";
    }
    echo "&nbsp;".$date."&nbsp;";
    if (count($next)>0){
        echo "<a href=\"hydxd.php?date=".$next[0]."\">next</a>";
    }
    echo "</h2></div>";
?>
<div id='find' style="margin:0 auto;width:90%">
<form id="inquiry" name="inquiry" method="post" action="hycode.php" target="_blank">
<input type="text" name="code" id="code" size="20" maxlength="6"/>
<label><input type="submit" name="Submit" value="GO" /></label>
</form>
<!--<input type='text' id='code' /><button id='goto' action="dxcode.php">GO TO</button>-->
</div>
<div id='table'>
   <table class="table table-striped" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnno">#</th>
          <th class="columnname">代码</th>
          <th class="columnname">名称</th>
          <th class="columnname">匹配量</th>
          <th class="columnname">上破概率(%)</th>
          <th class="columnname">下破概率(%)</th>
          <th class="columnname">高点概率(%)</th>
          <th class="columnname">低点概率(%)</th>
          <th class="columnname">阳线概率(%)</th>
          <th class="columnname">成交量(万元)</th>
        </tr>
      </thead>
      <tbody id="tbody">
      </tbody>
    </table>
  </div>
<script type="text/javascript">
<?php
    $data = $dx->exe_sql_batch("select code,count,100*hbp,100*lbp,100*hpp,100*lpp,100*kp from iknow_tell2 where date='".$date."' order by lpp desc");
    echo "var data = new Array();\n";
    foreach($data as $row){
        $name = $dx->exe_sql_one("select name from iknow_name where code='".$row[0]."'");
        $name = $name[0];
        $volwy = $dx->exe_sql_one("select volwy from iknow_data where code='".$row[0]."' and date='".$date."'");
        $volwy = $volwy[0];
        echo "data.push(Array(\"".$row[0]."\",\"".$name."\",".$row[1].",".$row[2].",".$row[3].",".$row[4].",".$row[5].",".$row[6].",".$volwy."));\n";
    }
?>

function fill(){
    var tbody = document.getElementById("tbody");
    for (i=0,len=data.length;i<len;i++){
        var row = document.createElement('tr');
        row.setAttribute("id",data[i][0]);
        var seq = document.createElement('td');
        seq.innerHTML = i+1;
        row.appendChild(seq);
        var code = document.createElement('td');
        var a = document.createElement('a');
        a.innerHTML = data[i][0]; 
        a.setAttribute("href","hycode.php?code="+data[i][0]);
        a.setAttribute("target","_blank");
        code.appendChild(a);
        row.appendChild(code);
        var name = document.createElement('td');
        name.innerHTML = data[i][1];
        row.appendChild(name);
        var cnt = document.createElement('td');
        cnt.innerHTML = data[i][2];
        row.appendChild(cnt);
        var hb = document.createElement('td');
        hb.innerHTML = data[i][3];
        row.appendChild(hb);
        var lb = document.createElement('td');
        lb.innerHTML = data[i][4];
        row.appendChild(lb);
        var hp = document.createElement('td');
        hp.innerHTML = data[i][5];
        row.appendChild(hp);
        var lp = document.createElement('td');
        lp.innerHTML = data[i][6]; 
        row.appendChild(lp);
        var kv = document.createElement('td');
        kv.innerHTML = data[i][7]; 
        row.appendChild(kv);
        var vol = document.createElement('td');
        vol.innerHTML = data[i][8]; 
        row.appendChild(vol);
        tbody.appendChild(row);
    }
}

$(document).ready(function(){
    fill();
    var sort_direction = 1; //排序标志，1为升序，-1为降序
    $('th').each(function(i){
        $(this).click(function(){
            if(sort_direction==1){
                sort_direction=-1;
            }else{
                sort_direction=1;
            }
            //获得行数组
            var trarr=$('table').find('tbody > tr').get();
            //数组排序
            trarr.sort(function(a, b){
                var col1 = $(a).children('td').eq(i).text().toUpperCase();
                var col2 = $(b).children('td').eq(i).text().toUpperCase();
                if (i!=2){
                    col1 = parseFloat(col1);
                    col2 = parseFloat(col2);
                }
                return(col1 < col2) ? -sort_direction: (col1 > col2) ? sort_direction: 0;
                        //返回-1表示a>b降序,返回1表示a<b升序,否则为0相等
                        /*
                         * if (col1 > col2) {
                            return sort_direction;
                        }else if(col1 <col2){
                            return -sort_direction;
                        }else{
                            return 0;
                        }*/
                });
            $.each(trarr, function(i,row){
                //将排好序的数组重新填回表格
                $('tbody').append(row);
            });
        });
    });
});

</script>
</body>
</html>