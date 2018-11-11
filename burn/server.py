#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import json
import MySQLdb
import urllib2
import random
import threading
import Queue
import time
import datetime
import xml.etree.ElementTree as ET
from socket import *


BURN_DIV_HR = 0
BURN_DIV_SALE = 1
BURN_DIV_FINANCE = 2
BURN_DIV_REASEARCH = 3

BURN_DIV_NAME_HR = 'HR'
BURN_DIV_NAME_SALE = 'SALES'
BURN_DIV_NAME_FINANCE = 'FINANCE'
BURN_DIV_NAME_REASEARCH = 'R&D'

BURN_CARD_TYPE_ACTION = 0
BURN_CARD_TYPE_PERSON = 1

BURN_CARD_TARGET_SELF = 0
BURN_CARD_TARGET_OTHER = 1

BURN_MSG_RET_CODE_SUCC = 10000
BURN_MSG_RET_CODE_SYS_ERR = 10001
BURN_MSG_RET_CODE_GAME_ONGOING = 11000

BURN_MSG_LOGON = '1000'
BURN_MSG_LOGON_ACK = '1001'
BURN_MSG_CREATE_GAME = '1010'
BURN_MSG_CREATE_GAME_ACK = '1011'
BURN_MSG_JOIN_GAME = '1020'
BURN_MSG_JOIN_GAME_ACK = '1021'
BURN_MSG_BUILD_TEAM = '1030'
BURN_MSG_BUILD_TEAM_ACK = '1031'
BURN_MSG_PLAY_CARD_START = '1032'
BURN_MSG_PLAY_CARD = '1040'
BURN_MSG_PLAY_CARD_ACK = '1041'
BURN_MSG_END_TURN = '1050'
BURN_MSG_END_TURN_ACK = '1051'

BURN_GAME_READY_OPEN = 1
BURN_GAME_ONGOING = 2
BURN_GAME_WAITING = 3
BURN_GAME_DONE = 4

BURN_PLAYER_STATUS_ONLINE = 0
BURN_PLAYER_STATUS_READY = 1
BURN_PLAYER_STATUS_IN_GAME_ACTIVE = 2
BURN_PLAYER_STATUS_IN_GAME_ALIVE = 3
BURN_PLAYER_STATUS_IN_GAME_OVER = 4
BURN_PLAYER_STATUS_OFFLINE = 5


class burncard(object):
    def __init__(self,id,type):
        self.id = id
        self.type = type

class burndivision(object):
    def __init__(self,name):
        self.name = name
        self.men = []
        self.ishead = False
        self.ability = -1

    def count(self):
        return len(self.men)

    def add(self,cardid):
        self.men.append(cardid)
        mgr = burnmanager()
        self.ishead = mgr.isvp(cardid)
        ab = -1
        for cid in self.men:
            cab = mgr.ability(cid)
            if mgr.isvp(cid):
                self.ishead = True
                self.ability = cab
                break
            if cab > ab:
                ab = cab
        if not self.ishead:
            self.ability = ab

class burnmanager(object):
    _instance_lock = threading.Lock()

    def __init__(self):
        url = 'http://www.boardgame.org.cn/burn/burn.xml'
        root = ET.fromstring(urllib2.urlopen(url).read())
        self.version = root.attrib['version']
        self.cards = {}
        self.market = {}
        self.actions = []
        emcards = root.findall('Card')
        for c in emcards:
            id = c.attrib['id']
            type = c.attrib['type']
            card = burncard(id,type)
            cardattrs = c.getchildren()
            for attr in cardattrs:
                attrtype = 'string'
                if attr.attrib.has_key('type'):
                    attrtype = attr.attrib['type']
                val = self._conv(attrtype,attr.text)
                setattr(card,attr.tag,val)
            self.cards[id] = card
            if card.type=='person':
                if not self.market.has_key(card.division):
                    self.market[card.division] = [card.id]
                else:
                    self.market[card.division].append(card.id)
            elif card.type=='action':
                self.actions.append(card.id)

    def __new__(cls, *args, **kwargs):
        if not hasattr(burnmanager, "_instance"):
            with burnmanager._instance_lock:
                if not hasattr(burnmanager, "_instance"):
                    burnmanager._instance = object.__new__(cls)  
        return burnmanager._instance

    def _conv(self,attrtype,attrtext):
        val = attrtext
        if attrtype='int':
            val = int(attrtext)
        elif attrtype='float':
            val = float(attrtext)
        elif attrtype='boolean':
            val = bool(attrtext)
        return val

    def new_game(self):
        actions = []
        market = {}
        for id in self.cards.keys():
            if self.cards[id].type=='person':
                if not market.has_key(self.cards[id].division):
                    market[self.cards[id].division] = [id]
                else:
                    market[self.cards[id].division].append(id)
            elif self.cards[id].type=='action':
                actions.append(id)
        return (actions,market)

    def isvp(self,cardid):
        if self.cards.has_key(cardid) and hasattr(self.cards[cardid],'isvp'):
            return self.cards[cardid].isvp
        return None

    def ability(self,cardid):
        if self.cards.has_key(cardid) and hasattr(self.cards[cardid],'ability'):
            return self.cards[cardid].ability
        return None

    def salary(self,cardid):
        if self.cards.has_key(cardid) and hasattr(self.cards[cardid],'salary'):
            return self.cards[cardid].salary
        return None

    def division_names(self):
        divs = []
        for d in self.market.keys():
            divs.append(d)
        return divs

