import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig, CanceledError } from 'axios';
import { getToken, removeToken } from '../utils/auth';
import { message } from 'antd';

// 请求配置
const config = {
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json; charset=utf-8',
    'Accept-Charset': 'utf-8'
  },
};

// 创建axios实例
const instance: AxiosInstance = axios.create(config);

// 添加请求拦截器
instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 获取token并添加到请求头
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.warn('未找到授权令牌，API调用可能会失败');
    }
    
    // 确保所有请求都包含正确的内容类型和字符集
    config.headers['Content-Type'] = 'application/json; charset=utf-8';
    config.headers['Accept'] = 'application/json; charset=utf-8';
    config.headers['Accept-Charset'] = 'utf-8';
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    // 判断是否需要静默处理错误（不显示错误消息）
    const config = response.config as InternalAxiosRequestConfig;
    const silent = config.headers?.['silent'] === 'true';
    
    // 从响应中提取数据
    const { data, code, message: msg } = response.data;
    
    // 处理API返回的错误
    if (code !== undefined && code !== 0 && code !== 200) {
      // 只有在非静默模式下才显示错误消息
      if (!silent) {
        message.error(msg || '请求失败');
      }
      return Promise.reject(new Error(msg || '请求失败'));
    }
    
    return response.data;
  },
  (error) => {
    // 如果请求被取消，不做处理
    if (error instanceof CanceledError) {
      console.log('请求已取消:', error.message);
      return Promise.reject(error);
    }
    
    // 判断是否需要静默处理错误（不显示错误消息）
    if (error.config) {
      const silent = error.config.headers?.['silent'] === 'true';
      if (silent) {
        return Promise.reject(error);
      }
    }
    
    // 处理错误响应
    if (error.response) {
      const { status } = error.response;
      
      // 处理401未授权错误
      if (status === 401) {
        removeToken();
        message.error('登录已过期，请重新登录');
        window.location.href = '/login';
      } 
      // 处理403权限不足错误
      else if (status === 403) {
        message.error('权限不足，无法访问');
      }
      // 处理其他服务器错误
      else if (status >= 500) {
        message.error('服务器错误，请稍后再试');
      }
      // 处理400错误
      else if (status === 400) {
        message.error(error.response.data.message || '请求参数错误');
      }
      // 处理404错误
      else if (status === 404) {
        message.error('请求的资源不存在');
      }
      // 处理其他客户端错误
      else {
        message.error(error.response.data.message || '请求失败');
      }
    } else if (error.request) {
      // 请求发出但未收到响应
      message.error('网络错误，请检查网络连接');
    } else {
      // 请求设置出错
      message.error('请求配置错误: ' + error.message);
    }
    
    return Promise.reject(error);
  }
);

// 取消所有请求（保留函数签名但简化实现）
export const cancelAllRequests = () => {
  console.log('取消所有请求功能已禁用');
};

/**
 * GET请求
 * @param url 请求地址
 * @param params 请求参数
 * @param config 请求配置
 * @returns Promise
 */
export function get<T>(url: string, params = {}, config: AxiosRequestConfig = {}): Promise<T> {
  return instance.get(url, { params, ...config });
}

/**
 * POST请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise
 */
export function post<T>(url: string, data = {}, config: AxiosRequestConfig = {}): Promise<T> {
  return instance.post(url, data, config);
}

/**
 * PUT请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise
 */
export function put<T>(url: string, data = {}, config: AxiosRequestConfig = {}): Promise<T> {
  return instance.put(url, data, config);
}

/**
 * DELETE请求
 * @param url 请求地址
 * @param config 请求配置
 * @returns Promise
 */
export function del<T>(url: string, config: AxiosRequestConfig = {}): Promise<T> {
  return instance.delete(url, config);
}

export default instance; 