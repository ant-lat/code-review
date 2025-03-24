-- 删除现有表（按依赖顺序）
DROP TABLE IF EXISTS issue_history;
DROP TABLE IF EXISTS review_comments;
DROP TABLE IF EXISTS issue_comments;
DROP TABLE IF EXISTS review_issues;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS analysis_results;
DROP TABLE IF EXISTS code_commits;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS project_roles;
DROP TABLE IF EXISTS role_menus;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS menus;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS parameters;

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(username, email)
);

-- 权限表
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    module TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色表
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    role_type TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- 用户角色关联表
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    UNIQUE(user_id, role_id)
);

-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    repository_url TEXT NOT NULL,
    repository_type TEXT DEFAULT 'git',
    branch TEXT DEFAULT 'main',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目角色关联表
CREATE TABLE project_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id, role_id)
);

-- 菜单表
CREATE TABLE menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    path TEXT,
    icon TEXT,
    parent_id INTEGER,
    order_num INTEGER DEFAULT 0,
    permission_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色菜单关联表
CREATE TABLE role_menus (
    role_id INTEGER NOT NULL,
    menu_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, menu_id)
);

-- 参数表
CREATE TABLE parameters (
    param_id TEXT NOT NULL,
    param_name TEXT NOT NULL,
    param_type TEXT NOT NULL,
    PRIMARY KEY (param_id, param_type)
);

-- 代码提交表
CREATE TABLE code_commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_id TEXT NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,
    repository TEXT NOT NULL,
    branch TEXT NOT NULL,
    author_id INTEGER,
    commit_message TEXT NOT NULL,
    commit_time TIMESTAMP NOT NULL,
    files_changed INTEGER DEFAULT 0,
    insertions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 问题表
CREATE TABLE issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    commit_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
    issue_type TEXT NOT NULL DEFAULT 'bug',
    severity TEXT,
    creator_id INTEGER,
    assignee_id INTEGER,
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    resolution_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    resolved_at TIMESTAMP,
    CHECK (status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'reopened', 'rejected')),
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CHECK (issue_type IN ('bug', 'feature', 'improvement', 'task', 'security', 'code_review')),
    CHECK (severity IS NULL OR severity IN ('low', 'medium', 'high', 'critical'))
);

-- 问题评论表
CREATE TABLE issue_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    user_id INTEGER,
    content TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    is_resolution INTEGER DEFAULT 0,
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 问题修改历史表
CREATE TABLE issue_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    user_id INTEGER,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知表
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER NOT NULL,
    issue_id INTEGER,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 代码分析结果表
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    commit_id INTEGER,
    analysis_type TEXT NOT NULL,
    result_summary TEXT,
    details TEXT,  -- SQLite不支持JSON类型，使用TEXT存储JSON数据
    code_quality_score REAL,
    complexity_score REAL,
    maintainability_score REAL,
    security_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建更新触发器
-- users表的updated_at触发器
CREATE TRIGGER users_update_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- permissions表的updated_at触发器
CREATE TRIGGER permissions_update_timestamp
AFTER UPDATE ON permissions
BEGIN
    UPDATE permissions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- roles表的updated_at触发器
CREATE TRIGGER roles_update_timestamp
AFTER UPDATE ON roles
BEGIN
    UPDATE roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- projects表的updated_at触发器
CREATE TRIGGER projects_update_timestamp
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- project_roles表的updated_at触发器
CREATE TRIGGER project_roles_update_timestamp
AFTER UPDATE ON project_roles
BEGIN
    UPDATE project_roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- menus表的updated_at触发器
CREATE TRIGGER menus_update_timestamp
AFTER UPDATE ON menus
BEGIN
    UPDATE menus SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- issues表的updated_at触发器
CREATE TRIGGER issues_update_timestamp
AFTER UPDATE ON issues
BEGIN
    UPDATE issues SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- issue_comments表的updated_at触发器
CREATE TRIGGER issue_comments_update_timestamp
AFTER UPDATE ON issue_comments
BEGIN
    UPDATE issue_comments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 添加外键约束（可选，由于SQLite的外键管理不同，不建议直接添加）
-- 如果需要添加外键约束，可以在创建表时直接指定，例如：
-- CREATE TABLE user_roles (
--     ...
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
-- );
-- 其他表的外键约束类似

-- 初始化数据
-- 添加默认用户（admin/123456）
INSERT INTO users (user_id, username, email, phone, password_hash, is_active) 
VALUES ('admin', 'admin', 'admin@example.com', '13800138000', '$2b$12$sWSdI13BJ5ipPca/5CJUmuoGwdCI2zX36Hh1bi0vcd3jRVqkwOtYW', 1);

-- 添加基本角色
INSERT INTO roles (name, description, role_type) VALUES ('管理员', '系统管理员，拥有所有权限', 'user');
INSERT INTO roles (name, description, role_type) VALUES ('项目管理员', '项目管理员，负责管理项目', 'project');
INSERT INTO roles (name, description, role_type) VALUES ('开发人员', '开发人员，负责开发代码', 'project');
INSERT INTO roles (name, description, role_type) VALUES ('审核人员', '代码审核人员，负责审核代码', 'project');
INSERT INTO roles (name, description, role_type) VALUES ('普通用户', '普通用户，仅有基本查看权限', 'user');

