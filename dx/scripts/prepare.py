#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

class base:
    def __init__(self):
        self.code = ''
        self.date = ''
        self.fv = ''
        self.stdzdf = 0.0
        self.stdzf = 0.0
        self.stdosrc = 0.0
        self.stdcsrc = 0.0
        self.nhb = 0
        self.nlb = 0
        self.nk = 0
        self.nv1 = 0
        self.nv2 = 0
        self.nhp = 0
        self.nlp = 0
        self.nopenzdf = 0.0
        self.nhighzdf = 0.0
        self.nlowzdf = 0.0
        self.nclosezdf = 0.0


class ikprepare:
    def __init__(self,name):
        self.basedir = '/var/data/iknow/base'
        self.attrdir = '/var/data/iknow/attr'
        self.datedir = '/var/data/iknow/attr_date'
        self.fvdir = '/var/data/iknow/fv'
        self.telldir = '/var/data/iknow/tell'
        g_iu.mkdir(self.datedir)
        g_iu.mkdir(self.fvdir)
        g_iu.mkdir(self.telldir)
        logd = '/var/data/iknow/log'
        self.logger = logging.getLogger('name')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logfile = os.path.join(logd,'%s.log'%name)
        rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(logging.INFO)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self.logger.addHandler(rh)
        self.logger.setLevel(logging.INFO)

    def __del__(self):
        pass

    def attrdate(self):
        files = os.listdir(self.attrdir)
        files.sort()
        for fn in files:
            ffn = os.path.join(self.attrdir,fn.strip())
            print 'attrdate handling file[%s]...'%(ffn)
            mat = g_iu.loadcsv(ffn,{3:type(1.0),4:type(1.0),5:type(1.0),6:type(1.0)})
            for row in mat:
                ofn = os.path.join(self.datedir,'%s.csv'%row[1])
                f = open(ofn,'a')
                f.write('%s,%s,%s,%0.4f,%0.4f,%0.4f,%0.4f\n'%(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
                f.close

    def basrfv(self):
        files = os.listdir(self.basedir)
        files.sort()
        for fn in files:
            ffn = os.path.join(self.basedir,fn.strip())
            print 'basrfv handling file[%s]...'%(ffn)
            mat = g_iu.loadcsv(ffn,{})
            for row in mat:
                ofn = os.path.join(self.fvdir,'%s.csv'%row[2])
                f = open(ofn,'a')
                line = g_iu.linar(row)
                f.write('%s\n'%line)
                f.close
                
    def loadfvfile(self,filename):
        f = open(filename,'r')
        lines = f.readlines()
        f.close()
        blis = []
        try:
            for line in lines:
                items = line.split(',')
                b = base()
                b.code = items[0]
                b.date = items[1]
                b.fv = items[2]
                b.stdzdf = float(items[3])
                b.stdzf = float(items[4])
                b.stdosrc = float(items[5])
                b.stdcsrc = float(items[6])
                b.nhb = int(items[7])
                b.nlb = int(items[8])
                b.nk = int(items[9])
                b.nv1 = int(items[10])
                b.nv2 = int(items[11])
                b.nhp = int(items[12])
                b.nlp = int(items[13])
                b.nopenzdf = float(items[14])
                b.nhighzdf = float(items[15])
                b.nlowzdf = float(items[16])
                b.nclosezdf = float(items[17])
                blis.append(b)
        except Exception,e:
            return None
        return blis
                
    def tell(self,start,end):
        files = os.listdir(self.datedir)
        files.sort(reverse=True)
        mincnt = 21
        rate = 0.001
        for fn in files:
            if fn.strip()[:10]>start:
                continue
            if fn.strip()[:10]<end:
                break
            ffn = os.path.join(self.datedir,fn.strip())
            ofn = os.path.join(self.telldir,'%s'%fn.strip())
            self.logger.info('handling file[%s]....'%ffn)
            fvd = {}
            mat = g_iu.loadcsv(ffn,{3:type(1.0),4:type(1.0),5:type(1.0),6:type(1.0)})
            total = float(len(mat))
            for row in mat:
                if fvd.has_key(row[2]):
                    fvd[row[2]].append(row[:2]+row[3:])
                else:
                    fvd[row[2]] = [row[:2]+row[3:]]
            told =[]
            handled = 1
            for fv in fvd.keys():
                fvfn = os.path.join(self.fvdir,'%s.csv'%fv)
                #fvmat = self.loadfvfile(fvfn)
                fvmat = g_iu.loadcsv(fvfn,{3:type(1.0),4:type(1.0),5:type(1.0),6:type(1.0),7:type(1),8:type(1),9:type(1),10:type(1),11:type(1),12:type(1),13:type(1),14:type(1.0),15:type(1.0),16:type(1.0),17:type(1.0)})
                if not fvmat:
                    continue
                for line in fvd[fv]:
                    code = line[0]
                    date = line[1]
                    ds = []
                    for fvbase in fvmat:
                        if fvbase[1]>=date:
                            continue
                        d = ((line[2]-fvbase[3])**2+(line[3]-fvbase[4])**2+(line[4]-fvbase[5])**2+(line[5]-fvbase[6])**2)**0.5
                        #d = abs(line[2]-fvbase.stdzdf)+abs(line[3]-fvbase.stdzf)+abs(line[4]-fvbase.stdosrc)+abs(line[5]-fvbase.stdcsrc)
                        if d < 0.013:
                            ds.append(fvbase[7:])
                    #ds.sort()
                    #thv = max(int(len(ds)*rate),min(len(ds),mincnt))
                    #ds = ds[:thv]
                    if len(ds)==0:
                        continue
                    perf = [[row[i] for row in ds] for i in range(11)]
                    row = []
                    for p in perf:
                        row.append(float('%0.4f'%(float(sum(p))/float(len(p)))))
                    told.append((code,date)+tuple([len(ds),]+row))
                    self.logger.info('handling progress[%0.2f%%] date[%s] fv[%s] code[%s] count[%d]'%(100*(handled/total),date,fv,code,len(ds)))
                    handled = handled+1
            g_iu.dumpfile(ofn,told)
            
if __name__ == "__main__":

    parser  = OptionParser()
    parser.add_option('-s', '--start', action='store', dest='start',default=None, help='start day')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='end day')
    parser.add_option('-n', '--name', action='store', dest='name',default=None, help='log name')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    #bill.attrdate()
    #bill.basrfv()
    if ops.start and ops.end and ops.name:
        bill = ikprepare(ops.name)
        bill.tell(ops.start,ops.end)
    
    
    
    