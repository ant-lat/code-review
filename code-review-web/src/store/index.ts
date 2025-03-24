import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import notificationReducer from './slices/notificationSlice';
import userReducer from './slices/userSlice';
import projectReducer from './slices/projectSlice';
import roleReducer from './slices/roleSlice';
import menuReducer from './slices/menuSlice';

// 配置Redux store
const store = configureStore({
  reducer: {
    auth: authReducer,
    notification: notificationReducer,
    user: userReducer,
    project: projectReducer,
    role: roleReducer,
    menu: menuReducer,
  },
  // 开发环境启用Redux DevTools
  devTools: process.env.NODE_ENV !== 'production',
});

// RootState类型
export type RootState = ReturnType<typeof store.getState>;
// AppDispatch类型
export type AppDispatch = typeof store.dispatch;

export default store; 