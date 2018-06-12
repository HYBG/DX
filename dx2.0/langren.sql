CREATE TABLE `langren`.`lr_roles` (
  `roleid` int(2) NOT NULL,
  `rolename` varchar(12) NOT NULL,
  `langmark` int(2) NOT NULL,
  `desp` varchar(1024) NOT NULL,
  PRIMARY KEY (`roleid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `langren`.`lr_room` (
  `roomid` varchar(32) NOT NULL,
  `gameid` varchar(24) NOT NULL,
  `created` int(8) NOT NULL,
  PRIMARY KEY (`roomid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `langren`.`lr_seats` (
  `gameid` varchar(24) NOT NULL COMMENT 'game id',
  `seatno` int(2) NOT NULL COMMENT 'seat no',
  `role` varchar(16) NOT NULL COMMENT 'role',
  `openid` varchar(32) COMMENT 'openid',
  `nickname` varchar(32) COMMENT 'player nick',
  `avatarurl` varchar(1024) COMMENT 'img url',
  `status` int(2) NOT NULL DEFAULT '1' COMMENT 'seat status,1:open,2:take,3:frezee',
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`gameid`,`seatno`),
  KEY `loc` (`gameid`,`status`),
  KEY `player` (`openid`)
)ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;

