/*******************
sort table body
*******************/
function sort_tbody(sortedindex){
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
                sortedindex.find(function(value){
                    if(value === i){
                        col1 = parseFloat(col1);
                        col2 = parseFloat(col2);
                    }
                });
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
}
