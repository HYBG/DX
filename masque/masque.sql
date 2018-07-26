CREATE TABLE `masque`.`lr_roles` (
  `roleid` int(2) NOT NULL,
  `rolename` varchar(12) NOT NULL,
  `langmark` int(2) NOT NULL,
  `desp` varchar(1024) NOT NULL,
  PRIMARY KEY (`roleid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;