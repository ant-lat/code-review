-- 删除现有表（按依赖顺序）
DROP TABLE IF EXISTS issue_history CASCADE;
DROP TABLE IF EXISTS review_comments CASCADE;
DROP TABLE IF EXISTS issue_comments CASCADE;
DROP TABLE IF EXISTS review_issues CASCADE;
DROP TABLE IF EXISTS issues CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS code_commits CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS project_roles CASCADE;
DROP TABLE IF EXISTS role_menus CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS menus CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS parameters CASCADE;

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_username_email_unique UNIQUE (username, email)
);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '用户ID';
COMMENT ON COLUMN users.user_id IS '用户ID';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '电子邮箱';
COMMENT ON COLUMN users.phone IS '手机号码';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.is_active IS '是否激活';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';

-- 创建用户表的更新触发器函数
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建用户表的更新触发器
CREATE TRIGGER users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_users_updated_at();

-- 权限表
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE permissions IS '权限表';
COMMENT ON COLUMN permissions.id IS '权限ID';
COMMENT ON COLUMN permissions.code IS '权限代码';
COMMENT ON COLUMN permissions.name IS '权限名称';
COMMENT ON COLUMN permissions.description IS '权限描述';
COMMENT ON COLUMN permissions.module IS '所属模块';
COMMENT ON COLUMN permissions.created_at IS '创建时间';
COMMENT ON COLUMN permissions.updated_at IS '更新时间';

-- 创建权限表的更新触发器函数
CREATE OR REPLACE FUNCTION update_permissions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建权限表的更新触发器
CREATE TRIGGER permissions_updated_at
BEFORE UPDATE ON permissions
FOR EACH ROW
EXECUTE FUNCTION update_permissions_updated_at();

-- 角色表
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    role_type VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE roles IS '角色表';
COMMENT ON COLUMN roles.id IS '角色ID';
COMMENT ON COLUMN roles.name IS '角色名称';
COMMENT ON COLUMN roles.description IS '角色描述';
COMMENT ON COLUMN roles.role_type IS '角色类型：project或user';
COMMENT ON COLUMN roles.created_at IS '创建时间';
COMMENT ON COLUMN roles.updated_at IS '更新时间';

-- 创建角色表的更新触发器函数
CREATE OR REPLACE FUNCTION update_roles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建角色表的更新触发器
CREATE TRIGGER roles_updated_at
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION update_roles_updated_at();

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS '角色权限关联表';
COMMENT ON COLUMN role_permissions.role_id IS '角色ID';
COMMENT ON COLUMN role_permissions.permission_id IS '权限ID';
COMMENT ON COLUMN role_permissions.assigned_at IS '分配时间';

-- 用户角色关联表
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT user_role_unique UNIQUE (user_id, role_id)
);

COMMENT ON TABLE user_roles IS '用户角色关联表';
COMMENT ON COLUMN user_roles.id IS '关联ID';
COMMENT ON COLUMN user_roles.user_id IS '用户ID';
COMMENT ON COLUMN user_roles.role_id IS '角色ID';
COMMENT ON COLUMN user_roles.created_at IS '创建时间';
COMMENT ON COLUMN user_roles.expires_at IS '过期时间';
COMMENT ON COLUMN user_roles.is_active IS '是否激活';

-- 项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500) NOT NULL,
    repository_type VARCHAR(10) DEFAULT 'git',
    branch VARCHAR(100) DEFAULT 'main',
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE projects IS '项目表';
COMMENT ON COLUMN projects.id IS '项目ID';
COMMENT ON COLUMN projects.name IS '项目名称';
COMMENT ON COLUMN projects.description IS '项目描述';
COMMENT ON COLUMN projects.repository_url IS '仓库URL';
COMMENT ON COLUMN projects.repository_type IS '仓库类型';
COMMENT ON COLUMN projects.branch IS '默认分支';
COMMENT ON COLUMN projects.is_active IS '是否激活';
COMMENT ON COLUMN projects.created_by IS '创建人ID';
COMMENT ON COLUMN projects.created_at IS '创建时间';
COMMENT ON COLUMN projects.updated_at IS '更新时间';

