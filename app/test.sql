/*
 Navicat Premium Data Transfer

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 80041
 Source Host           : 127.0.0.1:3306
 Source Schema         : test

 Target Server Type    : MySQL
 Target Server Version : 80041
 File Encoding         : 65001

 Date: 06/05/2025 00:48:36
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for test_error_log
-- ----------------------------
DROP TABLE IF EXISTS `test_error_log`;
CREATE TABLE `test_error_log`  (
  `log_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '日志的uuid',
  `error_type` int(0) NOT NULL COMMENT '错误类型（1--时间线性增长，2--一组超过其他两秒以上）',
  `created_at` timestamp(0) NULL DEFAULT NULL COMMENT '日志创建时间',
  PRIMARY KEY (`log_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试问题日志记录(主表)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for test_run_log_relation
-- ----------------------------
DROP TABLE IF EXISTS `test_run_log_relation`;
CREATE TABLE `test_run_log_relation`  (
  `log_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '日志uuid',
  `run_id` int(0) NOT NULL COMMENT '测试记录id',
  PRIMARY KEY (`log_id`, `run_id`) USING BTREE,
  INDEX `test_run_log_relation_test_runs_run_id_fk`(`run_id`) USING BTREE,
  CONSTRAINT `test_run_log_relation_test_error_log_log_id_fk` FOREIGN KEY (`log_id`) REFERENCES `test_error_log` (`log_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `test_run_log_relation_test_runs_run_id_fk` FOREIGN KEY (`run_id`) REFERENCES `test_runs` (`run_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试记录和测试日志的关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for test_runs
-- ----------------------------
DROP TABLE IF EXISTS `test_runs`;
CREATE TABLE `test_runs`  (
  `run_id` int(0) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `round_id` int(0) NOT NULL COMMENT '轮次id',
  `actual_input` json NOT NULL COMMENT '实际输入',
  `expected_output` json NOT NULL COMMENT '预期正常输出',
  `expected_error_output` json NULL COMMENT '预期异常输出',
  `expected_stuck_output` json NULL COMMENT '预期卡住输出',
  `actual_output` json NULL COMMENT '实际输出',
  `expected_duration` int(0) NOT NULL COMMENT '预期执行时间(ms)',
  `actual_duration` int(0) NOT NULL COMMENT '实际执行时间(ms)',
  `status` int(0) NOT NULL COMMENT '系统状态（1--正常 2--错误 3--卡住 4--新状态） ',
  `type` int(0) NOT NULL COMMENT '操作类型（1-唤醒操作 2-休眠操作）',
  `strategy` int(0) NOT NULL,
  PRIMARY KEY (`run_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2860 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试记录表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
