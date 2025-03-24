import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { getUserMenus } from '../../api/permission';
import { Menu } from '../../api/permission';
import { message } from 'antd';

// 定义菜单状态类型
interface MenuState {
  menus: Menu[];
  loading: boolean;
  error: string | null;
  initialized: boolean;
}

// 初始状态
const initialState: MenuState = {
  menus: [],
  loading: false,
  error: null,
  initialized: false
};

// 异步获取用户菜单
export const fetchUserMenus = createAsyncThunk(
  'menu/fetchUserMenus',
  async (_, { rejectWithValue, getState }) => {
    try {
      console.log('开始获取用户菜单');
      const response = await getUserMenus();
      console.log('获取用户菜单成功:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('获取用户菜单失败:', error);
      return rejectWithValue(error.message || '获取用户菜单失败');
    }
  }
);

// 创建Slice
const menuSlice = createSlice({
  name: 'menu',
  initialState,
  reducers: {
    // 清除错误
    clearError: (state) => {
      state.error = null;
    },
    // 重置菜单状态
    resetMenuState: (state) => {
      state.menus = [];
      state.error = null;
      state.initialized = false;
    },
  },
  extraReducers: (builder) => {
    // 获取用户菜单
    builder
      .addCase(fetchUserMenus.pending, (state) => {
        state.loading = true;
        state.error = null;
        console.log('获取用户菜单中...');
      })
      .addCase(fetchUserMenus.fulfilled, (state, action) => {
        state.loading = false;
        state.menus = action.payload;
        state.initialized = true;
        console.log('获取用户菜单成功，更新菜单信息:', action.payload);
      })
      .addCase(fetchUserMenus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        console.error('获取用户菜单失败:', action.payload);
        state.initialized = true; // 即使失败也标记为已初始化
        message.error('获取菜单失败，您可能无法访问某些功能');
      });
  },
});

export const { clearError, resetMenuState } = menuSlice.actions;
export default menuSlice.reducer;

// 权限相关的选择器
export const selectMenus = (state: { menu: MenuState }) => state.menu.menus;
export const selectMenuLoading = (state: { menu: MenuState }) => state.menu.loading;
export const selectMenuError = (state: { menu: MenuState }) => state.menu.error;
export const selectMenuInitialized = (state: { menu: MenuState }) => state.menu.initialized;

// 辅助函数：查找菜单项
export const findMenuItem = (menus: Menu[], path: string): Menu | undefined => {
  for (const menu of menus) {
    if (menu.path === path) {
      return menu;
    }
    if (menu.children?.length) {
      const found = findMenuItem(menu.children, path);
      if (found) return found;
    }
  }
  return undefined;
};

// 辅助函数：检查菜单项是否有权限
export const hasMenuPermission = (menus: Menu[], path: string): boolean => {
  return !!findMenuItem(menus, path);
}; 