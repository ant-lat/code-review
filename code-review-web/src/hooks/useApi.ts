import { useState, useEffect, useRef } from 'react';
import { message } from 'antd';

/**
 * API请求钩子选项
 */
interface ApiOptions<T, P> {
  /** 是否在组件挂载时自动发起请求 */
  loadOnMount?: boolean;
  /** 请求依赖项，当依赖变化时重新请求 */
  deps?: any[];
  /** 请求参数 */
  params?: P;
  /** 是否自动处理错误 */
  autoHandleError?: boolean;
  /** 请求成功回调 */
  onSuccess?: (data: T) => void;
  /** 请求失败回调 */
  onError?: (error: any) => void;
  /** 缓存键 */
  cacheKey?: string;
  /** 缓存时间（毫秒） */
  cacheTime?: number;
}

/**
 * 使用API请求的钩子
 * @param apiFn API请求函数
 * @param options 请求选项
 * @returns 请求状态和数据
 */
function useApi<T, P = any>(
  apiFn: (params?: P) => Promise<any>,
  options: ApiOptions<T, P> = {}
) {
  const {
    loadOnMount = true,
    deps = [],
    params,
    autoHandleError = true,
    onSuccess,
    onError,
    cacheKey,
    cacheTime
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);
  
  // 使用ref跟踪当前请求状态，防止重复请求
  const requestRef = useRef<any>(null);
  // 缓存数据
  const cacheRef = useRef<{[key: string]: {data: any, timestamp: number}}>({});

  /**
   * 执行请求
   */
  const request = async (requestParams?: P) => {
    // 如果存在正在进行的相同请求，则取消当前请求
    if (requestRef.current) {
      return;
    }
    
    // 检查缓存
    if (cacheKey && cacheTime) {
      const cachedData = cacheRef.current[cacheKey];
      const now = Date.now();
      
      if (cachedData && (now - cachedData.timestamp < cacheTime)) {
        setData(cachedData.data);
        return;
      }
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // 创建请求标记
      const requestId = Date.now();
      requestRef.current = requestId;
      
      const result = await apiFn(requestParams || params);
      
      // 检查请求是否已被取消或被新请求替代
      if (requestRef.current !== requestId) {
        return;
      }
      
      console.log('API响应数据:', result);
      
      // 处理不同类型的响应格式
      let processedData;
      if (result && result.data) {
        if (result.data.items && Array.isArray(result.data.items)) {
          // 标准分页响应 {data: {items: [], total: number}}
          processedData = result;
        } else if (Array.isArray(result.data)) {
          // 直接数组响应 {data: []}
          processedData = result;
        } else {
          // 其他对象响应
          processedData = result;
        }
      } else {
        // 处理不规范响应
        console.warn('API响应格式不符合预期:', result);
        processedData = result;
      }
      
      // 更新状态
      setData(processedData);
      
      // 更新缓存
      if (cacheKey) {
        cacheRef.current[cacheKey] = {
          data: processedData,
          timestamp: Date.now()
        };
      }
      
      if (onSuccess) {
        onSuccess(processedData);
      }
    } catch (err: any) {
      // 检查请求是否已被取消或被新请求替代
      if (requestRef.current === null) {
        return;
      }
      
      setError(err);
      
      if (autoHandleError) {
        message.error(err.message || '请求失败');
      }
      
      if (onError) {
        onError(err);
      }
      
      console.error('API请求失败:', err);
    } finally {
      // 清理请求标记
      requestRef.current = null;
      setLoading(false);
    }
  };

  /**
   * 刷新数据
   */
  const refresh = () => {
    // 清除缓存
    if (cacheKey) {
      delete cacheRef.current[cacheKey];
    }
    return request(params);
  };
  
  /**
   * 获取数据函数，带参数
   */
  const fetchData = (fetchParams?: P) => {
    return request(fetchParams);
  };

  // 组件挂载时自动请求
  useEffect(() => {
    if (loadOnMount) {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 依赖项变化时刷新
  useEffect(() => {
    if (deps.length > 0) {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return {
    data,
    loading,
    error,
    refresh,
    fetchData
  };
}

export default useApi; 