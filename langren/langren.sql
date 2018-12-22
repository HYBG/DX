CREATE TABLE `lr_game` (
  `gameid` varchar(18) NOT NULL,
  `seatno` int(1) NOT NULL,
  `roomid` varchar(6) NOT NULL,
  `openid` varchar(32) DEFAULT NULL,
  `nick` varchar(40) DEFAULT NULL,
  `img` varchar(160) DEFAULT NULL,
  `roleid` varchar(5) NOT NULL,
  `status` int(1) NOT NULL DEFAULT '1' COMMENT '1:vacant,2:reserved,3:archived,\nseat0: 10:all seated,100:timeout and no result\n101:lang win,102:man win,103: mingwang win',
  `langtag` int(1) NOT NULL,
  `end` int(1) DEFAULT NULL,
  `createtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`gameid`,`seatno`),
  KEY `open` (`openid`),
  KEY `idle` (`gameid`,`status`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


CREATE TABLE `lr_user` (
  `openid` varchar(32) NOT NULL,
  `nick` varchar(40) DEFAULT NULL,
  `img` varchar(160) DEFAULT NULL,
  `country` varchar(20) DEFAULT NULL,
  `province` varchar(20) DEFAULT NULL,
  `city` varchar(40) DEFAULT NULL,
  `gender` int(1) DEFAULT NULL,
  `lang` varchar(16) DEFAULT NULL,
  `experience` int(1) DEFAULT '0',
  `langrate` double DEFAULT '0',
  `shenrate` double DEFAULT '0',
  `lwinrate` double DEFAULT '0',
  `swinrate` double DEFAULT '0',
  PRIMARY KEY (`openid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `lr_room` (
  `roomid` varchar(6) NOT NULL,
  `gameid` varchar(18) NOT NULL DEFAULT '0',
  `expire` double NOT NULL DEFAULT '0',
  `count` int(1) NOT NULL DEFAULT '0' COMMENT '0:waiting,1:busy',
  PRIMARY KEY (`roomid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


