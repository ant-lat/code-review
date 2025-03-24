import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { projectsApi } from '../../api';
import { Project, ProjectCreateParams } from '../../api/types';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  total: number;
}

const initialState: ProjectState = {
  projects: [],
  currentProject: null,
  loading: false,
  error: null,
  total: 0
};

// 获取项目列表
export const fetchProjects = createAsyncThunk(
  'projects/fetchProjects',
  async (params: any = {}, { rejectWithValue }) => {
    try {
      const response = await projectsApi.getProjects(params);
      return {
        projects: response.data,
        total: response.page_info.total
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取项目列表失败');
    }
  }
);

// 获取项目详情
export const fetchProjectById = createAsyncThunk(
  'projects/fetchProjectById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await projectsApi.getProjectById(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取项目详情失败');
    }
  }
);

// 创建项目
export const createProject = createAsyncThunk(
  'projects/createProject',
  async (data: ProjectCreateParams, { rejectWithValue }) => {
    try {
      const response = await projectsApi.createProject(data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '创建项目失败');
    }
  }
);

// 更新项目
export const updateProject = createAsyncThunk(
  'projects/updateProject',
  async ({ id, ...data }: { id: number } & Partial<ProjectCreateParams>, { rejectWithValue }) => {
    try {
      const response = await projectsApi.updateProject(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || '更新项目失败');
    }
  }
);

// 删除项目
export const deleteProject = createAsyncThunk(
  'projects/deleteProject',
  async (id: number, { rejectWithValue }) => {
    try {
      await projectsApi.deleteProject(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message || '删除项目失败');
    }
  }
);

// 获取项目统计
export const fetchProjectStats = createAsyncThunk(
  'projects/fetchProjectStats',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await projectsApi.getProjectStats(id);
      return {
        projectId: id,
        stats: response.data
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取项目统计失败');
    }
  }
);

// 获取项目活动
export const fetchProjectActivities = createAsyncThunk(
  'projects/fetchProjectActivities',
  async ({ projectId, params }: { projectId: number, params?: any }, { rejectWithValue }) => {
    try {
      const response = await projectsApi.getProjectActivities(projectId, params);
      return {
        projectId,
        activities: response.data,
        total: response.page_info.total
      };
    } catch (error: any) {
      return rejectWithValue(error.message || '获取项目活动失败');
    }
  }
);

const projectSlice = createSlice({
  name: 'projects',
  initialState,
  reducers: {
    clearProjectError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // 获取项目列表
      .addCase(fetchProjects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload.projects;
        state.total = action.payload.total;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 获取项目详情
      .addCase(fetchProjectById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProjectById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentProject = action.payload;
      })
      .addCase(fetchProjectById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 创建项目
      .addCase(createProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createProject.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(createProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 更新项目
      .addCase(updateProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateProject.fulfilled, (state, action) => {
        state.loading = false;
        // 更新项目列表中对应的项目信息
        state.projects = state.projects.map(project => 
          project.id === action.payload.id ? action.payload : project
        );
        
        // 如果当前项目是被更新的项目，则更新当前项目
        if (state.currentProject && state.currentProject.id === action.payload.id) {
          state.currentProject = action.payload;
        }
      })
      .addCase(updateProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // 删除项目
      .addCase(deleteProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.loading = false;
        // 从项目列表中移除已删除的项目
        state.projects = state.projects.filter(project => project.id !== action.payload);
        
        // 如果当前项目是被删除的项目，则清空当前项目
        if (state.currentProject && state.currentProject.id === action.payload) {
          state.currentProject = null;
        }
      })
      .addCase(deleteProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { clearProjectError } = projectSlice.actions;
export default projectSlice.reducer; 