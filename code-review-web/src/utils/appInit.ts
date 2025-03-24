/**
 * 应用初始化工具
 * @author Claude
 * @date 2023-07-15
 */

import { initCommonEnums } from './enumUtils';
import { fetchNotificationTypes } from '../store/slices/notificationSlice';
import store from '../store';
import { hasToken } from './auth';
import { fetchCurrentUser } from '../store/slices/authSlice';

/**
 * 应用初始化
 * 在应用启动时执行以下操作：
 * 1. 初始化公共枚举
 * 2. 加载当前用户信息
 * 3. 加载通知类型
 */
export async function initializeApp(): Promise<void> {
  // 初始化基础枚举数据
  initCommonEnums();
  
  // 检查是否有token
  const hasValidToken = hasToken();
  
  if (hasValidToken) {
    try {
      // 获取用户信息
      await store.dispatch(fetchCurrentUser() as any);
      
      // 加载通知类型
      await store.dispatch(fetchNotificationTypes() as any);
    } catch (error) {
      console.error('应用初始化失败:', error);
    }
  }
}

export default initializeApp; 