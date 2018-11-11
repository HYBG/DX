'use strict';

GAME_STATUS_INIT = 0;
GAME_STATUS_ONGOING = 1;
GAME_STATUS_DONE = 2;

GAME_PLAYER_STATUS_WAITING = 1;
GAME_PLAYER_STATUS_INGAME = 2;

GAME_PLAYER_INIT_MONEY = 6;

GAME_MSG_FULL = 'GAME_MSG_FULL';
GAME_MSG_DONE = 'GAME_MSG_DONE';

function masque(_uid,_nick,_img,_conn,_pcnt){
    var m_pcount = _pcnt;
    var m_jcount = 0;
    var m_owner = _uid;
    var m_data = {};
    var m_conns = {};
    var m_gameid = 'GID'+
    var m_gamestatus = GAME_STATUS_INIT;

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
                send_all(GAME_MSG_START);
            }
            else{
                send_all(GAME_MSG_JOIN);
            }
        }
    }
    
    function exit(_seatno){
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
                send_all(GAME_MSG_JOIN);
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

        m_data['fine'] = 0;
        if (m_pcount==4){
            m_data['T1'] = cards[4][1];
            m_data['T2'] = cards[5][1];
        }
        else if (m_pcount==5){
            m_data['T1'] = cards[5][1];
        }
        var seats = new Object;
        for (var j=0;j<cards.length;j++){
            if (cards[j][1][0]!='T'){
                var s = new Object;
                s.card = cards[j][0];
                s.userid = null;
                s.nick = null;
                s.img = null;
                s.good = GAME_PLAYER_STATUS_WAITING;
                s.money = GAME_PLAYER_INIT_MONEY;
                seats[cards[j][1]] = s;
            }
        }
        m_data['seats'] = seats;
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
    
    function create_msg(_name){
        var msg = new Object;
        msg.name = _name;
        msg.gamestatus = m_gamestatus;
        msg.gameid = m_gameid;
        msg.seats = m_data.seats;
        return msg;
    }
    
    function send_all(_name){
        for (var s in m_data.seats){
            if (m_data.seats[s].conn!=null){
                m_data.seats[s].conn.send(JSON.stringify(create_msg(_name)));
            }
        }
    }

    function send_start(){
        var _players = [];
        for (var s in m_data.seats){
            if (m_data.seats[s].userid!=null){
                _players.push({seatno:s,money:m_data.seats[s].money,card:m_data.seats[s].card,fine:m_data.fine});
            }
        }
        for (var s in m_data.seats){
            if (m_data.seats[s].conn!=null){
                var msg = create_msg(GAME_MSG_START);
                msg.players =_players;
                m_data.seats[s].conn.send(JSON.stringify(msg));
            }
        }
    }
    
    function send_full(_conn){
        _conn.send(JSON.stringify({name:GAME_MSG_FULL}));
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
}

export.masque=masque;