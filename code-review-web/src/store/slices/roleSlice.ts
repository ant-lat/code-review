import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { usersApi } from '../../api';
import { UserRole, Permission, RolePermissionParams } from '../../api/types';

interface RoleState {
  roles: UserRole[];
  currentRole: UserRole | null;
  permissions: Permission[];
  permissionGroups: { group: string; permissions: Permission[] }[];
  loading: boolean;
  error: string | null;
}

const initialState: RoleState = {
  roles: [],
  currentRole: null,
  permissions: [],
  permissionGroups: [],
  loading: false,
  error: null
};

// 获取所有角色
export const fetchRoles = createAsyncThunk(
  'roles/fetchRoles',
  async (_, { rejectWithValue }) => {
    try {
      const response = await usersApi.getRoles();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取角色列表失败');
    }
  }
);

// 获取角色详情
export const fetchRoleById = createAsyncThunk(
  'roles/fetchRoleById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await usersApi.getRoleById(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取角色详情失败');
    }
  }
);

// 创建角色
export const createRole = createAsyncThunk(
  'roles/createRole',
  async (data: { name: string; description: string }, { rejectWithValue }) => {
    try {
      const response = await usersApi.createRole(data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '创建角色失败');
    }
  }
);

// 更新角色
export const updateRole = createAsyncThunk(
  'roles/updateRole',
  async ({ id, ...data }: { id: number; name?: string; description?: string }, { rejectWithValue }) => {
    try {
      const response = await usersApi.updateRole(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '更新角色失败');
    }
  }
);

// 删除角色
export const deleteRole = createAsyncThunk(
  'roles/deleteRole',
  async (id: number, { rejectWithValue }) => {
    try {
      await usersApi.deleteRole(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message || '删除角色失败');
    }
  }
);

// 获取所有权限
export const fetchPermissions = createAsyncThunk(
  'roles/fetchPermissions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await usersApi.getPermissions();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取权限列表失败');
    }
  }
);

// 获取权限分组
export const fetchPermissionGroups = createAsyncThunk(
  'roles/fetchPermissionGroups',
  async (_, { rejectWithValue }) => {
    try {
      const response = await usersApi.getPermissionGroups();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取权限分组失败');
    }
  }
);

// 分配角色权限
export const assignRolePermissions = createAsyncThunk(
  'roles/assignRolePermissions',
  async (data: RolePermissionParams, { rejectWithValue }) => {
    try {
      const response = await usersApi.assignRolePermissions(data);
      return {
        roleId: data.role_id,
        response: response.data
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '分配角色权限失败');
    }
  }
);

// 获取角色权限
export const fetchRolePermissions = createAsyncThunk(
  'roles/fetchRolePermissions',
  async (roleId: number, { rejectWithValue }) => {
    try {
      const response = await usersApi.getRolePermissions(roleId);
      return {
        roleId,
        permissions: response.data
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取角色权限失败');
    }
  }
);

const roleSlice = createSlice({
  name: 'roles',
  initialState,
  reducers: {
    clearRoleError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // 获取角色列表
      .addCase(fetchRoles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRoles.fulfilled, (state, action) => {
        state.loading = false;
        state.roles = action.payload;
      })
      .addCase(fetchRoles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取角色详情
      .addCase(fetchRoleById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRoleById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentRole = action.payload;
      })
      .addCase(fetchRoleById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 创建角色
      .addCase(createRole.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createRole.fulfilled, (state, action) => {
        state.loading = false;
        state.roles.push(action.payload);
      })
      .addCase(createRole.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 更新角色
      .addCase(updateRole.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateRole.fulfilled, (state, action) => {
        state.loading = false;
        state.roles = state.roles.map(role => 
          role.id === action.payload.id ? action.payload : role
        );
        if (state.currentRole && state.currentRole.id === action.payload.id) {
          state.currentRole = action.payload;
        }
      })
      .addCase(updateRole.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 删除角色
      .addCase(deleteRole.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteRole.fulfilled, (state, action) => {
        state.loading = false;
        state.roles = state.roles.filter(role => role.id !== action.payload);
        if (state.currentRole && state.currentRole.id === action.payload) {
          state.currentRole = null;
        }
      })
      .addCase(deleteRole.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取所有权限
      .addCase(fetchPermissions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPermissions.fulfilled, (state, action) => {
        state.loading = false;
        state.permissions = action.payload;
      })
      .addCase(fetchPermissions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取权限分组
      .addCase(fetchPermissionGroups.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPermissionGroups.fulfilled, (state, action) => {
        state.loading = false;
        state.permissionGroups = action.payload;
      })
      .addCase(fetchPermissionGroups.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 分配角色权限和获取角色权限
      .addCase(assignRolePermissions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(assignRolePermissions.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(assignRolePermissions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(fetchRolePermissions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRolePermissions.fulfilled, (state, action) => {
        state.loading = false;
        // 更新角色的权限
        state.roles = state.roles.map(role => {
          if (role.id === action.payload.roleId) {
            return { ...role, permissions: action.payload.permissions.map(p => p.code) };
          }
          return role;
        });
        // 如果是当前角色，更新当前角色的权限
        if (state.currentRole && state.currentRole.id === action.payload.roleId) {
          state.currentRole = { 
            ...state.currentRole, 
            permissions: action.payload.permissions.map(p => p.code) 
          };
        }
      })
      .addCase(fetchRolePermissions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { clearRoleError } = roleSlice.actions;
export default roleSlice.reducer; 