import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { notificationsApi } from '../../api';
import { NotificationTypeInfo } from '../../api/types';
import { transformEnum, registerEnum, EnumItem } from '../../utils/enumUtils';

interface NotificationState {
  notifications: any[];
  unreadCount: number;
  loading: boolean;
  error: string | null;
  total: number;
  notificationTypes: NotificationTypeInfo[];
}

// 初始状态
const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: null,
  total: 0,
  notificationTypes: []
};

// 获取通知列表
export const fetchNotifications = createAsyncThunk(
  'notifications/fetchNotifications',
  async (params: {
    unread_only?: boolean;
    notification_type?: string;
    search?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
    page_size?: number;
  } = {}, { rejectWithValue }) => {
    try {
      const response = await notificationsApi.getUserNotifications(params);
      return {
        notifications: response.data,
        total: response.page_info.total
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取通知失败');
    }
  }
);

// 获取未读通知数量
export const fetchUnreadCount = createAsyncThunk(
  'notifications/fetchUnreadCount',
  async (notificationType: string | undefined = undefined, { rejectWithValue }) => {
    try {
      const response = await notificationsApi.getUnreadNotificationCount(notificationType);
      // 确保返回实际的未读计数
      return response.data && typeof response.data.count === 'number' ? response.data.count : 0;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取未读通知数量失败');
    }
  }
);

// 标记通知为已读
export const markAsRead = createAsyncThunk(
  'notifications/markAsRead',
  async (notificationIds: number[], { rejectWithValue, dispatch }) => {
    try {
      await notificationsApi.markNotificationsRead(notificationIds);
      dispatch(fetchUnreadCount());
      return notificationIds;
    } catch (error: any) {
      return rejectWithValue(error.message || '标记通知已读失败');
    }
  }
);

// 将所有通知标记为已读
export const markAllAsRead = createAsyncThunk(
  'notifications/markAllAsRead',
  async (notificationType: string | undefined = undefined, { rejectWithValue, dispatch }) => {
    try {
      await notificationsApi.markAllNotificationsRead(notificationType);
      dispatch(fetchUnreadCount());
      dispatch(fetchNotifications({}));
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || '标记所有通知已读失败');
    }
  }
);

// 删除通知
export const deleteNotification = createAsyncThunk(
  'notifications/deleteNotification',
  async (notificationId: number, { rejectWithValue, dispatch }) => {
    try {
      await notificationsApi.deleteNotification(notificationId);
      dispatch(fetchNotifications({}));
      return notificationId;
    } catch (error: any) {
      return rejectWithValue(error.message || '删除通知失败');
    }
  }
);

// 批量删除通知
export const deleteMultipleNotifications = createAsyncThunk(
  'notifications/deleteMultipleNotifications',
  async (notificationIds: number[], { rejectWithValue, dispatch }) => {
    try {
      await notificationsApi.deleteMultipleNotifications(notificationIds);
      dispatch(fetchNotifications({}));
      return notificationIds;
    } catch (error: any) {
      return rejectWithValue(error.message || '批量删除通知失败');
    }
  }
);

// 获取通知类型列表
export const fetchNotificationTypes = createAsyncThunk(
  'notifications/fetchNotificationTypes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await notificationsApi.getNotificationTypes();
      
      // 转换数据并注册到枚举系统
      const transformedTypes = transformEnum(response.data, 'id', 'name');
      registerEnum('notificationType', transformedTypes);
      
      // 确保类型兼容
      const compatibleTypes: NotificationTypeInfo[] = transformedTypes.map(item => ({
        value: String(item.value), // 确保value是字符串类型
        label: item.label,
        description: item.description || ''
      }));
      
      return compatibleTypes;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取通知类型失败');
    }
  }
);

// 创建通知切片
const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    clearNotificationError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // 获取通知列表
      .addCase(fetchNotifications.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.loading = false;
        state.notifications = action.payload.notifications;
        state.total = action.payload.total;
      })
      .addCase(fetchNotifications.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取未读通知数量
      .addCase(fetchUnreadCount.fulfilled, (state, action) => {
        state.unreadCount = action.payload;
      })
      
      // 标记通知已读
      .addCase(markAsRead.fulfilled, (state, action) => {
        const notificationIds = action.payload;
        state.notifications = state.notifications.map(notification => 
          notificationIds.includes(notification.id) 
            ? { ...notification, is_read: true } 
            : notification
        );
      })
      
      // 获取通知类型
      .addCase(fetchNotificationTypes.fulfilled, (state, action) => {
        state.notificationTypes = action.payload;
      });
  }
});

export const { clearNotificationError } = notificationSlice.actions;
export default notificationSlice.reducer; 