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
import urllib2
import commands

reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == "__main__":
    ofn = '/var/data/iknow/tmp/room.csv'
    f = open(ofn,'w')
    for i in range(1000,10000):
        line = '%d,0,0\n'%i
        f.write('%s'%line)
    f.close()
    