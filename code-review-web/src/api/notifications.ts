import { get, post, put, del } from './request';
import { ResponseBase, PageResponse } from './types';

// 通知类型信息
export interface NotificationTypeInfo {
  id: string;
  name: string;
  description: string;
}

// 通知信息
export interface Notification {
  id: number;
  user_id: number;
  content: string;
  title: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  issue_id?: number;
  source_id?: number;
  source_type?: string;
  link?: string;
}

// 未读通知计数
export interface UnreadCountResponse {
  count: number;
}

/**
 * 获取用户通知列表
 */
export function getUserNotifications(params?: {
  unread_only?: boolean;
  notification_type?: string;
  search?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResponse<Notification[]>> {
  return get('/notifications', params);
}

/**
 * 获取未读通知数量
 */
export function getUnreadNotificationCount(notificationType?: string): Promise<ResponseBase<UnreadCountResponse>> {
  const params = notificationType ? { notification_type: notificationType } : undefined;
  return get('/notifications/unread-count', params);
}

/**
 * 标记多个通知为已读
 */
export function markNotificationsRead(notificationIds: number[]): Promise<ResponseBase<null>> {
  return put('/notifications/read', { notification_ids: notificationIds });
}

/**
 * 标记所有通知为已读
 */
export function markAllNotificationsRead(notificationType?: string): Promise<ResponseBase<null>> {
  const params = notificationType ? { notification_type: notificationType } : undefined;
  return put('/notifications/read/all', params);
}

/**
 * 删除单个通知
 */
export function deleteNotification(notificationId: number): Promise<ResponseBase<null>> {
  return del(`/notifications/${notificationId}`);
}

/**
 * 批量删除通知
 */
export function deleteMultipleNotifications(notificationIds: number[]): Promise<ResponseBase<null>> {
  return del('/notifications', { data: { notification_ids: notificationIds } });
}

/**
 * 获取所有通知类型
 */
export function getNotificationTypes(): Promise<ResponseBase<NotificationTypeInfo[]>> {
  return get('/notifications/types');
} 