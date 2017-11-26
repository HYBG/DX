#!/usr/bin/python

import os
import sys
import urllib2
import logging
import string
import re
import datetime
import time
import random
import socket
import commands
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import smtplib  
from email.mime.text import MIMEText

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('iknow')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iknow.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class ikutil:
    def __init__(self):
        pass
        
    def _typeing(self,val,typ):
        if typ == type(1.0):
            return float(val)
        elif typ == type(1):
            return int(val)
        else:
            return str(val)

    def linar(self,vector):
        line = ''
        for it in vector:
            if type(it) == type(1.0):
                line = line + '%0.4f,'%it
            elif type(it) == type(1):
                line = line + '%d,'%it
            else:
                line = line + '%s,'%str(it)
        return line[:-1]

    def log(self,level,str):
        g_logger.log(level,str)
        
    def home(self):
        return g_home

    def loadcsv(self,filename,typed={},key=-1):
        f = open(filename,'r')
        rows = f.readlines()
        f.close()
        mat = []
        cd = {}
        for r in rows:
            its = r.strip().split(',')
            lis = []
            k = None
            for i in range(len(its)):
                tp = type('')
                if re.match('.*\..*',its[i]):
                    tp = type(1.0)
                if typed.has_key(i):
                    tp = typed[i]
                if key < 0:
                    lis.append(self._typeing(its[i],tp))
                else:
                    if key == i:
                        k = self._typeing(its[i],tp)
                    else:
                        lis.append(self._typeing(its[i],tp))
            if key >= 0:
                if k:
                    if len(lis) == 1:
                        cd[k] = lis[0]
                    else:
                        cd[k] = tuple(lis)
                else:
                    raise Exception('loadcsv file[%s] key[%d] out of range'%(filename,key))
            else:
                if len(lis) == 1:
                    mat.append(lis[0])
                else:
                    mat.append(tuple(lis))
        if key < 0:
            return mat
        else:
            return cd

    def allcodes(self):
        f = open(os.path.join(os.path.join(g_home,'etc'),'astock.lis'),'r')
        rows = f.readlines()
        f.close()
        codes = []
        for line in rows:
            line = line.strip()
            if re.match('60\d{4}', line):
                codes.append(line)
            elif re.match('[0,3]0\d{4}', line):
                codes.append(line)
            elif re.match('1\d{5}', line):
                codes.append(line)
            elif re.match('5\d{5}', line):
                codes.append(line)
        return codes

    def dumpfile(self,filename,mat):
        f = open(filename,'w')
        for r in mat:
            if type(r) == type([]) or type(r) == type(()):
                f.write(u'%s\n'%self.linar(r))
            else:
                f.write(u'%s\n'%str(r))
        f.close()

    def appendmat(self,filename,mat):
        f = open(filename,'a')
        for r in mat:
            line = ''
            for it in r:
                if type(it) == type(1.0):
                    line = line + '%0.4f,'%it
                else:
                    line = line + '%s,'%str(it)
            line = line[:-1]
            f.write('%s\n'%line)
        f.close()

    def link(self,dir,link,target):
        cwd = os.getcwd()
        os.chdir(dir)
        cmd = 'ln -snf %s %s'%(target,link)
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute cmd[%s] status[%d] output[%s]'%(cmd,status,output))
        os.chdir(cwd)

    def mkdir(self,dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def execmd(self,cmd):
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute command[%s],status[%d],output[%s]'%(cmd,status,output.strip()))
        return status

    def isopen(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=11,minute=30,second=0)
        o2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=0,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2 or (now>c1 and now < o2):
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[-3] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            g_logger.warning('get current url[%s] exception[%s]'%(url,e))
            return None

    def rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = (info[-3],float(info[1]),float(info[4]),float(info[5]),float(info[3]),int(info[8]),float(info[2]))
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def handlefiles(self,dir,fre,handle,input,output):
        files = os.listdir(dir)
        files.sort()
        for sfn in files:
            fn = os.path.join(dir,sfn)
            if fre:
                if re.match(fre,sfn):
                    handle(fn,input,output)
            else:
                handle(fn,input,output)
            
    def importdata(self,csvfn,tabname):
        sfn = os.path.join(os.path.join(g_home,'tmp'),'%s.sql'%tabname)
        sql = "load data infile '%s' into table %s fields terminated by ',' optionally enclosed by \'\"\' escaped by \'\"\'  lines terminated by '\\n';"%(csvfn,tabname)
        f = open(sfn,'w')
        f.write('%s'%sql)
        f.close()
        cmd = 'mysql -u root -p123456 hy < %s'%sfn
        self.execmd(cmd)

    def sendmail(self,tolist,cclist,bcclist,subject,content):
        mail_host='smtp.ym.163.com'
        mail_user='alex@dongxia365.com'
        mail_pass='1982Liu0904'
        '''mail_host='smtp.163.com'
        mail_user='dongxia365'
        mail_pass='China1234'
        mail_postfix = '163.com'''
        me='dx tech'+'<'+mail_user+'>'
        msg = MIMEText(content,_subtype='plain',_charset='utf-8')
        msg['Subject'] = subject
        msg['From'] = me
        if tolist:
            msg['To'] = ';'.join(tolist)
        if cclist:
            msg['Cc'] = ';'.join(cclist)
        if bcclist:
            msg['Bcc'] = ';'.join(bcclist)
        try:
            server = smtplib.SMTP()
            server.connect(mail_host)
            server.login(mail_user,mail_pass)
            if tolist:
                server.sendmail(me, tolist, msg.as_string())
            if cclist:
                server.sendmail(me, cclist, msg.as_string())
            if bcclist:
                server.sendmail(me, bcclist, msg.as_string())
            server.close()
        except Exception,e:
            g_logger.info('scan send email exception[%s]'%e) 
