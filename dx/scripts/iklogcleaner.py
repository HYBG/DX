#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import random
import socket
import commands

if __name__ == "__main__":
    while 1:
        logdir = '/var/data/iknow/log'
        fns = os.listdir(logdir)
        for fn in fns:
            if (re.match('.*\.log\.[2-9]',fn)):
                ffn = os.path.join(logdir,fn)
                commands.getstatusoutput('rm -fr %s'%ffn)
        logname = '/var/data/iknow/log/ib_logfile1'
        if os.path.isfile(logname):
            commands.getstatusoutput('rm -fr %s'%logname)
        time.sleep(10)
        


