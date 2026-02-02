-- 判题库建表脚本：在「判题用的数据库」中执行此文件，学生提交的 SQL 才能正确执行。
-- 使用方式：mysql -u root -p -P 3307 sql-edu < scripts/init_judge_tables.sql
-- 或在 MySQL 客户端中：USE `sql-edu`; 然后粘贴下面内容执行。

-- 题目中使用的 orders 表（与前端「表结构（示例数据）」一致）
CREATE TABLE IF NOT EXISTS `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 示例数据（与题目 schema_preview 一致，便于判题与标准答案对比）
INSERT INTO `orders` (`id`, `user_id`, `amount`, `created_at`) VALUES
(1, 101, 100.00, '2023-01-01 10:00:00'),
(2, 101, 150.50, '2023-01-01 11:30:00'),
(3, 102, 200.00, '2023-01-01 12:00:00'),
(4, 101, 50.25,  '2023-01-02 09:00:00'),
(5, 102, 75.00,  '2023-01-02 10:15:00'),
(6, 103, 300.00, '2023-01-03 14:00:00')
ON DUPLICATE KEY UPDATE `user_id` = VALUES(`user_id`);
