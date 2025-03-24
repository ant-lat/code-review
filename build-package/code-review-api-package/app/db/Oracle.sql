-- 删除已存在的表
DROP TABLE ci_cd_records CASCADE CONSTRAINTS;
DROP TABLE code_hotspots CASCADE CONSTRAINTS;
DROP TABLE notifications CASCADE CONSTRAINTS;
DROP TABLE role_menus CASCADE CONSTRAINTS;
DROP TABLE menus CASCADE CONSTRAINTS;
DROP TABLE role_permissions CASCADE CONSTRAINTS;
DROP TABLE permissions CASCADE CONSTRAINTS;
DROP TABLE review_comments CASCADE CONSTRAINTS;
DROP TABLE issue_history CASCADE CONSTRAINTS;
DROP TABLE review_issues CASCADE CONSTRAINTS;
DROP TABLE code_files CASCADE CONSTRAINTS;
DROP TABLE code_commits CASCADE CONSTRAINTS;
DROP TABLE project_roles CASCADE CONSTRAINTS;
DROP TABLE projects CASCADE CONSTRAINTS;
DROP TABLE users CASCADE CONSTRAINTS;

-- 创建序列
CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE projects_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE project_roles_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE code_commits_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE code_files_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE review_issues_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE review_comments_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE issue_history_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE permissions_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE menus_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE notifications_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE code_hotspots_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE ci_cd_records_seq START WITH 1 INCREMENT BY 1;

-- 用户表
CREATE TABLE users (
    id NUMBER DEFAULT users_seq.NEXTVAL PRIMARY KEY,
    username VARCHAR2(50) NOT NULL UNIQUE,
    email VARCHAR2(100) NOT NULL UNIQUE,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) CHECK (role IN ('admin', 'developer', 'reviewer')),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id NUMBER DEFAULT projects_seq.NEXTVAL PRIMARY KEY,
    name VARCHAR2(255) NOT NULL,
    repository_url VARCHAR2(500) NOT NULL,
    created_by NUMBER,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_projects_users FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 项目用户角色表
