// 为SVG文件声明模块
declare module '*.svg' {
  const content: string;
  export default content;
}

// 为图片文件声明模块
declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

// 为CSS模块声明
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.less' {
  const classes: { [key: string]: string };
  export default classes;
}

// 全局类型定义
declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__: any;
  }

  // 用户登录状态
  interface UserState {
    id?: number;
    username?: string;
    email?: string;
    role?: string;
    isLoggedIn: boolean;
    token?: string;
    refreshToken?: string;
    permissions?: string[];
    loading: boolean;
    error?: string | null;
  }

  // 项目状态
  interface ProjectState {
    projects: any[];
    currentProject: any | null;
    loading: boolean;
    error: string | null;
    total: number;
  }

  // 问题状态
  interface IssueState {
    issues: any[];
    currentIssue: any | null;
    loading: boolean;
    error: string | null;
    total: number;
  }

  // 通知状态
  interface NotificationState {
    notifications: any[];
    unreadCount: number;
    loading: boolean;
    error: string | null;
    total: number;
    notificationTypes: NotificationTypeInfo[];
  }

  // 通知类型信息
  interface NotificationTypeInfo {
    value: string;
    label: string;
    description: string;
  }

  // 应用状态
  interface AppState {
    auth: UserState;
    projects: ProjectState;
    issues: IssueState;
    notifications: NotificationState;
    [key: string]: any;
  }

  // API请求参数
  type ApiParams = Record<string, any>;

  // API响应
  interface ApiResponse<T = any> {
    code: number;
    status: 'success' | 'error' | 'warning';
    message: string;
    timestamp: string;
    path?: string;
    data: T;
  }

  // 分页信息
  interface PageInfo {
    page: number;
    size: number;
    total: number;
    pages: number;
  }

  // 分页响应
  interface PageResponse<T = any> extends ApiResponse<T[]> {
    page_info: PageInfo;
  }
}

export {}; 