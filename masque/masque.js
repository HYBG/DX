'use strict';

var mysql      = require('mysql');

GAME_STATUS_INIT = 0;
GAME_STATUS_ONGOING = 1;
GAME_STATUS_DONE = 2;

GAME_PLAYER_STATUS_WAITING = 1;
GAME_PLAYER_STATUS_INGAME = 2;

GAME_PLAYER_INIT_MONEY = 6;
GAME_PLAYER_WIN_MONEY = 13;
GAME_PLAYER_WIN_MONEY_L = 10;


function masque(_uid,_nick,_img,_conn,_pcnt){
    var m_pcount = _pcnt;
    var m_jcount = 0;
    var m_owner = _uid;
    var m_data = null;
    var dt = Date();
    var m_gameid = 'GID'+Date().now()+String(Math.floor(Math.random()*(99-10+1)+10));
    var m_gamestatus = GAME_STATUS_INIT;
    var m_round = 0;
    var m_db = mysql.createConnection({
        host     : 'localhost',
        user     : 'root',
        password : '123456',
        database : 'masque'
    });
    m_db.connect();
    var m_flops = new Object;
    m_flops.buf = [];
    m_flops.add = function(_seatno){
        this.buf.push(_seatno);
    }
    m_flops.clear = function(){
        this.buf = [];
    }
    m_flops.couldclaim = function(_nextseat){
        var could = false;
        for(var j=0;j<this.buf.length;j++){
            if (this.buf[j]==_nextseat){
                could = true;
            }
        }
        return could;
    }
    var m_expect = new Object;
    m_expect.userid = null;
    m_expect.seat = null;
    m_expect.actions = [];
    m_expect.para = null;
    m_expect.timer = null;
    m_expect.buf = null;
    m_expect.setup = function(_seatno,expire){
        m_expect.seat = _seatno;
        m_expect.userid = m_data.seats[_seatno].userid;
        m_actions = [];
        m_expect.para = null;
        m_expect.timer = setTimeout(handle_timeout,expire);
    }
    m_expect.add = function(_name,_callback){
        this.actions.push({name:_name,callback:_callback});
    }
    m_expect.objfy = function(){
        var acts = [];
        for (var i=0;i<this.actions.length;i++){
            acts.push(this.actions[i].name);
        }
        return {seat:this.seat,actions:acts};
    }
    var m_claims = new Object;
    m_claims.seat = null;
    m_claims.role = null;
    m_claims.questions = [];
    m_claims.setup = function(_seat,_role){
        this.seat = _seat;
        this.role = _role;
    }
    m_claims.clear = function(){
        this.seat = null;
        this.role = null;
        this.questions = [];
    }
    m_claims.add = function(_seat){
        this.questions.push(_seat);
    }
    var m_execute = new Object;
    m_execute.current = null;
    m_execute.exeseats = null;
    m_execute.punishseats = null;
    m_execute.setup = function(_cur,_exe,punish){
        this.current = _cur;
        this.exeseats = _exe;
        this.punishseats = punish;
    }
    m_execute.clear = function(){
        this.current = null;
        this.exeseats = null;
        this.punishseats = null;
    }

    this.join = function(_uid,_nick,_img,_conn){
        if (m_gamestatus==GAME_STATUS_ONGOING){
            _conn.send(JSON.stringify({name:'GAME_MSG_FULL'}));
        }
        else if(m_gamestatus==GAME_STATUS_DONE){
            _conn.send(JSON.stringify({name:'GAME_MSG_DONE'}));
        }
        else{
            sitdown(_uid,_nick,_img,_conn);
            if (m_jcount==m_pcount){
                m_gamestatus = GAME_STATUS_ONGOING;
                m_expect.setup('S1',20000);
                m_expect.add('A2001',handle_A2001);
                m_round++;
                send_all(create_base_msg('GAME_MSG_START'));
            }
            else{
                send_all(create_base_msg('GAME_MSG_JOIN'));
            }
        }
    }

    this.exit = function(_seatno){
        if (m_data.gamestatus==GAME_STATUS_INIT){
            m_data.seats[_seatno].userid = null;
            m_data.seats[_seatno].nick = null;
            m_data.seats[_seatno].img = null;
            m_data.seats[_seatno].conn = null;
            m_data.seats[_seatno].good = GAME_PLAYER_STATUS_EXIT;
            m_jcount--;
            if (m_jcount==0){
                m_data.gamestatus = GAME_STATUS_DONE;
            }
            else{
                send_all(create_base_msg('GAME_MSG_JOIN'));
            }
        }
        else if (m_data.gamestatus==GAME_STATUS_ONGOING){
            m_data.seats[_seatno].good = GAME_PLAYER_STATUS_EXIT;
            m_data.seats[_seatno].conn.send(JSON.stringify({name:'GAME_MSG_EXIT'}));
        }
        else{
            m_data.seats[_seatno].conn.send(JSON.stringify({name:'GAME_MSG_EXIT'}));
        }
    }

    this.play = function(_uid,_seatno,_action,_para){
        if (is_expect(_uid,_seatno)){
            m_expect.para = _para;
            m_expect.actions[_action].callback();
        }
    }
    
    function handle_timeout(){
        
    }

    function handle_A2001(){
        clearTimeout(m_expect.timer);
        var exch = boolean(m_expect.para.exchange);
        var exchange = {first:m_expect.seat,second:m_expect.para.target};
        if (exch){
            var tag = exchange.second;
            var card = m_data.seats[tag].card;
            if (tag[0]=='T'){
                card = m_data[tag];
            }
            var c = m_data.seats[exchange.first].card;
            m_data.seats[exchange.first].card = card;
            if (tag[0]=='T'){
                m_data[tag] = c;
            }
            else{
                m_data.seats[tag].card = c;
            }
        }
        m_round++;
        m_expect.setup(next(m_expect.seat),20000);
        m_expect.add('A2001',handle_A2001);
        if (m_round>4){
            m_expect.add('A2002',handle_A2002);
            m_expect.add('A2003',handle_A2003);
        }
        send_all(create_game_msg('GAME_MSG_A2001',exchange));
    }
    
    function handle_A2002(){
        clearTimeout(m_expect.timer);
        var seatno = m_expect.seat;
        var c = m_data.seats[seatno].card;
        m_round++;
        m_expect.setup(next(m_expect.seat),20000);
        m_expect.add('A2001',handle_A2001);
        m_expect.add('A2002',handle_A2002);
        m_expect.add('A2003',handle_A2003);
        send({seatno:create_game_msg('GAME_MSG_A2002',{seat:seatno,card:c})},create_msg_A2002(GAME_MSG_A2002,null));
    }
    
    function handle_A2003(){
        clearTimeout(m_expect.timer);
        var role = m_expect.para.role;
        var seatno = m_expect.seat;
        m_claims.setup(seatno,role);
        m_expect.setup(next(m_expect.seat),20000);
        m_expect.add('A2004',handle_A2004);
        send_all(create_game_msg('GAME_MSG_A2003',{seat:seatno,claim:role}));
    }

    function handle_A2004(){
        clearTimeout(m_expect.timer);
        var answer = boolean(m_expect.para.answer);
        var nextseat = next(m_expect.seat);
        if (answer){
            m_claims.add(m_expect.seat);
        }
        if (nextseat==m_claims.seat){
            var right = [];
            var wrong = [];
            if (m_data.seats[m_claims.seat].card == m_claims.role){
                right.push(m_claims.seat);
            }
            else{
                wrong.push(m_claims.seat);
            }
            m_flops.add(m_claims.seat);
            for (var i=0;i<m_claims.questions.length;i++){
                if(m_data.seats[m_claims.questions[i]].card==m_claims.role){
                    right.push(m_claims.questions[i]);
                }
                else{
                    wrong.push(m_claims.questions[i]);
                }
                m_flops.add(m_claims.questions[i]);
            }
            m_execute.setup(m_expect.seat,right,wrong);
            execute(m_claims.role);
        }
        else{
            m_expect.setup(nextseat,20000);
            m_expect.add('A2004',handle_A2004);
            send(create_game_msg('GAME_MSG_A2003',{seat:m_claims.seat,claim:m_claims.role}));
        }
    }

    function execute(_role){
        if (_role=='C1001'){
            handle_C1001();
        }
        else if (_role=='C1002'){
            handle_C1002();
        }
        else if(_role=='C1003'){
            handle_C1003();
        }
        else if(_role=='C1004'){
            handle_C1004();
        }
        else if(_role=='C1005'){
            handle_C1005();
        }
        else if(_role=='C1006'){
            handle_C1006();
        }
        else if(_role=='C1007'){
            handle_C1007();
        }
        else if(_role=='C1008'){
            handle_C1008();
        }
        else if((_role=='C1009')||(_role=='C1010')){
            handle_C1009();
        }
        else if(_role=='C1011'){
            handle_C1011();
        }
        else if(_role=='C1012'){
            handle_C1012();
        }
        else if(_role=='C1013'){
            handle_C1013();
        }
    }

    function next_move(_msg_name,_para){
        var nextseat = next(m_execute.current);
        var could = m_flops.couldclaim(nextseat)
        m_claims.clear();
        m_expect.setup(nextseat,20000);
        m_expect.add('A2001',handle_A2001);
        m_expect.add('A2002',handle_A2002);
        if (could){
            m_expect.add('A2003',handle_A2003);
        }
        send(create_game_msg(_msg_name,_para));
        m_flops.clear();
        m_round++;
    }

    function handle_C1001(){
        if (m_execute.exeseats.length>=1){
            m_data.seats[m_execute.exeseats[0]].money += m_data.fine;
            m_data.fine = 0;
            if (m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1001',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }
    
    function handle_C1002(){
        var riches = richest();
        if (m_execute.exeseats.length>=1){
            if (richest.length==1){
                m_data.seats[m_execute.exeseats[0]].money += 2;
                m_data.seats[riches[0]].money -= 2;
                if ((m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY)||(m_data.seats[riches[0]].money<=0)){
                    this.m_gamestatus = GAME_STATUS_DONE;
                }
            }
            else{
                m_expect.setup(m_execute.exeseats[0],20000);
                m_expect.add('C1002_1',handle_C1002_1);
                send(create_game_msg('GAME_MSG_C1002_1',{richest:riches}));
                return;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1002',{executed:m_execute.exeseats,punished:m_execute.punishseats,richest:riches[0]});
        }
    }
    
    function handle_C1002_1(){
        clearTimeout(m_expect.timer);
        var pick = m_expect.para.pick
        m_data.seats[m_expect.seat].money += 2;
        m_data.seats[pick].money -= 2;
        if ((m_data.seats[m_expect.seat].money>=GAME_PLAYER_WIN_MONEY)||(m_data.seats[m_expect.para.pick].money<=0)){
            this.m_gamestatus = GAME_STATUS_DONE;
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1002',{executed:m_execute.exeseats,punished:m_execute.punishseats,richest:pick});
        }
    }
    
    function handle_C1003(){
        if (m_execute.exeseats.length>=1){
            m_data.seats[m_execute.exeseats[0]].money += 3;
            if (m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1003',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }
    
    function handle_C1004(){
        if (m_execute.exeseats.length>=1){
            m_data.seats[m_execute.exeseats[0]].money += 1;
            if (m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        if (m_execute.exeseats.length>=1){
            m_expect.setup(m_execute.exeseats[0],20000);
            m_expect.add('C1004_1',handle_C1004_1);
            send(create_game_msg('GAME_MSG_C1004_1',null));
        }
        else{
            next_move('GAME_MSG_C1004',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function handle_C1004_1(){
        clearTimeout(m_expect.timer);
        var exch = boolean(m_expect.para.exchange);
        var exchange = {executed:m_execute.exeseats,punished:m_execute.punishseats,first:m_expect.para.first,second:m_expect.para.second};
        if (exch){
            var c = m_data.seats[exchange.first].card;
            m_data.seats[exchange.first].card = m_data.seats[exchange.second].card;
            m_data.seats[exchange.second].card = c;
        }
        next_move('GAME_MSG_C1004_1',exchange);
    }

    function handle_C1005(){
        if (m_execute.exeseats.length>=1){
            m_data.seats[m_execute.exeseats[0]].money += 2;
            if (m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1005',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function handle_C1006(){
        if (m_execute.exeseats.length>=1){
            m_data.seats[m_execute.exeseats[0]].money += 1;
            var next = next(m_execute.exeseats[0]);
            var prev = prev(m_execute.exeseats[0]);
            m_data.seats[next].money -= 1;
            m_data.seats[prev].money -= 1;
            if ((m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY)||(m_data.seats[next].money<=0)||(m_data.seats[prev].money<=0)){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1006',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function handle_C1007(){
        if (m_execute.exeseats.length>=1){
            m_expect.setup(m_execute.exeseats[0],20000);
            m_expect.add('C1007_1',handle_C1007_1);
            send(create_game_msg('GAME_MSG_C1007_1',null));
        }
        else{
            punish(m_execute.punishseats);
            if (this.m_gamestatus == GAME_STATUS_DONE){
                send_all(create_base_msg('GAME_MSG_DONE'));
            }
            else{
                next_move('GAME_MSG_C1007',{executed:m_execute.exeseats,punished:m_execute.punishseats});
            }
        }
    }

    function handle_C1007_1(){
        clearTimeout(m_expect.timer);
        var tag = m_expect.para.target;
        var money = m_data.seats[m_execute.exeseats[0]].money;
        m_data.seats[m_execute.exeseats[0]].money = m_data.seats[tag].money;
        m_data.seats[tag].money = money;
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1007_1',{executed:m_execute.exeseats,punished:m_execute.punishseats,target:tag});
        }
    }

    function handle_C1008(){
        if (m_execute.exeseats.length>=1){
            m_expect.setup(m_execute.exeseats[0],20000);
            m_expect.add('C1008_1',handle_C1008_1);
            send(create_game_msg('GAME_MSG_C1008_1',null));
        }
        else{
            punish(m_execute.punishseats);
            if (this.m_gamestatus == GAME_STATUS_DONE){
                send_all(create_base_msg('GAME_MSG_DONE'));
            }
            else{
                next_move('GAME_MSG_C1007',{executed:m_execute.exeseats,punished:m_execute.punishseats});
            }
        }
    }

    function handle_C1008_1(){
        clearTimeout(m_expect.timer);
        var tag = m_expect.para.target;
        var tcard = m_data.seats[tag].card;
        if (tag[0]=='T'){
            tcard = m_data[tag];
        }
        var hold = m_data.seats[m_expect.seat].card;
        m_expect.setup(m_execute.exeseats[0],20000);
        m_expect.add('C1008_2',handle_C1008_2);
        m_expect.buf = new Object;
        m_expect.buf.first = m_expect.seat;
        m_expect.buf.second = tag;
        send(create_game_msg('GAME_MSG_C1008_2',{hand:hold,target:tcard}));
    }

    function handle_C1008_2(){
        clearTimeout(m_expect.timer);
        var exch = boolean(m_expect.para.exchange);
        var tag = m_expect.buf.second;
        if (exch){
            var card = m_data.seats[tag].card;
            if (tag[0]=='T'){
                card = m_data[tag];
            }
            var c = m_data.seats[m_expect.buf.first].card;
            m_data.seats[m_expect.buf.first].card = card;
            if (tag[0]=='T'){
                m_data[tag] = c;
            }
            else{
                m_data.seats[tag].card = c;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1008_2',{executed:m_execute.exeseats,punished:m_execute.punishseats,target:tag});
        }
        m_expect.buf = null;
    }

    function handle_C1009(){
        if (m_execute.exeseats.length==1){
            m_data.seats[m_execute.exeseats[0]].money += 1;
            if (m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        else if(m_execute.exeseats.length==2){
            m_data.seats[m_execute.exeseats[0]].money += 2;
            m_data.seats[m_execute.exeseats[1]].money += 2;
            if ((m_data.seats[m_execute.exeseats[0]].money>=GAME_PLAYER_WIN_MONEY)||(m_data.seats[m_execute.exeseats[1]].money>=GAME_PLAYER_WIN_MONEY)){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1009',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function handle_C1011(){
        if (m_execute.exeseats.length>=1){
            if (m_data.seats[m_execute.exeseats[0]].money>GAME_PLAYER_WIN_MONEY_L){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1011',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function handle_C1012(){
        if (m_execute.exeseats.length>=1){
            m_expect.setup(m_execute.exeseats[0],20000);
            m_expect.add('C1012_1',handle_C1012_1);
            send(create_game_msg('GAME_MSG_C1012_1',null));
        }
        else{
            punish(m_execute.punishseats);
            if (this.m_gamestatus == GAME_STATUS_DONE){
                send_all(create_base_msg('GAME_MSG_DONE'));
            }
            else{
                next_move('GAME_MSG_C1012',{executed:m_execute.exeseats,punished:m_execute.punishseats});
            }
        }
    }

    function handle_C1012_1(){
        clearTimeout(m_expect.timer);
        m_expect.setup(m_expect.para.target,20000);
        m_expect.add('C1012_2',handle_C1012_2);
        send(create_game_msg('GAME_MSG_C1012_1',null));
    }
    
    function handle_C1012_2(){
        clearTimeout(m_expect.timer);
        var iam = m_expect.para.card;
        var tobe = m_data.seats[m_expect.seat].card;
        m_flops.add(m_expect.seat);
        if (iam == tobe){
            next_move('GAME_MSG_C1012_2',{executed:m_execute.exeseats,punished:m_execute.punishseats,target:m_expect.seat,claim:iam,being:tobe});
        }
        else{
            m_data.seats[m_expect.seat].money -= 4;
            m_data.seats[m_execute.exeseats[0]].money += 4;
            punish(m_execute.punishseats);
            if (this.m_gamestatus == GAME_STATUS_DONE){
                send_all(create_base_msg('GAME_MSG_DONE'));
            }
            else{
                next_move('GAME_MSG_C1012_2',{executed:m_execute.exeseats,punished:m_execute.punishseats,target:m_expect.seat,claim:iam,being:tobe});
            }
        }
    }

    function handle_C1013(){
        if (m_execute.exeseats.length>=1){
            if (m_data.seats[m_execute.exeseats[0]].money<10){
                m_data.seats[m_execute.exeseats[0]].money = 10;
            }
        }
        punish(m_execute.punishseats);
        if (this.m_gamestatus == GAME_STATUS_DONE){
            send_all(create_base_msg('GAME_MSG_DONE'));
        }
        else{
            next_move('GAME_MSG_C1013',{executed:m_execute.exeseats,punished:m_execute.punishseats});
        }
    }

    function init(_uid,_nick,_img,_conn){
        var cards = undefined;
        if (m_pcount<=4){
            m_pcount=4;
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1005','S4'],['C1006','T1'],['C1011','T2']];
        }
        else if (m_pcount==5){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1005','S4'],['C1007','S5'],['C1011','T2']];
        }
        else if (m_pcount==6){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1005','S4'],['C1007','S5'],['C1011','S6']];
        }
        else if (m_pcount==7){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1005','S4'],['C1006','S5'],['C1007','S6'],['C1008','S7']];
        }
        else if (m_pcount==8){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C1007','S6'],['C1009','S7'],['C1010','S8']];
        }
        else if (m_pcount==9){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C1007','S6'],['C1009','S7'],['C1010','S8'],['C1011','S9']];
        }
        else if (m_pcount==10){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C1007','S6'],['C1008','S7'],['C1009','S8'],['C1010','S9'],['C1011','S10']];
        }
        else if (m_pcount==11){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C107','S6'],['C1008','S7'],['C1009','S8'],['C1010','S9'],['C1011','S10'],['C1012','S11']];
        }
        else if (m_pcount==12){
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C1007','S6'],['C1008','S7'],['C1009','S8'],['C1010','S9'],['C1011','S10'],['C1012','S11'],['C1013','S12']];
        }
        else {
            m_pcount=13;
            cards = [['C1001','S1'],['C1002','S2'],['C1003','S3'],['C1004','S4'],['C1005','S5'],['C1006','S6'],['C1007','S7'],['C1008','S8'],['C1009','S9'],['C1010','S10'],['C1011','S11'],['C1012','S12'],['C1013','S13']];
        }

        for (var i=0;i<cards.length;i++){
            var pos = Math.floor(Math.random()*cards.length);
            var c = cards[i][0];
            cards[i][0] = cards[pos][0];
            cards[pos][0] = c;
        }

        m_data = new Object;
        m_data.fine = 0;
        if (m_pcount==4){
            m_data.T1 = cards[4][1];
            m_data.T2 = cards[5][1];
        }
        else if (m_pcount==5){
            m_data.T1 = cards[5][1];
        }
        m_data.seats = new Object;
        for (var j=0;j<cards.length;j++){
            if (cards[j][1][0]!='T'){
                var s = new Object;
                s.card = cards[j][0];
                s.userid = null;
                s.nick = null;
                s.img = null;
                s.good = GAME_PLAYER_STATUS_WAITING;
                s.money = GAME_PLAYER_INIT_MONEY;
                s.conn = null;
                m_data.seats[cards[j][1]] = s;
            }
        }
        m_data.objfy_short = function(){
            var data = new Object;
            data.fine = this.fine;
            data.seats = new Object;
            for (var s in this.seats){
                data.seats[s].money = this.seats[s].money;
                data.seats[s].good = this.seats[s].good;
            }
            return data;
        }
        m_data.objfy_long = function(){
            var data = new Object;
            data.fine = this.fine;
            if ('T1' in this){
                data.T1 = this.T1;
            }
            if ('T2' in this){
                data.T2 = this.T2;
            }
            data.seats = new Object;
            for (var s in this.seats){
                data.seats[s].card = this.seats[s].card;
                data.seats[s].userid = this.seats[s].userid;
                data.seats[s].nick = this.seats[s].nick;
                data.seats[s].img = this.seats[s].img;
                data.seats[s].money = this.seats[s].money;
                data.seats[s].good = this.seats[s].good;
            }
            return data;
        }
        var sno = 'S'+Math.ceil(Math.random()*m_pcount);
        m_data.seats[sno].userid = _uid;
        m_data.seats[sno].nick = _nick;
        m_data.seats[sno].img = _img;
        m_data.seats[sno].conn = _conn;
        m_jcount = 1;
    }
    
    function next(_seat){
        var no = Number(_seat.substring(1));
        var nextno = no+1;
        if (no==m_pcount){
            nextno = 1;
        }
        return 'S'+nextno;
    }

    function prev(_seat){
        var no = Number(_seat.substring(1));
        var prevno = no-1;
        if (no==1){
            prevno = m_pcount;
        }
        return 'S'+prevno;
    }

    function create_base(_name,ingame){
        var msg = new Object;
        msg.name = _name;
        msg.gamestatus = m_gamestatus;
        msg.gameid = m_gameid;
        if (ingame){
            msg.seats = m_data.objfy_short();
            msg.expect = m_expect.objfy();
        }
        return msg;
    }

    function create_base_msg(_name){
        var msg = create_base(_name,false);
        msg.seats = m_data.objfy_long();
        return JSON.stringify(msg);
    }

    function send_all(_msg){
        for (var s in m_data.seats){
            if ((m_data.seats[s].conn!=undefined)&&(m_data.seats[s].conn!=null)){
                m_data.seats[s].conn.send(_msg);
            }
        }
    }
    
    function send(spec,msg){
        for (var s in m_data.seats){
            if ((m_data.seats[s].conn!=undefined)&&(m_data.seats[s].conn!=null)){
                if (s in spec){
                    m_data.seats[s].conn.send(spec[s]);
                }
                else{
                    m_data.seats[s].conn.send(msg);
                }
            }
        }
    }

    function sitdown(_uid,_nick,_img,_conn){
        var seq = 0;
        var inx = Math.ceil(Math.random()*(m_pcount-m_jcount));
        for (var s in m_data.seats){
            var i = Math.ceil(Math.random()*(m_pcount-m_jcount));
            if (m_data.seats[s].userid!=null){
                seq++;
                if (seq==inx){
                    m_data.seats[s].userid = _uid;
                    m_data.seats[s].nick = _nick;
                    m_data.seats[s].img = _img;
                    m_data.seats[s].conn = _conn;
                    m_jcount++;
                    break;
                }
            }
        }
    }

    function is_expect(_uid,_seatno){
        if (m_expect.seat==_seatno){
            if (m_data.seats[_seatno].userid==_uid){
                return true;
            }
        }
        return false;
    }
    
    function punish(_punishseats){
        for(var i=0;i<_punishseats.length;i++){
            m_data.seats[_punishseats[i]].money -= 1;
            m_data.fine += 1;
            if (m_data.seats[_punishseats[i]].money<=0){
                this.m_gamestatus = GAME_STATUS_DONE;
            }
        }
    }

    function richest(){
        var money = 0;
        for (var s in m_data.seats){
            if (m_data.seats[s].money>money){
                money = m_data.seats[s].money;
            }
        }
        var riches = [];
        for (var s in m_data.seats){
            if(m_data.seats[s].money==money){
                riches.push(s);
            }
        }
        return riches;
    }

    function create_game_msg(_name,_para){
        var msg = create_base(_name,true);
        if ((_para!=undefined)&&(_para!=null)){
            msg.para = _para;
        }
        return JSON.stringify(msg);
    }
}

export.masque=masque;