/**
 * 枚举处理工具函数
 * @author Claude
 * @date 2023-07-15
 */

// 枚举项类型定义
export interface EnumItem {
  value: string | number;
  label: string;
  color?: string;
  status?: string;
  description?: string;
  [key: string]: any;
}

// 枚举映射类型
export type EnumMap = Record<string, EnumItem[]>;

// 全局枚举存储
const enumCache: EnumMap = {};

/**
 * 注册枚举
 * @param key 枚举键名
 * @param items 枚举项列表
 */
export function registerEnum(key: string, items: EnumItem[]): void {
  enumCache[key] = items;
}

/**
 * 从后端响应转换为前端枚举格式
 * @param data 后端返回的数据
 * @param valueField 值字段名，默认为 'id'
 * @param labelField 标签字段名，默认为 'name'
 * @returns 转换后的枚举项列表
 */
export function transformEnum(
  data: any[],
  valueField: string = 'id',
  labelField: string = 'name'
): EnumItem[] {
  return data.map(item => ({
    value: item[valueField],
    label: item[labelField],
    ...item
  }));
}

/**
 * 获取枚举列表
 * @param key 枚举键名
 * @returns 枚举项列表
 */
export function getEnumList(key: string): EnumItem[] {
  return enumCache[key] || [];
}

/**
 * 根据值获取枚举项
 * @param key 枚举键名
 * @param value 枚举值
 * @returns 枚举项或undefined
 */
export function getEnumItem(key: string, value: string | number): EnumItem | undefined {
  const list = getEnumList(key);
  return list.find(item => item.value === value);
}

/**
 * 获取枚举标签
 * @param key 枚举键名
 * @param value 枚举值
 * @param defaultValue 默认值
 * @returns 枚举标签
 */
export function getEnumLabel(key: string, value: string | number, defaultValue: string = '未知'): string {
  const item = getEnumItem(key, value);
  return item ? item.label : defaultValue;
}

/**
 * 获取枚举颜色
 * @param key 枚举键名
 * @param value 枚举值
 * @param defaultColor 默认颜色
 * @returns 枚举颜色
 */
export function getEnumColor(key: string, value: string | number, defaultColor: string = ''): string {
  const item = getEnumItem(key, value);
  return item && item.color ? item.color : defaultColor;
}

/**
 * 初始化公共枚举
 * 当应用启动时应调用此函数加载基本枚举
 */
export function initCommonEnums(): void {
  // 通知类型枚举示例
  registerEnum('notificationType', [
    { value: 'system', label: '系统通知', color: 'blue', description: '系统消息通知' },
    { value: 'issue', label: '问题通知', color: 'orange', description: '问题相关通知' },
    { value: 'review', label: '审查通知', color: 'green', description: '代码审查相关通知' },
    { value: 'mention', label: '提及通知', color: 'purple', description: '有人@你的通知' }
  ]);
  
  // 问题状态枚举示例
  registerEnum('issueStatus', [
    { value: 'open', label: '待处理', color: 'blue', status: 'processing' },
    { value: 'in_progress', label: '进行中', color: 'orange', status: 'processing' },
    { value: 'resolved', label: '已解决', color: 'green', status: 'success' },
    { value: 'closed', label: '已关闭', color: 'red', status: 'default' }
  ]);
  
  // 问题优先级枚举示例
  registerEnum('issuePriority', [
    { value: 'low', label: '低', color: 'green' },
    { value: 'medium', label: '中', color: 'orange' },
    { value: 'high', label: '高', color: 'red' },
    { value: 'critical', label: '紧急', color: 'purple' }
  ]);
  
  // 用户角色枚举示例
  registerEnum('userRole', [
    { value: 'admin', label: '管理员', color: 'red', description: '系统管理员' },
    { value: 'developer', label: '开发者', color: 'blue', description: '开发人员' },
    { value: 'reviewer', label: '审查者', color: 'green', description: '代码审查者' },
    { value: 'user', label: '普通用户', color: 'gray', description: '普通用户' }
  ]);
} 