-- 创建项目表的更新触发器函数
CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建项目表的更新触发器
CREATE TRIGGER projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_projects_updated_at();

-- 项目角色关联表
CREATE TABLE project_roles (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT project_user_role_unique UNIQUE (project_id, user_id, role_id)
);

COMMENT ON TABLE project_roles IS '项目角色关联表';
COMMENT ON COLUMN project_roles.id IS '关联ID';
COMMENT ON COLUMN project_roles.project_id IS '项目ID';
COMMENT ON COLUMN project_roles.user_id IS '用户ID';
COMMENT ON COLUMN project_roles.role_id IS '项目中的角色ID';
COMMENT ON COLUMN project_roles.joined_at IS '加入时间';
COMMENT ON COLUMN project_roles.is_active IS '是否激活';
COMMENT ON COLUMN project_roles.updated_at IS '更新时间';

-- 创建项目角色关联表的更新触发器函数
CREATE OR REPLACE FUNCTION update_project_roles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建项目角色关联表的更新触发器
CREATE TRIGGER project_roles_updated_at
BEFORE UPDATE ON project_roles
FOR EACH ROW
EXECUTE FUNCTION update_project_roles_updated_at();

-- 菜单表
CREATE TABLE menus (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(255),
    icon VARCHAR(255),
    parent_id INTEGER,
    order_num INTEGER DEFAULT 0,
    permission_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE menus IS '菜单表';
COMMENT ON COLUMN menus.id IS '菜单ID';
COMMENT ON COLUMN menus.title IS '菜单标题';
COMMENT ON COLUMN menus.path IS '菜单路径';
COMMENT ON COLUMN menus.icon IS '菜单图标';
COMMENT ON COLUMN menus.parent_id IS '父菜单ID';
COMMENT ON COLUMN menus.order_num IS '排序号';
COMMENT ON COLUMN menus.permission_id IS '对应权限ID';
COMMENT ON COLUMN menus.created_at IS '创建时间';
COMMENT ON COLUMN menus.updated_at IS '更新时间';

-- 创建菜单表的更新触发器函数
CREATE OR REPLACE FUNCTION update_menus_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建菜单表的更新触发器
CREATE TRIGGER menus_updated_at
BEFORE UPDATE ON menus
FOR EACH ROW
EXECUTE FUNCTION update_menus_updated_at();

-- 角色菜单关联表
CREATE TABLE role_menus (
    role_id INTEGER NOT NULL,
    menu_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, menu_id)
);

COMMENT ON TABLE role_menus IS '角色菜单关联表';
COMMENT ON COLUMN role_menus.role_id IS '角色ID';
COMMENT ON COLUMN role_menus.menu_id IS '菜单ID';
COMMENT ON COLUMN role_menus.assigned_at IS '分配时间';

-- 参数表
CREATE TABLE parameters (
    param_id VARCHAR(10) NOT NULL,
    param_name VARCHAR(10) NOT NULL,
    param_type VARCHAR(10) NOT NULL,
    PRIMARY KEY (param_id, param_type)
);

COMMENT ON TABLE parameters IS '参数表';
COMMENT ON COLUMN parameters.param_id IS '参数ID';
COMMENT ON COLUMN parameters.param_name IS '参数名称';
COMMENT ON COLUMN parameters.param_type IS '参数类型';