class burnplayer(object):
    def __init__(self,userid,nick,img,sock,addr):
        self.userid = userid
        self.nick = nick
        self.img = img
        self.socket = sock
        self.addr = addr
        self.seatno = 0
        self.status = BURN_PLAYER_STATUS_ONLINE
        divs = burnmanager().division_names()
        self.divisions = {}
        for d in divs:
            self.divisions[d] = burndivision(d)

    def hire(self,divisionname,cardid):
        self.divisions[divisionname].add(cardid)

    def staff_count(self):
        cnt = 0
        for d in self.divisions.keys():
            cnt = cnt + self.divisions[d].count()
        return cnt

    def vpcnt(self):
        cnt = 0
        for d in self.divisions.keys():
            if self.divisions[d].ishead:
                cnt = cnt + 1
        return cnt

class burnmessage(object):
    def __init__(self,code,msg):
        self.code = code
        self.msg = msg
        self.players = []
        self.market = {}
        self.pile = 0
        self.drop = 0

    def addplayer(self,item):
        self.players.append(item)

    def json(self):
        dic = {}
        dic['name'] = self.name
        dic['players'] = self.players
        dic['market'] = self.market
        dic['pile'] = self.pile
        dic['drop'] = self.drop
        return josn.dumps(dic)

class burngame(object):
    def __init__(self,gameid,owner,count):
        self.gameid = gameid
        self.owner = owner.userid
        self.count = count
        self.players = []
        owner.seatno = 1
        owner.status = BURN_PLAYER_STATUS_READY
        self.players.append(owner)
        self.market = {}
        self.pile = []
        self.drop = []

    def _shuffle(self,lis):
        for i in range(len(lis)):
            s = random.randint(0,len(lis)-1)
            t = lis[s]
            lis[s] = lis[i]
            lis[i] = t

    def _player(self,no):
        for p in self.players:
            if p.seatno == no:
                return p
        return None

    def init_cards(self):
        mgr = burnmanager()
        self.drop,self.market = mgr.new_game()
        self._shuffle(self.drop)
        self.pile = self.drop
        self.drop = []
        for d in self.market.keys():
            self._shuffle(self.market[d])

    def join(self,player):
        if len(self.players)<self.count:
            player.status = BURN_PLAYER_STATUS_READY
            player.seatno = len(self.players)+1
            self.players.append(player)
            if len(self.players)==self.count:
                return BURN_GAME_READY_OPEN
            else:
                return BURN_GAME_WAITING
        else:
            return BURN_GAME_ONGOING

    def begin(self):
        for i in range(len(self.players)):
            self.players[i].status = BURN_PLAYER_STATUS_IN_GAME_ALIVE
            t = random.randint(0,len(self.players)-1)
            s = self.players[t].seatno
            self.players[t].seatno = self.players[i].seatno
            self.players[i].seatno = s
        first = self._player(1)
        first.status = BURN_PLAYER_STATUS_IN_GAME_ACTIVE
        msg = burnmessage(BURN_MSG_RET_CODE_SUCC,BURN_MSG_JOIN_GAME_ACK)
        for p in self.players:
            msg.addplayer({'userid':p.userid,'nick':p.nick,'img':p.img,'seatno':p.seatno,'status':p.status})
        self.init_cards()
        for d in self.market.keys():
            msg.market[d] = self.market[d][0]
        for p in self.players:
            p.socket.send(msg.json())

    def build_team(self,player,divisionname):
        if player.status == BURN_PLAYER_STATUS_IN_GAME_ACTIVE:
            cardid = self.market[divisionname].pop(0)
            player.hire(divisionname,cardid)
            player.status = BURN_PLAYER_STATUS_IN_GAME_ALIVE
            nextactive = (player.seatno+self.count+1)%(self.count+1)
            playcard = False
            for p in self.players:
                if p.seatno==nextactive:
                    p.status = BURN_PLAYER_STATUS_IN_GAME_ACTIVE
                    if p.staff_count()==4:
                        playcard = True
            if playcard:
                msg = burnmessage(BURN_MSG_RET_CODE_SUCC,BURN_MSG_PLAY_CARD_START)
            else:
                msg = burnmessage(BURN_MSG_RET_CODE_SUCC,BURN_MSG_BUILD_TEAM_ACK)
            for d in self.market.keys():
                msg.market[d] = self.market[d][0]
            for p in self.players:
                msg.addplayer({'seatno':p.seatno,'status':p.status})
            for p in self.players:
                p.socket.send(msg.json())
        else:
            logger = logging.getLogger('BURN')
            logger.info('player[%s] status[%d] is inactive'%(player.userid,player.status))

