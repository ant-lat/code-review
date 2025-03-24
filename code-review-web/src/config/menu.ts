/**
 * 菜单配置
 * @author Claude
 * @date 2023-07-15
 */

import { 
  DashboardOutlined, 
  ProjectOutlined, 
  BugOutlined,
  CodeOutlined, 
  BarChartOutlined, 
  UserOutlined, 
  SettingOutlined,
  BellOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { Permission } from '../utils/permission';

// 菜单项类型
export interface MenuItem {
  key: string;
  path: string;
  icon: React.ComponentType<any>;
  label: string;
  permission?: Permission | Permission[];
  children?: MenuItem[];
  hideInMenu?: boolean;
}

// 系统菜单配置
const menuConfig: MenuItem[] = [
  {
    key: 'dashboard',
    path: '/dashboard',
    icon: DashboardOutlined,
    label: '仪表盘',
    permission: 'dashboard:view'
  },
  {
    key: 'projects',
    path: '/projects',
    icon: ProjectOutlined,
    label: '项目管理',
    permission: 'project:view'
  },
  {
    key: 'issues',
    path: '/issues',
    icon: BugOutlined,
    label: '问题追踪',
    permission: 'issue:view'
  },
  {
    key: 'codeReview',
    path: '/code-review',
    icon: CodeOutlined,
    label: '代码审查',
    permission: 'code-review:view'
  },
  {
    key: 'codeAnalysis',
    path: '/code-analysis',
    icon: BarChartOutlined,
    label: '代码分析',
    permission: 'code-analysis:view'
  },
  {
    key: 'users',
    path: '/users',
    icon: UserOutlined,
    label: '用户管理',
    permission: 'user:manage'
  },
  {
    key: 'notifications',
    path: '/notifications',
    icon: BellOutlined,
    label: '通知中心',
    hideInMenu: true
  },
  {
    key: 'settings',
    path: '/settings',
    icon: SettingOutlined,
    label: '系统设置',
    permission: 'setting:manage',
    children: [
      {
        key: 'profile',
        path: '/settings/profile',
        icon: UserOutlined,
        label: '个人设置'
      },
      {
        key: 'system',
        path: '/settings/system',
        icon: SettingOutlined,
        label: '系统参数',
        permission: 'setting:system'
      }
    ]
  },
  {
    key: 'docs',
    path: '/docs',
    icon: FileTextOutlined,
    label: '帮助文档'
  }
];

export default menuConfig; 