-- 代码提交表
CREATE TABLE code_commits (
    id SERIAL PRIMARY KEY,
    commit_id VARCHAR(50) NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,
    repository VARCHAR(255) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    author_id INTEGER,
    commit_message TEXT NOT NULL,
    commit_time TIMESTAMP NOT NULL,
    files_changed INTEGER DEFAULT 0,
    insertions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE code_commits IS '代码提交记录表';
COMMENT ON COLUMN code_commits.id IS '提交ID';
COMMENT ON COLUMN code_commits.commit_id IS '提交哈希';
COMMENT ON COLUMN code_commits.project_id IS '关联项目';
COMMENT ON COLUMN code_commits.repository IS '代码仓库';
COMMENT ON COLUMN code_commits.branch IS '代码分支';
COMMENT ON COLUMN code_commits.author_id IS '提交作者';
COMMENT ON COLUMN code_commits.commit_message IS '提交说明';
COMMENT ON COLUMN code_commits.commit_time IS '提交时间';
COMMENT ON COLUMN code_commits.files_changed IS '修改文件数';
COMMENT ON COLUMN code_commits.insertions IS '新增行数';
COMMENT ON COLUMN code_commits.deletions IS '删除行数';
COMMENT ON COLUMN code_commits.created_at IS '记录创建时间';

-- 问题表
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    commit_id INTEGER,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    issue_type VARCHAR(50) NOT NULL DEFAULT 'bug',
    severity VARCHAR(20),
    creator_id INTEGER,
    assignee_id INTEGER,
    file_path VARCHAR(255),
    line_start INTEGER,
    line_end INTEGER,
    resolution_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    resolved_at TIMESTAMP,
    CONSTRAINT check_issue_status CHECK (status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'reopened', 'rejected')),
    CONSTRAINT check_issue_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT check_issue_type CHECK (issue_type IN ('bug', 'feature', 'improvement', 'task', 'security', 'code_review')),
    CONSTRAINT check_issue_severity CHECK (severity IS NULL OR severity IN ('low', 'medium', 'high', 'critical'))
);

COMMENT ON TABLE issues IS '问题跟踪表（包含一般问题和代码检视问题）';
COMMENT ON COLUMN issues.id IS '问题ID';
COMMENT ON COLUMN issues.project_id IS '关联项目ID';
COMMENT ON COLUMN issues.commit_id IS '关联提交ID';
COMMENT ON COLUMN issues.title IS '问题标题';
COMMENT ON COLUMN issues.description IS '问题描述';
COMMENT ON COLUMN issues.status IS '问题状态';
COMMENT ON COLUMN issues.priority IS '问题优先级';
COMMENT ON COLUMN issues.issue_type IS '问题类型';
COMMENT ON COLUMN issues.severity IS '严重程度（代码检视问题特有）';
COMMENT ON COLUMN issues.creator_id IS '创建者ID';
COMMENT ON COLUMN issues.assignee_id IS '指派人ID';
COMMENT ON COLUMN issues.file_path IS '文件路径';
COMMENT ON COLUMN issues.line_start IS '起始行号';
COMMENT ON COLUMN issues.line_end IS '结束行号';
COMMENT ON COLUMN issues.resolution_time IS '解决时间(小时)';
COMMENT ON COLUMN issues.created_at IS '创建时间';
COMMENT ON COLUMN issues.updated_at IS '更新时间';
COMMENT ON COLUMN issues.closed_at IS '关闭时间';
COMMENT ON COLUMN issues.resolved_at IS '解决时间';

-- 创建问题表的更新触发器函数
CREATE OR REPLACE FUNCTION update_issues_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建问题表的更新触发器
CREATE TRIGGER issues_updated_at
BEFORE UPDATE ON issues
FOR EACH ROW
EXECUTE FUNCTION update_issues_updated_at();

