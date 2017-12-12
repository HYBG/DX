CREATE TABLE `hy`.`iknow_keys` (
  `keyword` VARCHAR(20) NOT NULL,
  `callback` VARCHAR(20) NOT NULL COMMENT '回调函数',
  PRIMARY KEY (`keyword`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `hy`.`iknow_global` (
  `name` VARCHAR(20) NOT NULL,
  `value` VARCHAR(40) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_name` (
  `code` varchar(6) NOT NULL,
  `name` varchar(20) NOT NULL,
  `bdcode` varchar(6) NOT NULL,
  `bdname` varchar(20) NOT NULL,
  PRIMARY KEY (`code`),
  INDEX `bd` (`bdcode` ASC))
ENGINE=InnoDB 
DEFAULT CHARACTER SET=utf8;

CREATE TABLE `iknow_rest` (
  `date` varchar(10) NOT NULL,
  PRIMARY KEY (`date`))
ENGINE=InnoDB
DEFAULT CHARACTER SET=utf8;

CREATE TABLE `iknow_user` (
  `extid` varchar(40) NOT NULL COMMENT '外部ID,例如微信公众平台openid,官网注册用户名等',
  `entrance` int(2) NOT NULL COMMENT '用户入口,0:官网注册,1:内部用户,2:微信公众平台,3....',
  `description` varchar(20) NOT NULL COMMENT '用户入口描述',
  `pic` varchar(100) COMMENT '用户头像url',
  `nickname` varchar(20) COMMENT '用户昵称',
  `uid_i` varchar(32) NOT NULL COMMENT '用户内部ID,未认证,同时也是虚拟交易账户ID',
  `uid_a` varchar(32) NOT NULL COMMENT '用户内部ID,认证,同时也是实盘交易账户ID，认证后才激活',
  `passwd_logon` varchar(30) COMMENT '登录密码',
  `passwd_trade` varchar(30) COMMENT '交易密码',
  `rdate` varchar(10) NOT NULL COMMENT '首次注册日期',
  `status` int(1) NOT NULL  DEFAULT '0' COMMENT '0:未关注,1:关注,仅对微信用户有效',
  `role` int(1) NOT NULL  DEFAULT '100' COMMENT '角色0:root,100:普通注册用户,1-99为保留值',
  `limper` double NOT NULL  DEFAULT '200000' COMMENT '永久免费额度,可提升或降低',
  `limtmp` double NOT NULL  DEFAULT '0' COMMENT '临时额度,由保证金购买',
  `retmax` double NOT NULL  DEFAULT '0.05' COMMENT '最大回撤比例(%)',
  `settlemin` double NOT NULL  DEFAULT '0.1' COMMENT '结算收益门槛',
  `sharerate` double NOT NULL  DEFAULT '0.7' COMMENT '最高分红比例',
  `period` int(2) NOT NULL  DEFAULT '0' COMMENT '最大宽限期(交易日)',
  `money_v` double NOT NULL DEFAULT '0' COMMENT '练习盘中获得的利润分红,可以转换成冬夏币',
  `money_r` double NOT NULL DEFAULT '0' COMMENT '实盘获得的分红,可以提现',
  `money_dx` double NOT NULL DEFAULT '0' COMMENT '冬夏币,用来购买实盘管理额度及资产',
  PRIMARY KEY (`extid`,`entrance`),
  INDEX `ui` (`uid_i` ASC),
  INDEX `eid` (`extid` ASC),
  INDEX `ent` (`entrance` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_account_info` (
  `uid_i` varchar(32) NOT NULL COMMENT '用户内部ID,未认证,同时也是虚拟交易账户ID',
  `uid_a` varchar(32) NOT NULL COMMENT '用户内部ID,认证,同时也是实盘交易账户ID，认证后才激活',
  `status` int(1) NOT NULL COMMENT '0:未开启,1:虚拟项目管理,2:实盘项目管理',
  PRIMARY KEY (`uid_i`),
  INDEX `uid_a` (`uid_a` ASC),
  INDEX `status` (`status` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_money_record` (
  `seqid` varchar(20) NOT NULL,
  `timestamp` varchar(24) NOT NULL COMMENT '时间戳',
  `tag` int(1) NOT NULL  COMMENT '转入转出标识1:转入,2:转出',
  `currency` int(1) NOT NULL COMMENT '货币种类1:虚拟货币,2:人民币,3:冬夏币',
  `amount` double NOT NULL COMMENT '数量',
  `fromid` int(1) COMMENT '转出用户的uid_i,系统用户用统一标识代替',
  `toid` int(1) NOT NULL COMMENT '转入用户的uid_i,系统用户用统一标识代替',
  PRIMARY KEY (`seqid`),
  INDEX `tag` (`tag` ASC),
  INDEX `cur` (`currency` ASC),
  INDEX `tc` (`tag`,`currency`),
  INDEX `fromid` (`fromid` ASC),
  INDEX `toid` (`toid` ASC),
  INDEX `ftc` (`fromid`,`tag`,`currency`),
  INDEX `ttc` (`toid`,`tag`,`currency`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_invest_account_v` (
  `uid_i` varchar(32) NOT NULL,
  `pid` VARCHAR(20) COMMENT '项目ID',
  `cash` double NOT NULL DEFAULT '0',
  `freeze` double NOT NULL DEFAULT '0',
  `worth` double NOT NULL DEFAULT '0'COMMENT '总价值,现金和股票价值的总和,每日更新',
  `status` int(1) NOT NULL DEFAULT '0' COMMENT '状态,0:正常,1:冻结,2:关闭',
  PRIMARY KEY (`uid_i`),
  CONSTRAINT `uid_i`
    FOREIGN KEY (`uid_i`)
    REFERENCES `iknow_user` (`uid_i`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

/*每日更新*/
CREATE TABLE `iknow_project_v` (
  `pid` VARCHAR(20) NOT NULL,
  `uid_i` VARCHAR(32) NOT NULL COMMENT '绑定账户ID',
  `edate` VARCHAR(10) NOT NULL COMMENT '生效日期',
  `cdate` VARCHAR(10) NULL COMMENT '关闭日期',
  `closereason` INT(1) NULL COMMENT '关闭原因0:计提关闭,1:回撤关闭,2:其他关闭(主动),3:系统关闭(被动)',
  `status` INT(1) NOT NULL DEFAULT '0' COMMENT '项目状态0:正常,1:关闭',
  `retline` double NOT NULL DEFAULT '0' COMMENT '清盘线',
  `settleline` double NOT NULL DEFAULT '0' COMMENT '结算线',
  `baseline` DOUBLE NOT NULL DEFAULT '200000' COMMENT '基准金额,计提依据的水平线',
  `peak` DOUBLE NOT NULL DEFAULT '0' COMMENT '最近峰值,清盘依据的基准线',
  PRIMARY KEY (`pid`),
  INDEX `aid` (`uid_i` ASC),
  CONSTRAINT `uid`
    FOREIGN KEY (`uid_i`)
    REFERENCES `hy`.`iknow_user` (`uid_i`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_project_hold_v` (
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `code` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  `freeze` double NOT NULL,
  PRIMARY KEY (`pid`,`code`),
  INDEX `pid` (`pid` ASC),
  CONSTRAINT `projectid`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_v` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_order_v` (
  `seqid` varchar(20) NOT NULL COMMENT '流水ID',
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `timestamp` varchar(24) NOT NULL COMMENT '时间戳',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `oper` int(1) NOT NULL COMMENT '买卖标记1:买入,2:卖出',
  `typ` int(1) NOT NULL COMMENT '0:市价单,1:限价单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `price` double NOT NULL COMMENT '订单价格',
  `status` int(1) NOT NULL COMMENT '订单状态0:已报,1:已成,2:撤单',
  PRIMARY KEY (`seqid`),
  INDEX `oid` (`orderid` ASC),
  INDEX `pid` (`pid` ASC),
  INDEX `op` (`oper` ASC),
  INDEX `tp` (`typ` ASC),
  INDEX `st` (`status` ASC),
  CONSTRAINT `ptid`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_v` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_assign_v` (
  `seqid` varchar(20) NOT NULL COMMENT '流水ID',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `efftime` varchar(20) NOT NULL COMMENT '创建时间',
  `exptime` varchar(20) NOT NULL COMMENT '过期时间',
  `code` varchar(10) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `status` int(1) NOT NULL COMMENT '状态0:待确认,1:已确认',
  PRIMARY KEY (`seqid`),
  INDEX `pid` (`pid` ASC),
  CONSTRAINT `apid`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_v` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_invest_account_r` (
  `uid_a` varchar(32) NOT NULL COMMENT '用户内部ID,认证',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `cash` double NOT NULL DEFAULT '0' COMMENT '可用金额',
  `freeze` double NOT NULL DEFAULT '0' COMMENT '冻结金额',
  `worth` double NOT NULL DEFAULT '0' COMMENT '总价值,现金和股票价值的总和,每日更新',
  `status` int(1) NOT NULL DEFAULT '0' COMMENT '状态,0:正常,1:冻结,2:关闭',
  PRIMARY KEY (`uid_a`),
  CONSTRAINT `uidaa`
    FOREIGN KEY (`uid_a`)
    REFERENCES `hy`.`iknow_user` (`uid_a`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_project_abst_r` (
  `pid` varchar(20) NOT NULL,
  `edate` varchar(10) NOT NULL COMMENT '生效日期',
  `cdate` varchar(10) DEFAULT NULL COMMENT '关闭日期',
  `closereason` int(1) DEFAULT NULL COMMENT '关闭原因0:计提关闭,1:回撤关闭,2:用户关闭,3:系统关闭',
  `status` int(1) NOT NULL DEFAULT '0' COMMENT '项目状态0:正常,1:待确认,2:冻结,3:关闭',
  `retmax` double NOT NULL COMMENT '最大回撤比例(%),子项目最大回撤在该值与子项目管理人用户表中的最大回撤取小',
  `rate` double NOT NULL DEFAULT '0' COMMENT '总收益率',
  `baseline` double NOT NULL COMMENT '初始金额',
  `peak` double NOT NULL COMMENT '最近峰值',
  PRIMARY KEY (`pid`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_project_r` (
  `pid` varchar(20) NOT NULL,
  `ppid` varchar(20) COMMENT '母项目ID',
  `uid_a` varchar(32) NOT NULL COMMENT '绑定账户ID',
  `edate` varchar(10) NOT NULL COMMENT '生效日期',
  `cdate` varchar(10) DEFAULT NULL COMMENT '关闭日期',
  `closereason` int(1) DEFAULT NULL COMMENT '关闭原因0:计提关闭,1:回撤关闭,2:用户关闭,3:系统关闭',
  `status` int(1) NOT NULL DEFAULT '0' COMMENT '项目状态0:正常,1:待确认,2:冻结,3:关闭',
  `retline` double NOT NULL COMMENT '清盘线',
  `settleline` double NOT NULL COMMENT '结算线',
  `baseline` double NOT NULL COMMENT '基准金额',
  `peak` double NOT NULL COMMENT '最近峰值',
  PRIMARY KEY (`pid`),
  INDEX `uid_a` (`uid_a` ASC),
  CONSTRAINT `uidap`
    FOREIGN KEY (`uid_a`)
    REFERENCES `hy`.`iknow_user` (`uid_a`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_project_hold_r` (
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `code` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  `freeze` double NOT NULL,
  PRIMARY KEY (`pid`,`code`),
  INDEX `pid` (`pid` ASC),
  CONSTRAINT `pid`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_v` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_assign_r` (
  `seqid` varchar(20) NOT NULL COMMENT '流水ID',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `efftime` varchar(20) NOT NULL COMMENT '创建时间',
  `exptime` varchar(20) NOT NULL COMMENT '过期时间',
  `mortgage` double COMMENT '需要追加抵押冬夏币数量',
  `code` varchar(10) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `status` int(1) NOT NULL COMMENT '状态0:待确认,1:已确认',
  PRIMARY KEY (`seqid`),
  INDEX `pid` (`pid` ASC),
  CONSTRAINT `apidr`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_v` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_order_r` (
  `seqid` varchar(20) NOT NULL COMMENT '流水ID',
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `timestamp` varchar(24) NOT NULL COMMENT '时间戳',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `spid` varchar(20) COMMENT '子项目ID',
  `oper` int(1) NOT NULL COMMENT '买卖标记0:买入,1:卖出',
  `typ` int(1) NOT NULL COMMENT '0:市价单,1:限价单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `price` double NOT NULL COMMENT '订单价格',
  `status` int(1) NOT NULL COMMENT '订单状态0:已报,1:已成,2:撤单',
  PRIMARY KEY (`seqid`),
  INDEX `oid` (`orderid` ASC),
  INDEX `pid` (`pid` ASC),
  INDEX `op` (`oper` ASC),
  INDEX `tp` (`tpy` ASC),
  INDEX `st` (`status` ASC),
  CONSTRAINT `pid`
    FOREIGN KEY (`pid`)
    REFERENCES `hy`.`iknow_project_r` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `spid`
    FOREIGN KEY (`spid`)
    REFERENCES `hy`.`iknow_subproject_r` (`pid`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;





