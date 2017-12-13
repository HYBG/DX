CREATE TABLE `bg`.`bg_global` (
  `name` varchar(20) NOT NULL,
  `value` varchar(40) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_user` (
  `extid` VARCHAR(40) NOT NULL,
  `nickname` VARCHAR(40),
  `roomid` VARCHAR(4) COMMENT "房间id",
  `seatid` INT(2) COMMENT "座位号",
  `role` VARCHAR(10) COMMENT "角色",
  `voteid` VARCHAR(20) COMMENT "投票id",
  `status` INT(2) NOT NULL DEFAULT '0' COMMENT "0:未设置昵称,1:闲置中,2:",
  `expire` DOUBLE NOT NULL DEFAULT '0',
  PRIMARY KEY (`extid`),
  INDEX `st` (`status` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_room` (
  `roomid` VARCHAR(4),
  `status` INT(1) NOT NULL DEFAULT '0' COMMENT "0:idle,1:ready,2:using",
  `expire` DOUBLE NOT NULL DEFAULT '0' COMMENT "0:永不过期,在idle状态下,没有过期概念,ready和using状态下过期时间值是绝对秒数",
  PRIMARY KEY (`roomid`),
  INDEX `st` (`roomid`,`status`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_game` (
  `roomid` VARCHAR(4) NOT NULL,
  `seatid` INT(2) NOT NULL,
  `role` VARCHAR(10) NOT NULL,
  `player` VARCHAR(40) NOT NULL,
  `status` INT(1) NOT NULL DEFAULT '0' COMMENT "0:未占用,1:占用,2:冻结,3:置换(3,4为盗贼存在采用)", 
  PRIMARY KEY (`roomid`,`seatid`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_vote` (
  `voteid` VARCHAR(20) NOT NULL,
  `seatid` INT(2) NOT NULL,
  `vote` INT(2) NOT NULL DEFAULT '0',
  PRIMARY KEY (`voteid`,`seatid`),
  INDEX `vid` (`voteid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_process` (
  `idseq` VARCHAR(20),
  `roomid` VARCHAR(4),
  `notes` VARCHAR(100) NULL,
  `timestamp` VARCHAR(20) NULL,
  PRIMARY KEY (`idseq`),
  INDEX `rid` (`roomid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;



