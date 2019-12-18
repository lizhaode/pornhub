CREATE TABLE `channel` (
	`id` int NOT NULL AUTO_INCREMENT,
	`title` varchar(200) NOT NULL COMMENT '视频名字',
	`channel` varchar(20) NOT NULL COMMENT '视频归属片商',
	`url` text DEFAULT NULL COMMENT '视频下载链接',
	`parent_url` text DEFAULT NULL COMMENT '视频页面链接',
	`create_timestamp` timestamp NOT NULL DEFAULT current_timestamp,
	`update_timestamp` timestamp NOT NULL DEFAULT current_timestamp ON UPDATE current_timestamp,
	PRIMARY KEY (`id`),
	KEY `title` (`title`),
	KEY `channel` (`channel`)
) ENGINE = InnoDB CHARSET = utf8mb4;

CREATE TABLE `my_follow` (
	`id` int NOT NULL AUTO_INCREMENT,
	`title` varchar(200) NOT NULL COMMENT '视频名字',
	`channel` varchar(20) NOT NULL COMMENT '视频归属片商',
	`url` text DEFAULT NULL COMMENT '视频下载链接',
	`parent_url` text DEFAULT NULL COMMENT '视频页面链接',
	`create_timestamp` timestamp NOT NULL DEFAULT current_timestamp,
	`update_timestamp` timestamp NOT NULL DEFAULT current_timestamp ON UPDATE current_timestamp,
	PRIMARY KEY (`id`),
	KEY `title` (`title`),
	KEY `channel` (`channel`)
) ENGINE = InnoDB CHARSET = utf8mb4;