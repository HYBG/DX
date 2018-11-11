#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import json
#import MySQLdb
import urllib2
import random
import threading
import Queue
import time
import datetime
from socket import *

BURN_CARD_ATTR_ID = 'ID'
BURN_CARD_ATTR_TYPE = 'TYPE'
BURN_CARD_ATTR_NAME = 'NAME'
BURN_CARD_ATTR_DIV = 'DIVISION'
BURN_CARD_ATTR_DESC='DESC'
BURN_CARD_ATTR_ABILITY='ABILITY'
BURN_CARD_ATTR_SALARY = 'SALARY'
BURN_CARD_ATTR_TARGET = 'TARGET'
BURN_CARD_ATTR_PARA = 'PARA'

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


BURN_GAME_STATUS_READY = 1
BURN_GAME_STATUS_ONGOING = 2
BURN_GAME_STATUS_DONE = 3

class burncard(object):
    def __init__(self,id,typ,name):
        self.BURN_CARD_ATTR_ID = id
        if typ.upper()=='ACTION':
            self.BURN_CARD_ATTR_TYPE = BURN_CARD_TYPE_ACTION
        elif typ.upper()=='PERSON':
            self.BURN_CARD_ATTR_TYPE = BURN_CARD_TYPE_PERSON
        else:
            raise Exception('unknown card type[%s]'%typ)
        self.BURN_CARD_ATTR_NAME = name

class burnmanager(object):
    def __init__(self,version):
        self._version = version
        self._cards = {}
        url = 'http://www.boardgame.org.cn/burn/burn_1_0.csv'
        context = urllib2.urlopen(url).read()
        lines = context.split()
        for line in lines:
            items = line.split(',')
            id = items[0]
            type = items[1]
            div = items[2]
            name = items[3]
            desc = items[4]
            ability = items[5]
            salary = items[6]
            target = items[7]
            para = items[8]
            card = burncard(id,type,name)
            if div!='N/A':
                if div.upper()=='HR':
                    setattr(card,BURN_CARD_ATTR_DIV,BURN_DIV_NAME_HR)
                elif div.upper()=='SALES':
                    setattr(card,BURN_CARD_ATTR_DIV,BURN_DIV_NAME_SALE)
                elif div.upper()=='FIN':
                    setattr(card,BURN_CARD_ATTR_DIV,BURN_DIV_NAME_FINANCE)
                elif div.upper()=='R&D':
                    setattr(card,BURN_CARD_ATTR_DIV,BURN_DIV_NAME_REASEARCH)
                else:
                    raise Exception('unknown division[%s]'%div)
            if desc!='N/A':
                setattr(card,BURN_CARD_ATTR_DESC,desc)
            if ability!='N/A':
                setattr(card,BURN_CARD_ATTR_ABILITY,int(ability))
            if salary!='N/A':
                setattr(card,BURN_CARD_ATTR_SALARY,int(salary))
            if target!='N/A':
                if target.upper()=='SELF':
                    setattr(card,BURN_CARD_ATTR_TARGET,BURN_CARD_TARGET_SELF)
                elif target.upper()=='OTHER':
                    setattr(card,BURN_CARD_ATTR_TARGET,BURN_CARD_TARGET_OTHER)
                else:
                    raise Exception('unknow target[%s]'%target)
            if para!='N/A':
                setattr(card,BURN_CARD_ATTR_PARA,para)
            self._cards[id] = card

    def alldiv(self):
        return (BURN_DIV_HR,BURN_DIV_SALE,BURN_DIV_FINANCE,BURN_DIV_REASEARCH)

    def getversion(self):
        return self._version

    def getcardattr(self,id,name):
        if self._cards.has_key(id) and hasattr(self._cards[id],name):
            return getattr(self._cards[id],name)
        return None

    def getallactions(self):
        ids = []
        for id in self._cards.keys():
            if self._cards[id].type==BURN_CARD_TYPE_ACTION:
                cards.append(id)
        return ids

    def alldivs(self):
        ids ={}
        for id in self._cards.keys():
            if self._cards[id].type==BURN_CARD_TYPE_PERSON:
                if hasattr(self._cards[id],BURN_CARD_ATTR_DIV):
                    all = self.alldiv()
                    for div in all:
                        if ids.has_key(div):
                            ids[div].append(id)
                        else:
                            ids[div] = [id]
        return ids

