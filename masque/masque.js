'use strict';

GAME_STATUS_INIT = 0;
GAME_STATUS_ONGOING = 1;
GAME_STATUS_DONE = 2;

GAME_PLAYER_STATUS_WAITING = 1;
GAME_PLAYER_STATUS_INGAME = 2;

GAME_PLAYER_INIT_MONEY = 6;

function masque(_uid,_nick,_img,_pcnt){
    var m_pcount = _pcnt;
    var m_jcount = 0;
    var m_owner = _uid;
    var m_data = init(_uid,_nick,_img);
    var m_gameid = 'GID'+
    var m_gamestatus = GAME_STATUS_INIT;

    this.join = function(_uid,_nick,_img){
        
    }

    function init(_uid,_nick,_img){
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

        var game = new Object;
        game.fine = 0;
        if (m_pcount==4){
            game.T1 = cards[4][1];
            game.T2 = cards[5][1];
        }
        else if (m_pcount==5){
            game.T1 = cards[5][1];
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
                seats[cards[j][1]] = s;
            }
        }
        game.seats = seats;
        var sno = 'S'+Math.ceil(Math.random()*m_pcount);
        game.seats[sno].userid = _uid;
        game.seats[sno].nick = _nick;
        game.seats[sno].img = _img;
        return game;
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
}

export.masque=masque;