CREATE TABLE project_roles (
    id NUMBER DEFAULT project_roles_seq.NEXTVAL PRIMARY KEY,
    project_id NUMBER,
    user_id NUMBER,
    role VARCHAR2(20) CHECK (role IN ('admin', 'developer', 'architect')),
    assigned_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_project_roles_projects FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_roles_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 代码提交信息表
CREATE TABLE code_commits (
    id NUMBER DEFAULT code_commits_seq.NEXTVAL PRIMARY KEY,
    commit_id VARCHAR2(50) UNIQUE NOT NULL,
    project_id NUMBER,
    repository VARCHAR2(255) NOT NULL,
    branch VARCHAR2(100) NOT NULL,
    author_id NUMBER,
    commit_message CLOB,
    commit_time TIMESTAMP NOT NULL,
    CONSTRAINT fk_code_commits_projects FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_code_commits_users FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 代码文件表
CREATE TABLE code_files (
    id NUMBER DEFAULT code_files_seq.NEXTVAL PRIMARY KEY,
    commit_id NUMBER,
    file_path VARCHAR2(500) NOT NULL,
    content CLOB,
    CONSTRAINT fk_code_files_commits FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE
);

-- 代码检视问题表
CREATE TABLE review_issues (
    id NUMBER DEFAULT review_issues_seq.NEXTVAL PRIMARY KEY,
    project_id NUMBER,
    commit_id NUMBER,
    file_id NUMBER,
    line_start NUMBER,
    line_end NUMBER,
    issue_type VARCHAR2(50),
    description CLOB NOT NULL,
    severity VARCHAR2(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    priority VARCHAR2(20) CHECK (priority IN ('low', 'medium', 'high')),
    status VARCHAR2(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'verified', 'closed')),
    assignee_id NUMBER,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_review_issues_projects FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_issues_commits FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_issues_files FOREIGN KEY (file_id) REFERENCES code_files(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_issues_users FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 代码检视评论表
CREATE TABLE review_comments (
    id NUMBER DEFAULT review_comments_seq.NEXTVAL PRIMARY KEY,
    issue_id NUMBER,
    user_id NUMBER,
    comment CLOB NOT NULL,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_review_comments_issues FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_comments_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 问题修改历史表
CREATE TABLE issue_history (
    id NUMBER DEFAULT issue_history_seq.NEXTVAL PRIMARY KEY,
    issue_id NUMBER,
    user_id NUMBER,
    change_type VARCHAR2(50) NOT NULL,
    change_description CLOB,
    changed_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_issue_history_issues FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE,
    CONSTRAINT fk_issue_history_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 权限表
CREATE TABLE permissions (
    id NUMBER DEFAULT permissions_seq.NEXTVAL PRIMARY KEY,
    code VARCHAR2(255) NOT NULL UNIQUE,
    description CLOB NOT NULL,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id NUMBER NOT NULL,
    permission_id NUMBER NOT NULL,
    assigned_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_role_permissions PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_roles FOREIGN KEY (role_id) REFERENCES project_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_perms FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- 菜单表
CREATE TABLE menus (
    id NUMBER DEFAULT menus_seq.NEXTVAL PRIMARY KEY,
    title VARCHAR2(255) NOT NULL,
    path VARCHAR2(255),
    icon VARCHAR2(255),
    parent_id NUMBER,
    order_num NUMBER DEFAULT 0,
    permission_code VARCHAR2(255),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_menus_parent FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL
);

-- 角色菜单关联表
CREATE TABLE role_menus (
    role_id NUMBER NOT NULL,
    menu_id NUMBER NOT NULL,
    assigned_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_role_menus PRIMARY KEY (role_id, menu_id),
    CONSTRAINT fk_role_menus_roles FOREIGN KEY (role_id) REFERENCES project_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_menus_menus FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
);

-- 通知表
CREATE TABLE notifications (
    id NUMBER DEFAULT notifications_seq.NEXTVAL PRIMARY KEY,
    recipient_id NUMBER,
    issue_id NUMBER,
    message CLOB NOT NULL,
    is_read NUMBER(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_notifications_users FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_issues FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE,
    CONSTRAINT chk_notifications_is_read CHECK (is_read IN (0, 1))
);

-- 代码热点分析表
CREATE TABLE code_hotspots (
    id NUMBER DEFAULT code_hotspots_seq.NEXTVAL PRIMARY KEY,
    file_id NUMBER,
    issue_count NUMBER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_code_hotspots_files FOREIGN KEY (file_id) REFERENCES code_files(id) ON DELETE CASCADE
);

-- CI/CD 记录表
CREATE TABLE ci_cd_records (
    id NUMBER DEFAULT ci_cd_records_seq.NEXTVAL PRIMARY KEY,
    commit_id NUMBER,
    status VARCHAR2(20) CHECK (status IN ('success', 'failure', 'pending')),
    log CLOB,
    executed_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_ci_cd_records_commits FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE
);

-- 初始化角色数据
INSERT INTO users (username, email, password_hash, role, created_at) VALUES
('admin', 'admin@codereview.com', '$2b$12$5uVMWmGeeWMT2YPPs0jv.ebi6qvD.8Hp6eHu2SogY9d9Qo1cLm4qC', 'admin', SYSTIMESTAMP); -- 使用bcrypt算法生成的统一密码哈希（测试密码：Admin@123）
INSERT INTO users (username, email, password_hash, role, created_at) VALUES
('developer', 'developer@codereview.com', '$2b$12$rXKGH7W9JcC3Zq3vVjQ0DeN8q1TpO1sFwzLm2YhH5bRqA7nSvkPO', 'developer', SYSTIMESTAMP); -- 使用bcrypt算法生成的统一密码哈希（测试密码：Admin@123）
INSERT INTO users (username, email, password_hash, role, created_at) VALUES
('reviewer', 'reviewer@codereview.com', '$2b$12$tYhL8kqZdO7wS3eZvJn9BeY1qjz4WpQ2sXnM1rPcU6lVdA5qH7Dm', 'reviewer', SYSTIMESTAMP); -- 使用bcrypt算法生成的统一密码哈希（测试密码：Admin@123）

-- 添加默认项目
INSERT INTO projects (name, repository_url, created_by, created_at) VALUES
('示例项目', 'https://github.com/example/code-review-project.git', 1, SYSTIMESTAMP);

-- 添加项目角色
INSERT INTO project_roles (project_id, user_id, role, assigned_at) VALUES
(1, 1, 'admin', SYSTIMESTAMP);
INSERT INTO project_roles (project_id, user_id, role, assigned_at) VALUES
(1, 2, 'developer', SYSTIMESTAMP);
INSERT INTO project_roles (project_id, user_id, role, assigned_at) VALUES
(1, 3, 'architect', SYSTIMESTAMP);

-- 初始化权限数据
INSERT INTO permissions (code, description) VALUES
('user:view', '查看用户');
INSERT INTO permissions (code, description) VALUES
('user:create', '创建用户');
INSERT INTO permissions (code, description) VALUES
('user:edit', '编辑用户');
INSERT INTO permissions (code, description) VALUES
('user:delete', '删除用户');
INSERT INTO permissions (code, description) VALUES
('user:transfer', '转移用户');
INSERT INTO permissions (code, description) VALUES
('project:view', '查看项目');
INSERT INTO permissions (code, description) VALUES
('project:create', '创建项目');
INSERT INTO permissions (code, description) VALUES
('project:edit', '编辑项目');
INSERT INTO permissions (code, description) VALUES
('project:delete', '删除项目');
INSERT INTO permissions (code, description) VALUES
('issue:view', '查看问题');
INSERT INTO permissions (code, description) VALUES
('issue:create', '创建问题');
INSERT INTO permissions (code, description) VALUES
('issue:edit', '编辑问题');
INSERT INTO permissions (code, description) VALUES
('issue:delete', '删除问题');
INSERT INTO permissions (code, description) VALUES
('code:review', '代码审查');
INSERT INTO permissions (code, description) VALUES
('code:analyze', '代码分析');

-- 初始化菜单数据
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('系统管理', '/system', 'SettingOutlined', NULL, 1, NULL);
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('权限管理', '/system/permission', 'LockOutlined', 1, 1, NULL);
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('用户列表', '/system/permission/users', 'UserOutlined', 2, 1, 'user:view');
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('项目管理', '/projects', 'ProjectOutlined', NULL, 2, 'project:view');
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('问题管理', '/issues', 'BugOutlined', NULL, 3, 'issue:view');
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('代码审查', '/code-review', 'CodeOutlined', NULL, 4, 'code:review');
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('代码分析', '/code-analysis', 'BarChartOutlined', NULL, 5, 'code:analyze');

-- 为默认角色分配权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT pr.id, p.id
FROM project_roles pr
CROSS JOIN permissions p
WHERE 
    (pr.role = 'admin')
    OR (pr.role = 'developer' AND p.code IN (
        'project:view', 'issue:view', 'issue:create', 'issue:edit',
        'code:review'
    ))
    OR (pr.role = 'architect' AND p.code IN (
        'project:view', 'project:edit', 'issue:view', 'issue:create',
        'issue:edit', 'code:review', 'code:analyze'
    ));

-- 为默认角色分配菜单
INSERT INTO role_menus (role_id, menu_id)
SELECT pr.id, m.id
FROM project_roles pr
CROSS JOIN menus m
WHERE 
    (pr.role = 'admin')
    OR (pr.role = 'developer' AND m.path IN (
        '/projects', '/issues', '/code-review'
    ))
    OR (pr.role = 'architect' AND m.path IN (
        '/projects', '/issues', '/code-review', '/code-analysis'
    ));

-- 添加示例代码提交记录
INSERT INTO code_commits (commit_id, project_id, repository, branch, author_id, commit_message, commit_time) VALUES
('a1b2c3d4', 1, 'https://github.com/example/code-review-project.git', 'main', 2, '初始化项目结构', SYSTIMESTAMP);
INSERT INTO code_commits (commit_id, project_id, repository, branch, author_id, commit_message, commit_time) VALUES
('e5f6g7h8', 1, 'https://github.com/example/code-review-project.git', 'feature/user-management', 2, '添加用户管理功能', SYSTIMESTAMP);

-- 添加示例代码文件
INSERT INTO code_files (commit_id, file_path, content) VALUES
(1, 'src/users/users.service.ts', 'export class UsersService {\n  // 用户服务实现\n}');
INSERT INTO code_files (commit_id, file_path, content) VALUES
(1, 'src/users/users.controller.ts', 'export class UsersController {\n  // 用户控制器实现\n}');

-- 添加示例问题
INSERT INTO review_issues (project_id, commit_id, file_id, line_start, line_end, issue_type, description, severity, priority, status, assignee_id) VALUES
(1, 1, 1, 10, 15, 'code_style', '建议使用接口定义服务方法', 'low', 'low', 'open', 2);
INSERT INTO review_issues (project_id, commit_id, file_id, line_start, line_end, issue_type, description, severity, priority, status, assignee_id) VALUES
(1, 1, 2, 5, 8, 'security', '需要添加权限验证', 'high', 'high', 'open', 3);

-- 添加示例评论
INSERT INTO review_comments (issue_id, user_id, comment) VALUES
(1, 3, '请参考项目规范文档进行修改');
INSERT INTO review_comments (issue_id, user_id, comment) VALUES
(2, 1, '已添加TODO标记，下个迭代处理');

-- 添加示例问题历史
INSERT INTO issue_history (issue_id, user_id, change_type, change_description) VALUES
(1, 2, 'status_change', '问题状态从 new 变更为 open');
INSERT INTO issue_history (issue_id, user_id, change_type, change_description) VALUES
(2, 1, 'assignee_change', '指派给 reviewer 用户');

-- 添加示例通知
INSERT INTO notifications (recipient_id, issue_id, message) VALUES
(2, 1, '您有一个新的代码审查任务');
INSERT INTO notifications (recipient_id, issue_id, message) VALUES
(3, 2, '您被指派了一个高优先级的安全问题');

-- 添加示例代码热点
INSERT INTO code_hotspots (file_id, issue_count) VALUES
(1, 2);
INSERT INTO code_hotspots (file_id, issue_count) VALUES
(2, 1);

-- 添加示例CI/CD记录
INSERT INTO ci_cd_records (commit_id, status, log) VALUES
(1, 'success', 'Build and tests passed successfully');
INSERT INTO ci_cd_records (commit_id, status, log) VALUES
(2, 'pending', 'Waiting for test execution');