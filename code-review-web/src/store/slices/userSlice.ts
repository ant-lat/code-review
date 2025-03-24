import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { usersApi } from '../../api';
import { User, UserCreateParams, UserUpdateParams, PasswordResetParams } from '../../api/types';

interface UserState {
  users: User[];
  currentUser: User | null;
  loading: boolean;
  error: string | null;
  total: number;
}

const initialState: UserState = {
  users: [],
  currentUser: null,
  loading: false,
  error: null,
  total: 0
};

// 获取用户列表
export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async (params: any = {}, { rejectWithValue }) => {
    try {
      const response = await usersApi.getUsers(params);
      return {
        users: response.data,
        total: response.page_info.total
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取用户列表失败');
    }
  }
);

// 获取用户详情
export const fetchUserById = createAsyncThunk(
  'users/fetchUserById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await usersApi.getUserById(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取用户详情失败');
    }
  }
);

// 创建用户
export const createUser = createAsyncThunk(
  'users/createUser',
  async (data: UserCreateParams, { rejectWithValue }) => {
    try {
      const response = await usersApi.createUser(data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '创建用户失败');
    }
  }
);

// 更新用户
export const updateUser = createAsyncThunk(
  'users/updateUser',
  async ({ id, ...data }: { id: number } & Partial<UserUpdateParams>, { rejectWithValue }) => {
    try {
      const response = await usersApi.updateUser(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '更新用户失败');
    }
  }
);

// 删除用户
export const deleteUser = createAsyncThunk(
  'users/deleteUser',
  async (id: number, { rejectWithValue }) => {
    try {
      await usersApi.deleteUser(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message || '删除用户失败');
    }
  }
);

// 切换用户状态
export const toggleUserStatus = createAsyncThunk(
  'users/toggleUserStatus',
  async ({ id, isActive }: { id: number; isActive: boolean }, { rejectWithValue }) => {
    try {
      const response = await usersApi.toggleUserStatus(id, isActive);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '切换用户状态失败');
    }
  }
);

// 重置用户密码
export const resetUserPassword = createAsyncThunk(
  'users/resetUserPassword',
  async (data: PasswordResetParams, { rejectWithValue }) => {
    try {
      await usersApi.resetUserPassword(data);
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || '重置密码失败');
    }
  }
);

const userSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    clearUserError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // 获取用户列表
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload.users;
        state.total = action.payload.total;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取用户详情
      .addCase(fetchUserById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUserById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentUser = action.payload;
      })
      .addCase(fetchUserById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 其他操作的状态更新
      .addCase(createUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createUser.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(createUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(updateUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateUser.fulfilled, (state, action) => {
        state.loading = false;
        // 更新用户列表中对应的用户信息
        state.users = state.users.map(user => 
          user.id === action.payload.id ? action.payload : user
        );
      })
      .addCase(updateUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(deleteUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.loading = false;
        // 从用户列表中移除已删除的用户
        state.users = state.users.filter(user => user.id !== action.payload);
      })
      .addCase(deleteUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(toggleUserStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(toggleUserStatus.fulfilled, (state, action) => {
        state.loading = false;
        // 更新用户列表中对应用户的状态
        state.users = state.users.map(user => 
          user.id === action.payload.id ? action.payload : user
        );
      })
      .addCase(toggleUserStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { clearUserError } = userSlice.actions;
export default userSlice.reducer; 