-- 添加基本权限
INSERT INTO permissions (code, name, description, module) 
VALUES ('user:view', '查看用户', '查看用户列表和详情', '用户管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('user:create', '创建用户', '创建新用户', '用户管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('user:edit', '编辑用户', '编辑用户信息', '用户管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('user:delete', '删除用户', '删除用户', '用户管理');

INSERT INTO permissions (code, name, description, module) 
VALUES ('role:view', '查看角色', '查看角色列表和详情', '角色管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('role:create', '创建角色', '创建新角色', '角色管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('role:edit', '编辑角色', '编辑角色信息', '角色管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('role:delete', '删除角色', '删除角色', '角色管理');

INSERT INTO permissions (code, name, description, module) 
VALUES ('project:view', '查看项目', '查看项目列表和详情', '项目管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('project:create', '创建项目', '创建新项目', '项目管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('project:edit', '编辑项目', '编辑项目信息', '项目管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('project:delete', '删除项目', '删除项目', '项目管理');

INSERT INTO permissions (code, name, description, module) 
VALUES ('issue:view', '查看问题', '查看问题列表和详情', '问题管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('issue:create', '创建问题', '创建新问题', '问题管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('issue:edit', '编辑问题', '编辑问题信息', '问题管理');
INSERT INTO permissions (code, name, description, module) 
VALUES ('issue:delete', '删除问题', '删除问题', '问题管理');

INSERT INTO permissions (code, name, description, module) 
VALUES ('review:view', '查看代码审核', '查看代码审核列表和详情', '代码审核');
INSERT INTO permissions (code, name, description, module) 
VALUES ('review:create', '创建代码审核', '创建新代码审核', '代码审核');
INSERT INTO permissions (code, name, description, module) 
VALUES ('review:edit', '编辑代码审核', '编辑代码审核信息', '代码审核');
INSERT INTO permissions (code, name, description, module) 
VALUES ('review:delete', '删除代码审核', '删除代码审核', '代码审核');

-- 关联角色和权限（管理员拥有所有权限）
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- 项目管理员权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions WHERE module IN ('项目管理', '问题管理', '代码审核');

-- 开发人员权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'review:view', 'review:create');

-- 审核人员权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 4, id FROM permissions WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'review:view', 'review:edit');

-- 普通用户权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 5, id FROM permissions WHERE code IN ('project:view', 'issue:view', 'review:view');

-- 为admin用户分配管理员角色
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1);

-- 添加系统参数
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('low', '低', 'priority');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('medium', '中', 'priority');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('high', '高', 'priority');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('critical', '严重', 'priority');

INSERT INTO parameters (param_id, param_name, param_type) VALUES ('open', '打开', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('in_progress', '进行中', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('resolved', '已解决', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('closed', '已关闭', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('reopened', '重新打开', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('rejected', '已拒绝', 'status');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('verified', '已验证', 'status');

INSERT INTO parameters (param_id, param_name, param_type) VALUES ('bug', '缺陷', 'issue_type');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('feature', '功能', 'issue_type');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('improvement', '改进', 'issue_type');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('task', '任务', 'issue_type');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('security', '安全问题', 'issue_type');
INSERT INTO parameters (param_id, param_name, param_type) VALUES ('code_review', '代码审核', 'issue_type');

-- 添加基本菜单
INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('首页', '/dashboard', 'HomeOutlined', NULL, 1);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('系统管理', '/system', 'SettingOutlined', NULL, 2);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('用户管理', '/system/users', 'UserOutlined', 2, 1);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('角色管理', '/system/roles', 'TeamOutlined', 2, 2);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('权限管理', '/system/permissions', 'SafetyOutlined', 2, 3);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('项目管理', '/projects', 'ProjectOutlined', NULL, 3);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('问题管理', '/issues', 'BugOutlined', NULL, 4);

INSERT INTO menus (title, path, icon, parent_id, order_num) 
VALUES ('代码审核', '/reviews', 'CodeOutlined', NULL, 5);

-- 关联角色和菜单
INSERT INTO role_menus (role_id, menu_id)
SELECT 1, id FROM menus;

INSERT INTO role_menus (role_id, menu_id)
SELECT 2, id FROM menus WHERE title NOT IN ('系统管理', '用户管理', '角色管理', '权限管理');

INSERT INTO role_menus (role_id, menu_id)
SELECT 3, id FROM menus WHERE title IN ('首页', '项目管理', '问题管理', '代码审核');

INSERT INTO role_menus (role_id, menu_id)
SELECT 4, id FROM menus WHERE title IN ('首页', '项目管理', '问题管理', '代码审核');

INSERT INTO role_menus (role_id, menu_id)
SELECT 5, id FROM menus WHERE title IN ('首页', '项目管理', '问题管理');
