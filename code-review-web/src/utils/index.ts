import * as XLSX from 'xlsx';
import moment from 'moment';

/**
 * 格式化日期时间
 * @param date 日期时间字符串
 * @param format 格式化模式，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期时间字符串
 */
export const formatDateTime = (date: string, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  if (!date) return '-';
  return moment(date).format(format);
};

/**
 * 格式化日期
 * @param date 日期字符串
 * @param format 格式化模式，默认为 'YYYY-MM-DD'
 * @returns 格式化后的日期字符串
 */
export const formatDate = (date: string, format: string = 'YYYY-MM-DD'): string => {
  if (!date) return '-';
  return moment(date).format(format);
};

/**
 * 格式化相对时间
 * @param dateStr 日期字符串
 * @returns 相对于当前时间的友好描述，如"刚刚"、"5分钟前"等
 */
export const formatRelativeTime = (dateStr: string): string => {
  if (!dateStr) return '-';
  
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '-';
  
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // 转换为秒
  const seconds = Math.floor(diff / 1000);
  
  if (seconds < 60) {
    return '刚刚';
  }
  
  // 转换为分钟
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}分钟前`;
  }
  
  // 转换为小时
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}小时前`;
  }
  
  // 转换为天
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days}天前`;
  }
  
  // 转换为月
  const months = Math.floor(days / 30);
  if (months < 12) {
    return `${months}个月前`;
  }
  
  // 转换为年
  const years = Math.floor(months / 12);
  return `${years}年前`;
};

/**
 * 节流函数
 * @param fn 需要节流的函数
 * @param delay 延迟时间，单位毫秒，默认为300ms
 * @returns 节流后的函数
 */
export const throttle = (fn: Function, delay: number = 300): Function => {
  let timer: ReturnType<typeof setTimeout> | null = null;
  
  return function(this: any, ...args: any[]) {
    if (timer) return;
    
    timer = setTimeout(() => {
      fn.apply(this, args);
      timer = null;
    }, delay);
  };
};

/**
 * 防抖函数
 * @param fn 需要防抖的函数
 * @param delay 延迟时间，单位毫秒，默认为300ms
 * @returns 防抖后的函数
 */
export const debounce = (fn: Function, delay: number = 300): Function => {
  let timer: ReturnType<typeof setTimeout> | null = null;
  
  return function(this: any, ...args: any[]) {
    if (timer) clearTimeout(timer);
    
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
};

/**
 * 深拷贝
 * @param obj 需要拷贝的对象
 */
export function deepCopy<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepCopy(item)) as any;
  }
  
  if (obj instanceof Object) {
    const copy: any = {};
    Object.keys(obj).forEach(key => {
      copy[key] = deepCopy((obj as any)[key]);
    });
    return copy;
  }
  
  return obj;
}

/**
 * 将对象转换为查询字符串
 * @param params 参数对象
 */
export function toQueryString(params: Record<string, any>): string {
  if (!params) return '';
  
  return Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
}

/**
 * 获取文件扩展名
 * @param filename 文件名
 */
export function getFileExtension(filename: string): string {
  if (!filename) return '';
  
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  
  return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + units[i];
}

/**
 * 导出数据到Excel文件
 * @param data 要导出的数据
 * @param filename 文件名
 */
export function exportToExcel(data: any[], filename: string = 'export') {
  try {
    // 创建工作簿
    const wb = XLSX.utils.book_new();
    
    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(data);
    
    // 将工作表添加到工作簿
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    
    // 生成文件名（添加时间戳）
    const timestamp = moment().format('YYYYMMDD_HHmmss');
    const fullFilename = `${filename}_${timestamp}.xlsx`;
    
    // 导出文件
    XLSX.writeFile(wb, fullFilename);
    
    return true;
  } catch (error) {
    console.error('导出Excel失败:', error);
    return false;
  }
} 