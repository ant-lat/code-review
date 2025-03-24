import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { login as loginApi, getCurrentUser } from '../../api/auth';
import { User, LoginParams, LoginResult } from '../../api/types';
import { Permission, getUserPermissions as getPermissionsApi } from '../../api/permission';
import { setToken, setCurrentUser, removeToken, removeCurrentUser, getToken, getCurrentUser as getStoredUser } from '../../utils/auth';
import { message } from 'antd';

// 定义认证状态类型
interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  permissions: Permission[] | any[]; // 修改这里，允许更灵活的权限类型
  initialized: boolean; // 添加初始化状态标志
}

// 初始状态
const initialState: AuthState = {
  user: getStoredUser(),
  token: getToken(),
  loading: false,
  error: null,
  permissions: [],
  initialized: false
};

// 打印初始认证状态
console.log('初始认证状态:', {
  hasToken: !!initialState.token,
  hasUser: !!initialState.user,
  user: initialState.user
});

// 异步获取用户权限
export const fetchUserPermissions = createAsyncThunk(
  'auth/fetchUserPermissions',
  async (_, { rejectWithValue, getState }) => {
    try {
      // 获取当前状态
      const state = getState() as { auth: AuthState };
      
      // 检查是否有token
      if (!state.auth.token) {
        console.error('获取用户权限失败: 没有token');
        return rejectWithValue('获取用户权限失败: 未登录');
      }
      
      console.log('开始获取用户权限 - 调用/user-access/permissions接口');
      const response = await getPermissionsApi();
      console.log('获取用户权限成功:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('获取用户权限失败:', error);
      return rejectWithValue(error.message || '获取用户权限失败');
    }
  }
);

// 应用初始化
export const initializeAuth = createAsyncThunk(
  'auth/initialize',
  async (_, { dispatch, getState }) => {
    const state = getState() as { auth: AuthState };
    
    if (state.auth.token) {
      console.log('检测到token存在，尝试获取用户信息...');
      // 如果有token，先获取用户信息
      await dispatch(fetchCurrentUser());
      // 权限将在fetchCurrentUser成功后自动获取
    } else {
      console.log('没有检测到token，需要用户登录');
    }
    
    return { initialized: true };
  }
);

// 异步登录
export const login = createAsyncThunk(
  'auth/login',
  async (params: LoginParams, { rejectWithValue, dispatch }) => {
    try {
      console.log('开始登录流程:', params.user_id);
      const response = await loginApi(params);
      console.log('登录成功, 返回结果:', response.data);
      
      // 登录成功后立即获取用户信息
      // 权限将在fetchCurrentUser成功后自动获取
      dispatch(fetchCurrentUser());
      
      return response.data;
    } catch (error: any) {
      console.error('登录失败:', error);
      return rejectWithValue(error.message || '登录失败');
    }
  }
);

// 异步获取当前用户信息
export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue, dispatch, getState }) => {
    try {
      // 获取当前状态
      const state = getState() as { auth: AuthState };
      
      // 检查是否有token
      if (!state.auth.token) {
        console.error('获取用户信息失败: 没有token');
        return rejectWithValue('获取用户信息失败: 未登录');
      }
      
      console.log('开始获取用户信息');
      const response = await getCurrentUser();
      console.log('获取用户信息成功:', response.data);
      
      // 处理后端返回的用户数据格式
      const userData = response.data;
      
      // 如果permissions是对象数组，提取permission code到一个数组
      if (userData.permissions && Array.isArray(userData.permissions)) {
        userData.permissionCodes = userData.permissions.map((p: any) => p.code);
      }
      
      // 如果roles是对象数组，提取角色名称
      if (userData.roles && Array.isArray(userData.roles)) {
        userData.roleNames = userData.roles.map((r: any) => r.name);
      }
      
      // 获取用户信息成功后，获取用户权限
      dispatch(fetchUserPermissions());
      
      return userData;
    } catch (error: any) {
      console.error('获取用户信息失败:', error);
      // 如果是认证错误（401），则静默失败，避免弹窗提示
      if (error.response && error.response.status === 401) {
        return rejectWithValue('认证失败，请重新登录');
      }
      return rejectWithValue(error.message || '获取用户信息失败');
    }
  }
);

// 创建Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // 退出登录
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.error = null;
      state.permissions = [];
      removeToken();
      removeCurrentUser();
      console.log('用户登出，清除认证信息');
    },
    // 清除错误
    clearError: (state) => {
      state.error = null;
    },
    // 设置权限
    setPermissions: (state, action: PayloadAction<Permission[]>) => {
      state.permissions = action.payload;
    },
  },
  extraReducers: (builder) => {
    // 初始化
    builder
      .addCase(initializeAuth.fulfilled, (state, action) => {
        state.initialized = action.payload.initialized;
        console.log('认证状态初始化完成');
      });
      
    // 登录
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
        console.log('登录中...');
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access_token;
        
        // 保存token信息
        setToken(action.payload.access_token);
        
        // 登录成功后需要单独获取用户信息
        console.log('登录成功，存储令牌:', {
          token: action.payload.access_token.substring(0, 10) + '...',
          expires_in: action.payload.expires_in,
          token_type: action.payload.token_type
        });
        
        message.success('登录成功');
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        console.error('登录失败:', action.payload);
        message.error(state.error || '登录失败');
      });
    
    // 获取当前用户信息
    builder
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
        console.log('获取用户信息中...');
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        setCurrentUser(action.payload);
        console.log('获取用户信息成功，更新用户信息:', action.payload);
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        // 失败时不设置error信息，避免显示错误提示
        // state.error = action.payload as string;
        console.error('获取用户信息失败:', action.payload);
        // 如果获取用户信息失败，可能是登录过期，需要退出登录
        state.user = null;
        state.token = null;
        state.permissions = [];
        removeToken();
        removeCurrentUser();
        console.log('获取用户信息失败，清除认证状态');
      });
      
    // 获取用户权限
    builder
      .addCase(fetchUserPermissions.pending, (state) => {
        console.log('获取用户权限中...');
      })
      .addCase(fetchUserPermissions.fulfilled, (state, action) => {
        state.permissions = action.payload || [];
        console.log('获取用户权限成功:', action.payload);
        
        // 如果用户存在，更新用户的权限信息
        if (state.user) {
          // 将新的权限信息添加到用户对象中
          const permissions: Permission[] = action.payload || [];
          
          // 更新用户权限属性，使用类型断言确保类型兼容
          state.user.permissions = permissions as any;
          
          // 提取permission code到一个数组
          state.user.permissionCodes = permissions.map(p => p.code);
          
          // 更新本地存储
          setCurrentUser(state.user);
        }
      })
      .addCase(fetchUserPermissions.rejected, (state, action) => {
        console.error('获取用户权限失败:', action.payload);
        state.permissions = [];
      });
  },
});

export const { logout, clearError, setPermissions } = authSlice.actions;

export default authSlice.reducer; 