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

class ikutil:
    def __init__(self):
        self._logger = logging.getLogger('ikutil')
        self._loglevel = logging.INFO
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logd = os.path.join(g_home,'log')
        logfile = os.path.join(logd,'ikutil.log')
        rh = RotatingFileHandler(logfile, maxBytes=50*1024*1024,backupCount=10)
        rh.setLevel(self._loglevel)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)
        
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

    def createlogger(self,logname,filename,level):
        logger = logging.getLogger(logname)
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        rh = RotatingFileHandler(filename, maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(level)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        logger.addHandler(rh)
        logger.setLevel(level)
        return logger

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
        self._logger.info('execute cmd[%s] status[%d] output[%s]'%(cmd,status,output))
        os.chdir(cwd)

    def mkdir(self,dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def execmd(self,cmd):
        status,output = commands.getstatusoutput(cmd)
        self._logger.info('execute command[%s],status[%d],output[%s]'%(cmd,status,output.strip()))
        return status
            
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
            
    def importdata(self,csvfn,tabname,db='hy'):
        sfn = os.path.join(os.path.join(g_home,'tmp'),'%s.sql'%tabname)
        sql = "load data infile '%s' into table %s fields terminated by ',' optionally enclosed by \'\"\' escaped by \'\"\'  lines terminated by '\\n';"%(csvfn,tabname)
        f = open(sfn,'w')
        f.write('%s'%sql)
        f.close()
        cmd = 'mysql -u root -p123456 %s < %s'%(db,sfn)
        return self.execmd(cmd)

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
            self._logger.info('scan send email exception[%s]'%e) 
