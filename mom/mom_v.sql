CREATE TABLE `ikmom_rest` (
  `date` VARCHAR(10) NOT NULL,
  PRIMARY KEY (`date`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `ikmom_user` (
  `uname` varchar(40) NOT NULL COMMENT '用户名,全局唯一',
  `uid` varchar(20) NOT NULL COMMENT '用户ID,全局唯一,系统生成,内部使用',
  `rdate` varchar(10) NOT NULL COMMENT '注册日期',
  `passwd` varchar(20) NOT NULL COMMENT '登录密码',
  `level` int(2) NOT NULL  DEFAULT '0' COMMENT '0:注册用户,1以上为系统用户',
  `status` int(1) NOT NULL  DEFAULT '0' COMMENT '0:空闲中,1:模拟操作中,2:实盘操作中',
  `limper` double NOT NULL  DEFAULT '500000' COMMENT '永久免费额度,可提升或降低,只针对实盘',
  `limtmp` double NOT NULL  DEFAULT '0' COMMENT '临时额度,由保证金购买',
  `retmax` double NOT NULL  DEFAULT '0.05' COMMENT '最大回撤比例(%)',
  `settlemin` double NOT NULL  DEFAULT '0.1' COMMENT '结算收益门槛',
  `sharerate` double NOT NULL  DEFAULT '0.7' COMMENT '最高分红比例',
  `graceperiod` int(2) NOT NULL  DEFAULT '0' COMMENT '最大宽限期(交易日)',
  `auth` int(1) NOT NULL  DEFAULT '0' COMMENT '是否认证为实盘操作玩家,0:未认证,1:认证',
  PRIMARY KEY (`uname`),
  KEY `uid` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*CREATE TABLE `ikmom_user_auth_info` (
  `uid` varchar(20) NOT NULL,
  `auth` int(1) NOT NULL,
  -- 身份证件，银行信息，第三方账户，联系方式,交易密码等
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;*/

CREATE TABLE `ikmom_name` (
  `code` varchar(6) NOT NULL,
  `name` varchar(20) NOT NULL,
  `bdcode` varchar(6) NOT NULL,
  `bdname` varchar(20) NOT NULL,
  PRIMARY KEY (`code`,`name`),
  KEY `bd` (`bdcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_account` (
  `uid` varchar(20) NOT NULL,
  `money_v` double NOT NULL DEFAULT '0' COMMENT '练习盘中获得的利润分红,可以转换成冬夏币',
  `money_r` double NOT NULL DEFAULT '0' COMMENT '实盘获得的分红,可以提现',
  `money_dx` double NOT NULL DEFAULT '0' COMMENT '冬夏币,用来购买实盘管理额度及资产',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_invest_account_v` (
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `owner` varchar(20) NOT NULL COMMENT 'userid',
  `cash` double NOT NULL DEFAULT '200000' COMMENT '可用金额',
  `freeze` double NOT NULL DEFAULT '0' COMMENT '冻结金额',
  `status` int(1) NOT NULL DEFAULT '1' COMMENT '状态,0:未激活,1:闲置,2:使用中,3:关闭',
  PRIMARY KEY (`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_account_detail` (
  `seqnum` varchar(20) NOT NULL,
  `uid` varchar(20) NOT NULL,
  `date` varchar(10) NOT NULL,
  `time` varchar(10) NOT NULL,
  `mtype` double NOT NULL COMMENT '货币类型1:练习盘货币,2:现金,3:冬夏币',
  `inout` double NOT NULL COMMENT '转入转出标识0:转出,1:转入',
  `amount` double NOT NULL COMMENT '发生数量',
  `mark` varchar(40) NOT NULL COMMENT '备注',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_project_v` (
  `pid` varchar(20) NOT NULL,
  `manager` varchar(20) NOT NULL COMMENT '管理人uid',
  `status` int(1) NOT NULL DEFAULT '2' COMMENT '项目状态0:运行中不可计提,1:关闭,2:待确认,3:运行中可计提,4:冻结可计提,5:冻结不可计提',
  `retmax` double NOT NULL DEFAULT '0.05' COMMENT '最大回撤比例(%),虚拟项目该值等于管理人的retmax',
  `edate` varchar(10) NOT NULL COMMENT '生效日期',
  `cdate` varchar(10) DEFAULT NULL COMMENT '关闭日期',
  `rate` double NOT NULL DEFAULT '0' COMMENT '收益率,注入资产时调整基准金额,保持收益率不变',
  `baseline` double NOT NULL DEFAULT '200000' COMMENT '基准金额,计提依据的水平线',
  `peak` double NOT NULL DEFAULT '200000' COMMENT '最近峰值',
  PRIMARY KEY (`pid`),
  KEY `uid` (`manager`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_assign_v` (
  `seqnum` varchar(20) NOT NULL COMMENT '流水ID',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `code` varchar(10) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `price` double NOT NULL COMMENT '股票价格',
  `status` int(1) NOT NULL COMMENT '状态0:待确认,1:已确认',
  PRIMARY KEY (`seqnum`),
  KEY `pid` (`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_project_hold_v` (
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `code` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  `freeze` double NOT NULL,
  PRIMARY KEY (`pid`,`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_hold_snapshot_v` (
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `code` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  `date` varchar(10) NOT NULL COMMENT '快照生成日期',
  `time` varchar(10) NOT NULL COMMENT '快照生成时间',
  PRIMARY KEY (`pid`,`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_order_seq_v` (
  `seqnum` varchar(20) NOT NULL COMMENT '流水ID',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `date` varchar(10) NOT NULL COMMENT 'date:yyyy-mm-dd',
  `time` varchar(10) NOT NULL COMMENT 'timw:hh:mm:ss',
  `otype` int(1) NOT NULL COMMENT '指令类型0:买入,1:卖出,2:撤单',
  `orderseq` varchar(20) NOT NULL COMMENT '订单流水ID',
  PRIMARY KEY (`seqnum`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ikmom_order_v` (
  `seqnum` varchar(20) NOT NULL COMMENT '流水ID',
  `pid` varchar(20) NOT NULL COMMENT '项目ID',
  `buysell` int(1) NOT NULL COMMENT '买卖标记0:买入,1:卖出',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `price` double NOT NULL COMMENT '订单价格',
  `status` int(1) NOT NULL COMMENT '订单状态0:已报,1:已成,2:撤单',
  PRIMARY KEY (`seqnum`),
  KEY `st` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;