class burnmsg(object):
    def __init__(self,sock,addr):
        self.socket = sock
        self.addr = addr

class burnhand(object):
    def __init__(self,sock,svr,addr):
        self.sock = sock
        self.svr = svr
        self.addr = addr
        self._flag = True
        self._logger = logging.getLogger('BURN')

    def _parse(self,data):
        msg = json.loads(data)
        m = burnmsg(self.sock,self.addr)
        try:
            for k in msg.keys():
                setattr(m,k,msg[k])
        except Exception,e:
            self._logger.info('burnhand parse message exception[%s]'%e)
        return m

    def _run(self):
        self._flag = True
        while self._flag:
            m = self._parse(self.sock.recv(self.svr.getbufsize()))
            self.svr.putq(m)

    def stop(self):
        self._flag = False

    def start(self):
        th = threading.Thread(target=self._run)
        th.start()
        self._logger.info('burnhand start....')

class burnserver(object):
    def __init__(self,conf):
        config = ConfigParser.ConfigParser()
        config.read(conf)
        self._logfile = config.get('burnserver','log_file')
        self._dbname = config.get('burnserver','datebase','burn')
        self._dbhost = config.get('burnserver','dbhost','localhost')
        self._dbuser = config.get('burnserver','username','root')
        self._dbpasswd = config.get('burnserver','password','123456')
        self._sqllogon = config.getboolean('burnserver','sql_log_on')
        self._sleepinterval = config.getint('burnserver','sleep_interval')
        self._host = config.get('burnserver','host','0.0.0.0')
        self._port = config.getint('burnserver','port')
        self._connnum = config.getint('burnserver','connnum')
        self._bufsize = config.getint('burnserver','buffer')
        self._loglevel = self._getloglevel(config.get('burnserver','loglevel','info'))
        self._logger = logging.getLogger('BURN')
        formatstr = '%(asctime)s - %(process)d - %(thread)d - %(module)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s'
        fmter = logging.Formatter(formatstr)
        rh = RotatingFileHandler(self._logfile, maxBytes=100*1024*1024,backupCount=50)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)
        self._queue = Queue.Queue()
        self.reconn()
        self._sockgame = {}
        self._games = {}
        self._users = {}
        self._idseed = 0

    def _getloglevel(self,val):
        lev = logging.INFO
        if val.lower()=='debug':
            lev = logging.DEBUG
        elif val.lower()=='info':
            lev = logging.INFO
        elif val.lower()=='error':
            lev = logging.ERROR
        return lev

    def _create_game_id(self):
        now = datetime.datetime.now()
        id = '%04d%02d%02d%02d%02d%02d%06d%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second,now.microsecond,self._idseed)
        self._idseed = (self._idseed+1+100)%100
        return id

    def reconn(self):
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
            self._connection = MySQLdb.connect(host=self._dbhost,user=self._dbuser,passwd=self._dbpasswd,db=self._dbname,charset='utf8')
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('reconn connect db[%s] error[%s]'%(self._dbname,e))
        return False

    def exesqlquery(self,sql,param,log=False):
        n = 0
        if log:
            self._logger.info('exesqlquery prepare to query sql[%s],para[%s]'%(sql,str(param)))
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        mat = []
        while n>0:
            ret = self._cursor.fetchone()
            if len(ret)==1:
                mat.append(ret[0])
            elif len(ret)>1:
                mat.append(list(ret))
            n = n-1
        if log:
            self._logger.info('exesqlquery query results[%d]'%(len(mat)))
        return mat

    def task(self,sqls,log=False):
        show = self._sqllogon
        if log:
            show = log
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if show:
                    self._logger.info('task execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('task execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def setloglevel(self,level):
        self._logger.setLevel(level)

    def getbufsize(self):
        return self._bufsize

    def putq(self,obj):
        self._queue.put(obj)

    def getq(self):
        return self._queue.get()

    def _handle_message(self,msg):
        try:
            if msg.name == BURN_MSG_LOGON:
                self._handle_logon(msg)
            elif msg.name == BURN_MSG_CREATE_GAME:
                self._handle_create_game(msg)
            elif msg.name == BURN_MSG_JOIN_GAME:
                self._handle_join_game(msg)
            elif msg.name == BURN_MSG_BUILD_TEAM:
                self._handle_build_team(msg)
            elif msg.name == BURN_MSG_PLAY_CARD:
                self._handle_play_card(msg)
            elif msg.name == BURN_MSG_END_TURN:
                self._handle_end_turn(msg)
            else:
                self._handle_default(msg)
        except Exception,e:
            self._logger.error('_handle_message[%d] exeption[%s]'%(msg.name,e))

    def _handle_default(self,msg):
        self._logger.error('_handle_default unknown msg name[%d]'%msg.name)
        msg.socket.send(json.dumps({'retcode':BURN_MSG_RET_CODE_SUCC,'retmsg':''}))

    def _handle_logon(self,msg):
        userid = msg.userid
        nick = msg.nick
        img = msg.img
        sock = msg.socket
        addr = msg.addr
        self._users[userid] = burnplayer(userid,nick,img,sock,addr)
        msg.socket.send({'retcode':BURN_MSG_RET_CODE_SUCC,'retmsg':''})

    def _handle_create_game(self,msg):
        try:
            gameid = self._create_game_id()
            player = self._users[msg.userid]
            self._games[gameid] = burngame(gameid,player,msg.count)
            msg.socket.send({'retcode':BURN_MSG_RET_CODE_SUCC,'retmsg':''})
        except Exception,e:
            self._logger.error('_handle_create_game exception[%s]'%e)

    def _handle_join_game(self,msg):
        try:
            game = self._games[msg.gameid]
            player = self._users[msg.userid]
            if player.status==BURN_PLAYER_STATUS_ONLINE:
                status = game.join(player)
                if status == BURN_GAME_WAITING:
                    msg.socket.send({'retcode':BURN_MSG_RET_CODE_SUCC,'retmsg':''})
                elif status == BURN_GAME_READY_OPEN:
                    game.begin()
                else:
                    msg.socket.send({'retcode':BURN_MSG_RET_CODE_GAME_ONGOING,'retmsg':''})
            else:
                msg.socket.send({'retcode':10000,'retmsg':''})
        except Exception,e:
            self._logger.error('_handle_join_game exception[%s]'%e)

    def _handle_build_team(self,msg):
        try:
            player = self._users[msg.userid]
            game = self._games[msg.gameid]
            game.build_team(player,msg.division)
        except Exception,e:
            self._logger.error('_handle_build_team exception[%s]'%e)

    def _handle_play_card(self,msg):
        userid = mgs.userid
        gameid = msg.gameid
        cardid = msg.cardid
        

    def _handle_end_turn(self,msg):
        id = msg.userid

    def worker(self):
        self.info('thread start....')
        self.reconn()
        while 1:
            msg = self.getq()
            self._logger.info('worker get task[%s]'%(msg.name))
            begin = datetime.datetime.now()
            self._handle_message(msg)
            during = datetime.datetime.now()-begin
            self._logger.info('worker did task[%s] with seconds[%d]'%(msg.name,during.seconds))
        self._logger.info('worker thread end....')

    def run(self):
        sock = socket(AF_INET,SOCK_STREAM)
        sock.bind((self._host,self._port))
        sock.listen(self._connnum)
        self._logger.info('listening port[%s:%d]'%(self._host,self._port))
        worker = threading.Thread(target=self.worker)
        worker.start()
        while 1:
            client,addr = sock.accept()
            self._logger.debug("connection from peer[%s]"%(addr))
            hand = burnhand(client,self,addr)
            hand.start()