class burngame(object):
    def __init__(self,ownerid,ownernick,ownerimg,gameid,count,mgr):
        self.ownerid = ownerid
        self.gameid = gameid
        self.count = count
        self.status = BURN_GAME_STATUS_READY
        self.mgr = mgr
        self.activeone = ownerid
        self.drops = []
        self.pile = []
        self.divs = {}
        self.players ={}
        self.players[ownerid] = burnplayer(self.mgr,ownerid,ownernick,ownerimg)
        self.players[ownerid].seatno = 1

    def _shuffle(self,lis):
        pass
    
    def _alldiv(self):
        return (BURN_DIV_HR,BURN_DIV_SALE,BURN_DIV_FINANCE,BURN_DIV_REASEARCH)

    def _deal(self,playerid):
        need = 6-self.players[playerid].inhands()
        if len(self.pile)>=need:
            self.players[playerid].actions = self.players[playerid].actions + self.pile[:need]
        else:
            need = need - len(self.pile)
            self.players[playerid].actions = self.players[playerid].actions + self.pile
            self._shuffle(self.drops)
            self.pile = self.drops
            self.drops = []
            self.players[playerid].actions = self.players[playerid].actions + self.pile[:need]

    def _start(self):
        self.status = BURN_GAME_STATUS_ONGOING
        self.pile = self.mgr.getallactions()
        self._shuffle(self.pile)
        self.divs = self.mgr.alldivs()
        for k in self.divs.keys():
            self._shuffle(self.divs[k])

        names = []
        for p in self.players.keys():
            names.append(p)
        for name in names:
            ri = random.randint(0,len(names)-1)
            sn = self.players[name].seatno
            self.players[name].seatno = self.players[names[ri]].seatno
            self.players[names[ri]].seatno = sn
        for name in names:
            self._deal(name)
            if self.players[name].seatno == 1:
                self.activeone = name

    def playerjoin(self,playerid,playernick,playerimg):
        if self.status != BURN_GAME_STATUS_READY:
            raise Exception('game is already begin or finish')
        self.players[playerid] = burnplayer(self.mgr,playerid,playernick,playerimg)
        self.players[playerid].seatno = len(self.players)
        if len(self.players)==self.count:
            self._start()
            return True
        return False

    def recruit(self,playerid,divid):
        if len(self.divs[divid])>0:
            cardid = self.divs[divid].pop(0)
            self.players[playerid].divs[divid].addemployees(cardid)
            return True
        return False

    def handle_join(self,playerid,playernick,playerimg):
        if self.playerjoin(playerid,playernick,playerimg):
            pcnt = len(self.pile)
            dcnt = len(self.drops)
            dcnts = {}
            alld = self.mgr.alldiv()
            for div in all:
                dcnts[div] = (len(self.divs[div]),self.divs[div][0])
            return (True,pcnt,dcnt,dcnts,self.players)
        else:
            return (False,None,None,None,self.players)


    def handle_setup(self,playerid,did):
        pass

    def handle_play(self,playerid,cid,target=None):
        pass

    def handle_done(self,playerid):
        pass

class burndivision(object):
    def __init__(self,name,mgr):
        self.name = name
        self.mgr = mgr
        self.isvp = False
        self.ability = -1
        self.employees =[]

    def addemployee(self,id):
        self.employees.append(id)
        ab = self.mgr.getcardattr(id,BURN_CARD_ATTR_ABILITY)
        if self.mgr.getcardattr(id,BURN_CARD_ATTR_NAME) == 'VP':
            self.isvp = True
            self.ability = ab
        else:
            if self.mgr.getcardattr(id,BURN_CARD_ATTR_ABILITY) > self.ability and not self.isvp:
                self.ability = ab

    def fire(self,id):
        fid = None
        for i in rnage(len(self.employees)):
            if self.employees[i] == id:
                fid = self.employees.pop(i)
                break
        self.isvp = False
        for e in employees:
            if self.mgr.getcardattr(e,BURN_CARD_ATTR_NAME) == 'VP':
                self.ability = self.mgr.getcardattr(e,BURN_CARD_ATTR_ABILITY)
                self.isvp = True
        if not self.isvp:
            for e in self.employees:
                if self.mgr.getcardattr(e,BURN_CARD_ATTR_ABILITY) > self.ability:
                    self.ability = self.mgr.getcardattr(e,BURN_CARD_ATTR_ABILITY)
        return fid

