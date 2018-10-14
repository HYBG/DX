#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import Queue
import MySQLdb
import urllib2
import threading
import Queue
import json
import multiprocessing
import ConfigParser
from socket import *
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
from ikbase import ikbase
from ikbase import ikmessage
from ikbase import ikset
from ikbase import ikobj



class iknet(ikbase):
    def __init__(self,conf):
        ikbase.__init__(self,conf)
        self._tasklist = []
        self._rts = []
        config = ConfigParser.ConfigParser()
        config.read(conf)
        self._host = config.get('iknet','host','0.0.0.0')
        self._port = config.getint('iknet','port')
        self._connnum = config.getint('iknet','connect_number')
        self._bufsize = config.getint('iknet','buffer_size')
        self._sock = None

    def rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        codestr = '%s%s'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codestr)
        try:
            line = urllib2.urlopen(url).readline()
            try:
                info = line.split('"')[1].split(',')
                now = datetime.datetime.now()
                if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                    hq = ikobj()
                    setattr(hq,'code',codes[i])
                    setattr(hq,'open',float(info[1]))
                    setattr(hq,'high',float(info[4]))
                    setattr(hq,'low',float(info[5]))
                    setattr(hq,'close',float(info[3]))
                    setattr(hq,'lastclose',float(info[2]))
                    setattr(hq,'volwy',float(info[9])/10000.0)
                    setattr(hq,'volh',float(info[8])/100)
                    setattr(hq,'date',info[30])
                    setattr(hq,'time',info[31])
                    return hq
            except Exception, e:
                self.error('pid[%d] iknet get current price codes[%s] exception[%s]'%(os.getpid(),codes[i],e))
            return None
        except Exception, e:
            self.error('pid[%d] iknet get current price codes[%d] url[%s] exception[%s]'%(os.getpid(),len(codes),url,e))
            return None

    def _handle_watch_rt(self,paras):
        watchrt = self.exesqlquery('select code,name,industry,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fvcnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8 from ik_rt where watch=1',None)
        resp = {"retcode":1000,"retdata":watchrt}
        return resp

    def _handle_code_rt(self,paras):
        code=paras['code']
        data = self.exesqlquery('select code,name,industry,high8,low8,laststd,s4,s9,s29,s59,fv3 from ik_rt where code=%s',(code,))
        attrs = self.loadone(code,hlc[0][0],{'ik_attr':['k','d','emaf','emas','diff','dea','macd','vol5'],'ik_deri':['kfv','bfv','mfv']})
        resp = {"retcode":1010,"errmsg":"no data"}
        if attrs and data:
            obj = ikobj()
            setattr(obj,'code',data[0])
            setattr(obj,'name',data[1])
            setattr(obj,'industry',data[2])
            setattr(obj,'high8',data[3])
            setattr(obj,'low8',data[4])
            setattr(obj,'laststd',data[5])
            setattr(obj,'s4',data[6])
            setattr(obj,'s9',data[7])
            setattr(obj,'s29',data[8])
            setattr(obj,'s59',data[9])
            setattr(obj,'fv3',data[10])
            setattr(obj,'kfv',attrs.kfv)
            setattr(obj,'bfv',attrs.bfv)
            setattr(obj,'mfv',attrs.mfv)
            setattr(obj,'lastk',attrs.k)
            setattr(obj,'lastd',attrs.d)
            setattr(obj,'lasthigh',hlc[0][1])
            setattr(obj,'lastlow',hlc[0][2])
            setattr(obj,'emaf',attrs.emaf)
            setattr(obj,'emas',attrs.emas)
            setattr(obj,'diff',attrs.diff)
            setattr(obj,'dea',attrs.dea)
            setattr(obj,'lastmacd',attrs.macd)
            setattr(obj,'vol5',attrs.vol5)
            cls = []
            for it in hlc:
                cls.append(it[3])
            setattr(obj,'closes',cls)
            hq = self.rtprice(code)
            date = hq.date
            time = hq.time
            zdf = round(100*((hq.close-hq.lastclose)/hq.lastclose),2)
            csrc = 50.0
            if hq.high!=hq.low:
                csrc = round(100*((hq.close-hq.low)/(hq.high-hq.low)),2)
            volwy = hq.volwy
            ymd = hq.date.split('-')
            hms = hq.time.split(':')
            hqtime = datetime.datetime(int(ymd[0]),int(ymd[1]),int(ymd[2]),int(hms[0]),int(hms[1]),int(hms[2]))
            delta = hqtime-datetime.datetime(hqtime.year,hqtime.month,hqtime.day,9,30,0)
            if hqtime>datetime.datetime(hqtime.year,hqtime.month,hqtime.day,11,30,59):
                delta = hqtime-datetime.datetime(hqtime.year,hqtime.month,hqtime.day,13,0,0)+datetime.timedelta(seconds=7200)
            vr = round(hq.volwy/((obj.vol5/5.0)*(float(delta.seconds)/float(14400))),2)
            close = hq.close
            ma5 = round((close+obj.s4)/5.0,2)
            ma10 = round((close+obj.s9)/10.0,2)
            ma20 = round((close+sum(obj.closes))/20.0,2)
            ma30 = round((close+obj.s29)/30.0,2)
            ma60 = round((close+obj.s59)/60.0,2)
            all = 0.0
            for c in obj.closes:
                all = all + (c-ma20)**2
            all = all + (hq.close-ma20)**2
            std = round(all**0.5,2)
            hb = 0
            if hq.high>obj.lasthigh:
                hb = 1
                hbc = hbc + 1
            lb = 0
            if hq.low<obj.lastlow:
                lb = 1
                lbc = lbc + 1
            scsrc = scsrc + csrc
            kline = 0
            if hq.close>hq.open:
                kline = 1
            fv = self._fv(hb,lb,kline)
            fv4 = '%s%d'%(obj.fv3,fv)
            high = obj.high8
            if hq.high>high:
                high = hq.high
            low = obj.low8
            if hq.low<low:
                low = hq.low
            k = 50.0
            d = 50.0
            lastk = obj.lastk
            lastd = obj.lastd
            if high != low:
                rsv = 100*((hq.close-low)/(high-low))
                k = (2.0*lastk+rsv)/3.0
                d = (2.0*lastd+k)/3.0
            kfv = self._kfv(k,d,lastk)
            kfv2 = '%d%d'%(obj.kfv,kfv)
            bfv = self._bfv(hq.close,ma20,std,obj.laststd)
            bfv2 = '%d%d'%(obj.bfv,bfv)
            macdparan1 = 12
            macdparan2 = 26
            macdparan3 = 9
            emaf = 2*hq.close/(macdparan1+1)+(macdparan1-1)*obj.emaf/(macdparan1+1)
            emas = 2*hq.close/(macdparan2+1)+(macdparan2-1)*obj.emas/(macdparan2+1)
            diff = round(emaf-emas,4)
            dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*obj.dea/(macdparan3+1),4)
            macd = round(2*(diff-dea),4)
            mfv = self._macdv(macd,obj.lastmacd)
            mfv2 = '%d%d'%(obj.mfv,mfv)
            hr = round((hq.high-hq.lastclose)/hq.lastclose,4)
            lr = round((hq.low-hq.lastclose)/hq.lastclose,4)
            fvp = self.prob('fv4',fv4,hr,lr,vr)
            resp = {"retcode":1000,"retdata":[code,date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fvp[0]]+list(fvp[1])}
        return resp

    def handle_message(self,msg):
        sock = msg.name
        addr = msg.type
        data = json.loads(msg.data)
        name = data['name']
        if name == HY_NET_WATCH_RT:
            resp = self._handle_watch_rt(data['paras'])
        elif name == HY_NET_CODE_RT:
            resp = self._handle_code_rt(data['paras'])
        else:
            resp = {"retcode":1001,"errmsg":"invalid"}
        sock.send(json.dumps(resp))
        self.info('iknet pid[%d] send resp[%s] to addr[%s]'%(os.getpid(),str(resp),addr))
        sock.close()

    def beforerun(self):
        ADDR = (self._host,self._port)
        self._sock = socket(AF_INET,SOCK_STREAM)
        self._sock.bind(ADDR)
        self._sock.listen(self._connnum)
        self.info('pid[%d] iknet listening port[%s:%d]'%(os.getpid(),self._host,self._port))

    def main(self):
        client,addr = self._sock.accept()
        self.info('iknet pid[%d] connected from addr[%s]'%(os.getpid(),addr))
        data = client.recv(self._bufsize)
        self.info('iknet pid[%d] recv data[%s] from addr[%s]'%(os.getpid(),data,addr))
        self.putq(ikmessage(client,addr,data,False,None))

if __name__ == "__main__":
    ik = iknet('iknow.conf')
    ik.run()