-- 问题评论表
CREATE TABLE issue_comments (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    user_id INTEGER,
    content TEXT NOT NULL,
    file_path VARCHAR(255),
    line_number INTEGER,
    is_resolution BOOLEAN DEFAULT FALSE,
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE issue_comments IS '问题评论表';
COMMENT ON COLUMN issue_comments.id IS '评论ID';
COMMENT ON COLUMN issue_comments.issue_id IS '关联问题ID';
COMMENT ON COLUMN issue_comments.user_id IS '评论用户ID';
COMMENT ON COLUMN issue_comments.content IS '评论内容';
COMMENT ON COLUMN issue_comments.file_path IS '相关文件路径';
COMMENT ON COLUMN issue_comments.line_number IS '相关行号';
COMMENT ON COLUMN issue_comments.is_resolution IS '是否为解决方案';
COMMENT ON COLUMN issue_comments.parent_id IS '父评论ID，用于嵌套回复';
COMMENT ON COLUMN issue_comments.created_at IS '创建时间';
COMMENT ON COLUMN issue_comments.updated_at IS '更新时间';

-- 创建问题评论表的更新触发器函数
CREATE OR REPLACE FUNCTION update_issue_comments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建问题评论表的更新触发器
CREATE TRIGGER issue_comments_updated_at
BEFORE UPDATE ON issue_comments
FOR EACH ROW
EXECUTE FUNCTION update_issue_comments_updated_at();

-- 问题修改历史表
CREATE TABLE issue_history (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    user_id INTEGER,
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE issue_history IS '问题修改历史表';
COMMENT ON COLUMN issue_history.id IS '历史记录ID';
COMMENT ON COLUMN issue_history.issue_id IS '关联问题ID';
COMMENT ON COLUMN issue_history.user_id IS '操作用户ID';
COMMENT ON COLUMN issue_history.field_name IS '修改字段名';
COMMENT ON COLUMN issue_history.old_value IS '旧值';
COMMENT ON COLUMN issue_history.new_value IS '新值';
COMMENT ON COLUMN issue_history.changed_at IS '修改时间';

-- 通知表
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INTEGER NOT NULL,
    issue_id INTEGER,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notifications IS '通知表';
COMMENT ON COLUMN notifications.id IS '通知ID';
COMMENT ON COLUMN notifications.recipient_id IS '接收用户ID';
COMMENT ON COLUMN notifications.issue_id IS '关联问题ID';
COMMENT ON COLUMN notifications.type IS '通知类型';
COMMENT ON COLUMN notifications.message IS '通知内容';
COMMENT ON COLUMN notifications.is_read IS '是否已读';
COMMENT ON COLUMN notifications.read_at IS '阅读时间';
COMMENT ON COLUMN notifications.created_at IS '创建时间';

-- 代码分析结果表
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    commit_id INTEGER,
    analysis_type VARCHAR(50) NOT NULL,
    result_summary TEXT,
    details JSONB,
    code_quality_score FLOAT,
    complexity_score FLOAT,
    maintainability_score FLOAT,
    security_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE analysis_results IS '代码分析结果表';
COMMENT ON COLUMN analysis_results.id IS '分析结果ID';
COMMENT ON COLUMN analysis_results.project_id IS '关联项目ID';
COMMENT ON COLUMN analysis_results.commit_id IS '关联提交ID';
COMMENT ON COLUMN analysis_results.analysis_type IS '分析类型';
COMMENT ON COLUMN analysis_results.result_summary IS '结果摘要';
COMMENT ON COLUMN analysis_results.details IS '详细结果';
COMMENT ON COLUMN analysis_results.code_quality_score IS '代码质量得分';
COMMENT ON COLUMN analysis_results.complexity_score IS '复杂度得分';
COMMENT ON COLUMN analysis_results.maintainability_score IS '可维护性得分';
COMMENT ON COLUMN analysis_results.security_score IS '安全性得分';
COMMENT ON COLUMN analysis_results.created_at IS '创建时间';

-- 添加外键约束（可选，MySQL脚本中已注释）
-- ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
-- ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
-- 其他表的外键约束类似

-- 初始化数据
-- 添加默认用户（admin/123456）
INSERT INTO users (user_id, username, email, phone, password_hash, is_active) 
VALUES ('admin', 'admin', 'admin@example.com', '13800138000', '$2b$12$sWSdI13BJ5ipPca/5CJUmuoGwdCI2zX36Hh1bi0vcd3jRVqkwOtYW', true);

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