class burnplayer(object):
    def __init__(self,mgr,id,nick,img):
        self.mgr = mgr
        self.id = id
        self.nick = nick
        self.img = img
        self.seatno = 0
        self.divs = {BURN_DIV_HR:burndivision(BURN_DIV_NAME_HR,mgr),BURN_DIV_SALE:burndivision(BURN_DIV_NAME_SALE,mgr),BURN_DIV_FINANCE:burndivision(BURN_DIV_NAME_FINANCE,mgr),BURN_DIV_REASEARCH:burndivision(BURN_DIV_NAME_REASEARCH,mgr)}
        self.needpay = 0
        self.money = 100
        self.hands = []

    def inhands(self):
        return len(self.hands)

    def vpcnt(self):
        cnt = 0
        for d in self.divs.keys():
            if self.divs[d].isvp:
                cnt = cnt + 1
        return cnt

    def ability(self,divid):
        if self.divs.has_key(divid):
            return self.divs[divid].ability
        return None

class hyserver(object):
    def __init__(self,host,port,connnum=1000,bufsize=4096):
        self._host = host
        self._port = port
        self._connnum = connnum
        self._bufsize = bufsize
        self.queue = Queue.Queue()
    
    def handle_massage(self,client,name,paras):
        pass
    
    def work(self,msg):
        while 1:
            try:
                client,data = self.queue.get()
                data = json.loads(data)
                if data.has_key('name') and data.has_key('paras'):
                    self.handle_massage(client,data['name'],data['paras'])
                else:
                    client.send(json.loads('{"retcode":1001,"errmsg":"invalid"}'))
            except Exception,e:
                pass
    
    def run(self):
        ADDR = (self._host,self._port)
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(30)
        sock.bind(ADDR)
        sock.listen(self._connnum)
        print 'listening port[%d]'%self._port
        worker = threading.Thread(target=self.worker)
        woker.start()
        while True:
            client,addr = sock.accept()
            print("Connection from :",addr)
            while True:
                try:
                    data = client.recv(self._bufsize)
                    self.queue.put((client,data))
                except Exception,e:
                    print 'data exception[%s]'%e
            client.close()
        client.close()

class burn(hyserver):
    def __init__(self,host,port,connnum=1000,bufsize=4096):
        hyserver.__init__(host,port,connnum,bufsize)
        self._connection = None
        self._cursor = None
        self.mgr = burnmanager('1.0')
        self._data = {}

    def handle_massage(self,client,name,paras):
        if name=='create':
            self._handle_create(client,paras)
        else:
            client.send(json.loads('{"retcode":9000,"errmsg":"name invalid"}'))

    def _check_paras(self,paras,names):
        for name in names:
            if not paras.has_key(name):
                return False
        return True
    
    def _create_gameid(self):
        pass

    def _handle_create(self,client,paras):
        if not self._check_paras(paras,['ownerid','ownernick','ownerimg','count']):
            return '{"retcode":1001}'
        gameid = self._create_gameid()
        self._data[gameid] = burngame(paras['ownerid'],paras['ownernick'],paras['ownerimg'],gameid,int(paras['count'],self.mgr))
        '''
        insert game_table
        insert room_table'''
        return '{}'

    def _handle_join(self,client,paras):
        if not self._check_paras(paras,['gameid','playerid','playerbick','playerimg']):
            return '{"retcode":1001}'
        data = self._data[paras['gameid']].handle_join(paras['playerid'],paras['playerbick'],paras['playerimg'])
        if data[0]:
            pass
        else:
            pass

    def _handle_setupteam(self,client,paras):
        if not self._check_paras(paras,['gameid','playerid','divid']):
            pass
    
    def _handle_discard(self,client,paras):
        pass

    def _handle_play(self,client,paras):
        pass

    def _handle_done(self,client,paras):
        pass


class hy(object):
    def __init__(self):
        self.q = Queue.Queue()
    
    def work(self):
        while 1:
            data = self.q.get()
            print 'get data[%s] from queue'%str(data)

    def run(self):
        worker = threading.Thread(target=self.work)
        worker.start()
        while 1:
            now = datetime.datetime.now()
            self.q.put('msg[%s]'%str(now))
            time.sleep(2)


if __name__ == "__main__":
    '''print 'hello world'
    bn = burnmanager('1.0')
    svr = hyserver('',8088)
    #bn = burn('./burn_1_0.csv','1.0')
    svr.run()'''
    pid = os.fork()
    if pid > 0:
        print 'sub pid[%d]'%pid
        pid = os.fork()
        if pid >0:
            pass

#hy().run()
