-- 角色表添加code字段的迁移脚本
-- 版本: v1 到 v2
-- 日期: 2025-03-25

-- 为roles表添加code字段（如果不存在）
ALTER TABLE roles ADD COLUMN IF NOT EXISTS code VARCHAR(50) DEFAULT NULL COMMENT '角色代码';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_roles_code ON roles (code);

-- 更新现有角色数据的code值
-- user类型角色
UPDATE roles SET code = 'system_admin' WHERE name = 'admin' AND role_type = 'user';
UPDATE roles SET code = 'ops_admin' WHERE name = 'ops' AND role_type = 'user';
UPDATE roles SET code = 'project_manager' WHERE name = 'project_manager' AND role_type = 'user';
UPDATE roles SET code = 'normal_user' WHERE name = 'user' AND role_type = 'user';

-- project类型角色
UPDATE roles SET code = 'project_admin' WHERE name = 'PM' AND role_type = 'project';
UPDATE roles SET code = 'senior_developer' WHERE name = 'SE' AND role_type = 'project';
UPDATE roles SET code = 'developer' WHERE name = 'DEV' AND role_type = 'project';
UPDATE roles SET code = 'quality_assurance' WHERE name = 'QA' AND role_type = 'project';

-- 添加唯一约束（如果需要）
-- 注意：添加前先确保没有重复的code值
ALTER TABLE roles ADD CONSTRAINT UK_roles_code UNIQUE (code);

-- 为admin用户添加项目2的PM角色（如果不存在）
INSERT INTO project_roles (project_id, user_id, role_id, joined_at, is_active)
SELECT 2, 1, 6, NOW(), TRUE
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM project_roles 
    WHERE project_id = 2 AND user_id = 1 AND role_id = 6
);

-- 版本记录
-- 在系统版本表中记录此次迁移（如果有这样的表）
-- INSERT INTO system_versions (version, description, applied_at) 
-- VALUES ('v2', '为roles表添加code字段并更新数据', NOW()); 