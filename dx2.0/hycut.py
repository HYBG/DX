#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import urllib2
import socket
import MySQLdb
import copy
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

class hycut:
    def __init__(self):
        self._codes = []
        self._data = {}
        g_tool.conn('hy')
        self._reload()
        self._logger = g_iu.createlogger('hycut',os.path.join(os.path.join(g_home,'log'),'hycut.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        ld = g_tool.exesqlone('select date from hy.iknow_data order by date desc limit 1',None)
        ld = ld[0]
        data = g_tool.exesqlbatch('select code,open,high,low,close,(close-open)*volh from hy.iknow_data where date=%s order by code',(ld,))
        for row in data:
            self._codes.append(row[0])
            self._data[row[0]] = row[1:]
            
    def dumpfv(self):
        fvs = g_tool.exesqlbatch('select distinct fv from dx.iknow_lib',None)
        odir = os.path.join(g_home,'fvs')
        g_iu.mkdir(odir)
        for fv in fvs:
            fv = fv[0]
            data = g_tool.exesqlbatch('select stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,substring(nfv,5,1),h1 from dx.iknow_lib where fv=%s',(fv,))
            ofn = os.path.join(odir,'%s.csv'%fv)
            g_iu.dumpfile(ofn,data)
            
    def _centralization(self,mat):
        n = float(len(mat))
        cent = [0,0,0,0,0,0,0,0,0,0]
        for row in mat:
            for i in range(len(row)):
                cent[i] = cent[i]+row[i]
        for j in range(len(cent)):
            cent[j] = float(cent[j])/n
        cent.append(int(n))
        return cent
           
    def cut(self,filename):
        mat = g_iu.loadcsv(filename,{0:type(1.0),1:type(1.0),2:type(1.0),3:type(1.0),4:type(1.0),5:type(1.0),6:type(1.0),7:type(1.0),8:type(1.0),9:type(1.0)})
        nwmat = []
        mmat = []
        total = float(len(mat))
        while len(mat)>0:
            rate = 100-100*(len(mat)/total)
            bef = 0
            if rate-bef>0.01:
                self._logger.info('hycut handle progress[%0.2f%%] file[%s]....'%(rate,filename))
                bef = rate
            row = mat.pop()
            mt = [row]
            for i in range(len(mat)):
                d = self._distance(row[:8],mat[i][:8])
                if d < 0.05:
                    mt.append(mat[i])
                else:
                    mmat.append(mat[i])
            nwmat.append(self._centralization(mt))
            mat = mmat
            mmat = []
        return nwmat
            
    def cutfv(self):
        idir = os.path.join(g_home,'fvs')
        files = os.listdir(idir)
        odir = os.path.join(g_home,'fvs_1')
        g_iu.mkdir(odir)
        for fn in files:
            print 'handling file[%s]....'%fn
            ffn = os.path.join(idir,fn.strip())
            ofn = os.path.join(odir,fn.strip())
            mat = self.cut(ffn)
            g_iu.dumpfile(ofn,mat)
        
    def _standardization(self,cur,prev):
        prices = 0.0
        #print 'cur[%s] prev[%s]'%(str(cur),str(prev))
        prices = cur[0]+cur[1]+cur[2]+cur[3]+prev[0]+prev[1]+prev[2]+prev[3]
        pev = prices/8.0
        prices = 0.0
        prices = (cur[0]-pev)**2+(cur[1]-pev)**2+(cur[2]-pev)**2+(cur[3]-pev)**2+(prev[0]-pev)**2+(prev[1]-pev)**2+(prev[2]-pev)**2+(prev[3]-pev)**2
        pstd = prices**0.5
        vector = (self._stdv(cur[0],pev,pstd),self._stdv(cur[1],pev,pstd),self._stdv(cur[2],pev,pstd),self._stdv(cur[3],pev,pstd),self._stdv(prev[0],pev,pstd),self._stdv(prev[1],pev,pstd),self._stdv(prev[2],pev,pstd),self._stdv(prev[3],pev,pstd))
        return vector

    def _stdv(self,val,ev,std):
        stdv = 0.0
        if std!=0:
            stdv = (val-ev)/std
        return float('%0.4f'%stdv)
        
    def rtprice(self,codes):
        codeliststr = ''
        for code in codes:
            market = None
            if code[:2]=='60' or code[0]=='5':
                market = 'sh'
            else:
                market = 'sz'
            codeliststr = codeliststr + '%s%s,'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codeliststr[:-1])
        #print '%s'%url
        lis = []
        data = urllib2.urlopen(url).readlines()
        #print '%s'%data
        #lines = data.strip().split(';')
        i = 0
        lis = []
        #print 'data len[%d] %s'%(len(data),data[-1])
        for line in data:
            #print '%s'%line
            info = line.split('"')[1].split(',')
            now = datetime.datetime.now()
            if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                #print '%s'%info[8]
                code = codes[i]
                yc = float(info[2])
                open = float(info[1])
                high = float(info[4])
                low = float(info[5])
                close = float(info[3])
                v = (close-open)*float(info[8])
                zdf = (close-yc)/yc
                if (close>open) and (zdf < 0.099) and (zdf>0.035):
                    print 'code[%s] yc[%0.4f] open[%0.4f] high[%0.4f] low[%0.4f] close[%0.4f] zdf[%0.4f]'%(code,yc,open,high,low,close,zdf)
                    lis.append((code,open,high,low,close,v))
            i = i+1
        return lis
        
    def filter(self,codes):
        lis = self.rtprice(codes)
        matd = {}
        for row in lis:
            code = row[0]
            high = row[2]
            low = row[3]
            v = row[5]
            yrow = self._data[code]
            if high>yrow[1] and low>yrow[2] and v>yrow[4]:
                matd[code]=(yrow,row[1:])
        return matd

    def collet(self):
        codes1 = self._codes[:850]
        codes2 = self._codes[850:1700]
        codes3 = self._codes[1700:2550]
        codes4 = self._codes[2550:]
        matd = self.filter(codes1)
        matd.update(self.filter(codes2))
        matd.update(self.filter(codes3))
        matd.update(self.filter(codes4))
        return matd

    def _distance(self,v1,v2):
        all = 0.0
        for i in range(len(v1)):
            all = all + (v1[i]-v2[i])**2
        return all**0.5
        
    def _range(self,fv,stdvec,thv,day):
        data = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,h1 from dx.iknow_lib where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s',(day,fv,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv))
        return list(data)

    def _middle(self,lis):
        lis.sort()
        return lis[int(len(lis)/2)]

    def _prob(self,data):
        perf = [[row[i] for row in data] for i in range(2)]
        h1m = self._middle(perf[1])
        return float('%0.4f'%h1m)

    def dl(self):
        codes = self._codes[:850]
        lis = self.rtprice(codes)
        print '%s'%str(lis)
        #g_iu.dumpfile(os.path.join(g_home,'rt.csv'),lis)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-f', '--file', action='store', dest='file',default=None, help='filename')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = hycut()
    if ops.file:
        mat = ik.cut(ops.file)
        basename = os.path.basename(ops.file)
        ofn = os.path.join(os.path.join(g_home,'fvs_1'),basename)
        g_iu.dumpfile(ofn,mat)
    else:
        ik.cutfv()
    
    