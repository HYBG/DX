'use strict';

GAME_STATUS_INIT = 0;
GAME_STATUS_ONGOING = 1;
GAME_STATUS_DONE = 2;

GAME_PLAYER_STATUS_WAITING = 1;
GAME_PLAYER_STATUS_INGAME = 2;

GAME_PLAYER_INIT_MONEY = 6;

GAME_MSG_FULL = 'GAME_MSG_FULL';
GAME_MSG_DONE = 'GAME_MSG_DONE';
GAME_MSG_START = 'GAME_MSG_START';
GAME_MSG_JOIN = 'GAME_MSG_JOIN';
GAME_MSG_A2001 = 'GAME_MSG_A2001';
GAME_MSG_A2002 = 'GAME_MSG_A2002';
GAME_MSG_A2003 = 'GAME_MSG_A2003';

function masque(_uid,_nick,_img,_conn,_pcnt){
    var m_pcount = _pcnt;
    var m_jcount = 0;
    var m_owner = _uid;
    var m_data = null;
    var m_conns = {};
    var m_gameid = 'GID'+
    var m_gamestatus = GAME_STATUS_INIT;
    var m_round = 0;
    var m_expect = new Object;
    m_expect.userid = null;
    m_expect.seat = null;
    m_expect.actions = [];
    m_expect.para = null;
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

    this.join = function(_uid,_nick,_img,_conn){
        if (m_gamestatus==GAME_STATUS_ONGOING){
            _conn.send(JSON.stringify({name:GAME_MSG_FULL}));
        }
        else if(m_gamestatus==GAME_STATUS_DONE){
            _conn.send(JSON.stringify({name:GAME_MSG_DONE}));
        }
        else{
            sitdown(_uid,_nick,_img,_conn);
            if (m_jcount==m_pcount){
                m_gamestatus = GAME_STATUS_ONGOING;
                m_expect.setup('S1',20000);
                m_expect.add('A2001',handle_A2001);
                m_round++;
                send_all(create_base_msg(GAME_MSG_START));
            }
            else{
                send_all(create_base_msg(GAME_MSG_JOIN));
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
                send_all(create_base_msg(GAME_MSG_JOIN));
            }
        }
        else if (m_data.gamestatus==GAME_STATUS_ONGOING){
            m_data.seats[_seatno].good = GAME_PLAYER_STATUS_EXIT;
            m_data.seats[_seatno].conn.send(JSON.stringify({name:GAME_MSG_EXIT}));
        }
        else{
            m_data.seats[_seatno].conn.send(JSON.stringify({name:GAME_MSG_EXIT}));
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
        send_all(create_msg_A2001(exchange));
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
        send({seatno:create_msg_A2002({seat:seatno,card:c})},create_msg_A2002(null));
    }
    
    function handle_A2003(){
        clearTimeout(m_expect.timer);
        var role = m_expect.para.role;
        var seatno = m_expect.seat;
        m_claims.setup(seatno,role);
        m_expect.setup(next(m_expect.seat),20000);
        m_expect.add('A2004',handle_A2004);
        send_all(create_msg_A2003({seat:seatno,claim:role}));
    }

    function handle_A2004(){
        clearTimeout(m_expect.timer);
        var answer = boolean(m_expect.para.answer);
        var nextseat = next(m_expect.seat);
        if (nextseat==m_claims.seat){
            
        }
        else{
            m_expect.setup(nextseat,20000);
            m_expect.add('A2004',handle_A2004);
            send(create_msg_A2003({seat:m_claims.seat,claim:m_claims.role}));
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
        m_conns[sno] = _conn;
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
        for (var s in m_conns){
            if ((m_conns[s]!=undefined)&&(m_conns[s]!=null)){
                m_conns[s].send(_msg);
            }
        }
    }
    
    function send(spec,msg){
        for (var s in m_conns){
            if ((m_conns[s]!=undefined)&&(m_conns[s]!=null)){
                if (s in spec){
                    m_conns[s].send(spec[s]);
                }
                else{
                    m_conns[s].send(msg);
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
                    m_conns[s] = _conn;
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

    function create_msg_A2001(last){
        var msg = create_base(GAME_MSG_A2001,true);
        msg.exchange = last;
        return JSON.stringify(msg);
    }

    function create_msg_A2002(last){
        var msg = create_base(GAME_MSG_A2002,true);
        if ((last!=undefined)&&(last!=null)){
            msg.check = last;
        }
        return JSON.stringify(msg);
    }

    function create_msg_A2003(last){
        var msg = create_base(GAME_MSG_A2003,true);
        if ((last!=undefined)&&(last!=null)){
            msg.claim = last;
        }
        return JSON.stringify(msg);
    }
}

export.masque=masque;