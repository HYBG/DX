CREATE TABLE `bg`.`bg_global` (
  `name` varchar(20) NOT NULL,
  `value` varchar(100) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_roles` (
  `id` int(4) NOT NULL,
  `name` varchar(16) NOT NULL COMMENT "角色名称",
  `nature` varchar(8) NOT NULL COMMENT "角色身份",
  `group` varchar(16) NOT NULL COMMENT "角色阵营",
  `skill` varchar(1024) NOT NULL COMMENT "角色技能",
  `tips` varchar(512) NOT NULL COMMENT "角色技能提示",
  PRIMARY KEY (`id`),
  INDEX `name` (`name` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_synonym` (
  `key` varchar(16) NOT NULL COMMENT "关键字",
  `id` int(4) NOT NULL COMMENT "关键字ID",
  PRIMARY KEY (`key`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_keys` (
  `id` int(4) NOT NULL COMMENT "关键字ID",
  `status` varchar(8) NOT NULL COMMENT "可以接受该关键字的角色状态",
  `comments` varchar(64) NOT NULL COMMENT "关键字描述",
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_shortcut` (
  `id` varchar(8) NOT NULL COMMENT "快捷方式ID",
  `kid` int(4) NOT NULL COMMENT "keyID",
  `conf` varchar(32) NOT NULL COMMENT "配置字符串",
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_user` (
  `extid` VARCHAR(40) NOT NULL,
  `nickname` VARCHAR(40),
  `roomid` VARCHAR(4) COMMENT "房间id",
  `seatid` INT(2) COMMENT "座位号",
  `roleid` INT(4) COMMENT "角色ID",
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
  `stage` INT(2) NOT NULL DEFAULT '0' COMMENT "当前阶段",
  PRIMARY KEY (`roomid`),
  INDEX `st` (`roomid`,`status`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_game` (
  `roomid` VARCHAR(4) NOT NULL,
  `seatid` INT(2) NOT NULL,
  `roleid` INT(4) NOT NULL,
  `player` VARCHAR(40) NOT NULL,
  `extid` VARCHAR(40) NOT NULL,
  `status` INT(1) NOT NULL DEFAULT '0' COMMENT "0:未占用,1:占用,2:冻结(有盗贼时供盗贼候选的角色状态),3:被放弃,4:被交换", 
  `live` VARCHAR(8) NOT NULL COMMENT "生存或死亡类型",
  `stage` INT(2) NOT NULL DEFAULT '0' COMMENT "生存或死亡阶段",
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
  `idseq` VARCHAR(20) NOT NULL,
  `roomid` VARCHAR(4) NOT NULL,
  `notes` VARCHAR(100) NOT NULL,
  `timestamp` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`idseq`),
  INDEX `rid` (`roomid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_votedetail` (
  `idseq` VARCHAR(20) NOT NULL,
  `roomid` VARCHAR(4) NOT NULL,
  `vfor` VARCHAR(16) NOT NULL,
  `vstring` VARCHAR(100) NOT NULL,
  `created` TIMESTAMP default now(),
  PRIMARY KEY (`idseq`),
  INDEX `rid` (`roomid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_archives` (
  `created` TIMESTAMP default now(),
  `extid` VARCHAR(40) NOT NULL,
  `seatid` INT(2) NOT NULL,
  `amount` INT(4) NOT NULL,
  `role` VARCHAR(10) NOT NULL,
  `ending` VARCHAR(16) NOT NULL,
  `stage` VARCHAR(8) NOT NULL COMMENT "生存或死亡阶段",
  PRIMARY KEY (`created`),
  INDEX `extid` (`extid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_death` (
  `id` INT(2) NOT NULL,
  `name` VARCHAR(16) NOT NULL,
  `descr` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `bg`.`bg_stage` (
  `id` INT(2) NOT NULL,
  `name` VARCHAR(16) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;



