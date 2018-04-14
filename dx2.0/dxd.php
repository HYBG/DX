<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="./js/jquery-3.3.1.js"></script>
<title>汉尧科技</title>
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
require "../phplib/dx.php";
parse_str($_SERVER["QUERY_STRING"]);
if (!isset($date)){
    echo "无相应数据";
}
else{
    $dx = new dxlib();
    if ($dx->isok()){
        if ($dx->select_db("dx")){
            $prev = $dx->exe_sql_one("select date from iknow_tell where date<'".$date."' order by date desc limit 1");
            $next = $dx->exe_sql_one("select date from iknow_tell where date>'".$date."' order by date limit 1");
            echo "<div><h2>";
            if (count($prev)>0){
                echo "<a href=\"dxd.php?date=".$prev[0]."\">前一日</a>&nbsp;".$date."&nbsp;";
            }
            if (count($next)>0){
                echo "<a href=\"dxd.php?date=".$next[0]."\">后一日</a>";
            }
            echo "</h2></div>";
        }
    }
}
?>
<div id='find' style="margin:0 auto;width:90%">
<input type='text' id='code'/><button id='goto'>GO TO</button>
</div>
<div id='table'>
   <table class="table table-striped" style="margin:0 auto;width:90%">
      <thead style="background-color:#E0EEEE">
        <tr>
          <th class="columnno">#</th>
          <th class="columnname">代码</th>
          <th class="columnname">名称</th>
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
    $data = $dx->exe_sql_batch("select code,100*hpp,100*lpp,100*kp from iknow_tell where date='".$date."' order by code");
    echo "var data = new Array();\n";
    foreach($data as $row){
        $name = $dx->exe_sql_one("select name from iknow_name where code='".$row[0]."'");
        $name = $name[0];
        $volwy = $dx->exe_sql_one("select volwy from iknow_data where code='".$row[0]."' and date='".$date."'");
        $volwy = $volwy[0];
        echo "data.push(Array(\"".$row[0]."\",\"".$name."\",".$row[1].",".$row[2].",".$row[3].",".$volwy."));\n";
    }
?>

var code = document.getElementById('code');
var btn = document.getElementById('goto');
btn.onclick=function(){
    var obj = document.getElementById(code.value);
    var oPos = obj.offsetTop;
    return window.scrollTo(0, oPos-36);
};

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
        a.setAttribute("href","dxcode.php?code="+data[i][0]);
        a.setAttribute("target","_blank");
        code.appendChild(a);
        row.appendChild(code);
        var name = document.createElement('td');
        name.innerHTML = data[i][1];
        row.appendChild(name);
        var hp = document.createElement('td');
        hp.innerHTML = data[i][2];
        row.appendChild(hp);
        var lp = document.createElement('td');
        lp.innerHTML = data[i][3]; 
        row.appendChild(lp);
        var kv = document.createElement('td');
        kv.innerHTML = data[i][4]; 
        row.appendChild(kv);
        var vol = document.createElement('td');
        vol.innerHTML = data[i][5]; 
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