import React, { useState, useEffect, useMemo } from 'react';
import { Row, Col, Card, Statistic, List, Tag, Spin, DatePicker, Button, Tooltip, Space, Segmented, Avatar, Badge, Empty, message, Alert } from 'antd';
import type { SegmentedProps } from 'antd';
import { 
  ProjectOutlined, 
  BugOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  RocketOutlined,
  FireOutlined,
  ThunderboltOutlined,
  UserOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  RadarChartOutlined,
  SyncOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getAllUserPerformance, getDashboardStats, getRecentActivity } from '../../api/dashboard';
import PageHeader from '../../components/PageHeader';
import { formatDateTime } from '../../utils';
import useApi from '../../hooks/useApi';
import './index.less';
import dayjs from 'dayjs';
import { Pie, Line, Column, Liquid, Gauge, Rose, Area, DualAxes, Radar } from '@ant-design/plots';
import CountUp from 'react-countup';
import type { SegmentedValue } from 'antd/es/segmented';

const { RangePicker } = DatePicker;

// 示例模拟数据，以便在没有实际数据时也能显示图表
const mockData = {
  status_distribution: [
    { status: 'open', count: 25 },
    { status: 'in_progress', count: 15 },
    { status: 'resolved', count: 42 },
    { status: 'closed', count: 18 },
    { status: 'reopened', count: 5 }
  ],
  type_distribution: [
    { issue_type: 'bug', count: 35 },
    { issue_type: 'feature', count: 22 },
    { issue_type: 'improvement', count: 18 },
    { issue_type: 'task', count: 12 },
    { issue_type: 'code_review', count: 15 },
    { issue_type: 'security', count: 8 }
  ],
  avg_resolution_time: 15.6,
  team_workload: [
    { username: '张三', open_count: 8, in_progress_count: 4 },
    { username: '李四', open_count: 6, in_progress_count: 5 },
    { username: '王五', open_count: 7, in_progress_count: 2 },
    { username: '赵六', open_count: 5, in_progress_count: 3 },
    { username: '陈七', open_count: 4, in_progress_count: 6 }
  ],
  project_issue_distribution: [
    { project_name: '项目A', total_issues: 28 },
    { project_name: '项目B', total_issues: 23 },
    { project_name: '项目C', total_issues: 19 },
    { project_name: '项目D', total_issues: 15 },
    { project_name: '项目E', total_issues: 12 }
  ],
  trend_analysis: {
    points: Array.from({ length: 15 }, (_, i) => ({
      date: dayjs().subtract(14 - i, 'day').format('YYYY-MM-DD'),
      new_issues: Math.floor(Math.random() * 10) + 1,
      resolved_issues: Math.floor(Math.random() * 8) + 1
    }))
  },
  fix_rate_trend: Array.from({ length: 15 }, (_, i) => {
    const created = Math.floor(Math.random() * 10) + 5;
    const resolved = Math.floor(Math.random() * created);
    return {
      date: dayjs().subtract(14 - i, 'day').format('YYYY-MM-DD'),
      created,
      resolved,
      fix_rate: Math.round((resolved / created) * 100),
      interval: 'day'
    };
  })
};

// 定义状态分布项的类型
interface StatusDistributionItem {
  status: string;
  count: number;
}

// 定义类型分布项的类型
interface TypeDistributionItem {
  issue_type: string;
  count: number;
}

// 定义趋势分析点的类型
interface TrendPoint {
  date: string;
  new_issues: number;
  resolved_issues: number;
}

// 定义项目问题分布项的类型
interface ProjectDistributionItem {
  project_name: string;
  total_issues: number;
}

// 定义团队工作负载项的类型
interface TeamWorkloadItem {
  username: string;
  open_count: number;
  in_progress_count?: number;
}

// 定义修复率趋势点的类型
interface FixRatePoint {
  date: string;
  created: number;
  resolved: number;
  fix_rate: number;
  interval: string;
}

// 定义仪表盘统计数据的类型
interface DashboardStats {
  status_distribution?: StatusDistributionItem[];
  type_distribution?: TypeDistributionItem[];
  avg_resolution_time?: number;
  team_workload?: TeamWorkloadItem[];
  project_issue_distribution?: ProjectDistributionItem[];
  trend_analysis?: {
    points: TrendPoint[];
  };
  fix_rate_trend?: FixRatePoint[];
}

// 定义用户性能数据的类型
interface UserPerformance {
  user_id: number;
  username: string;
  total_issues_created: number;
  resolved_issues: number;
  avg_resolution_time: number;
  resolution_rate: number;
  activity_count: number;
  quality_score: number;
}

// 定义活动项的类型
interface ActivityItem {
  id: number;
  user_id: number;
  user_name: string;
  action: string;
  target_type: string;
  target_id: number;
  status?: string;
  created_at: string;
}

// 接口返回值类型
interface ApiResponse<T> {
  data: T;
  code?: number;
  message?: string;
}

const Dashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [refreshing, setRefreshing] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  const navigate = useNavigate();

  // 默认使用最近30天的数据
  const end = dayjs();
  const start = dayjs().subtract(30, 'day');
  const defaultDateFilters = {
    start_date: start.format('YYYY-MM-DD'),
    end_date: end.format('YYYY-MM-DD')
  };

  // 使用useApi hook处理API请求
  const {
    data: stats,
    loading: statsLoading,
    refresh: refreshStats,
    fetchData: fetchStats
  } = useApi<ApiResponse<DashboardStats>>(getDashboardStats, {
    loadOnMount: true,
    params: defaultDateFilters,
    cacheKey: 'dashboard-stats',
    cacheTime: 60000, // 1分钟缓存
    onError: () => {
      message.error('加载数据失败，已切换到演示模式');
      setUseMockData(true);
    }
  });

  const {
    data: activitiesResponse,
    loading: activitiesLoading,
    refresh: refreshActivities
  } = useApi<ApiResponse<ActivityItem[]>>(
    () => getRecentActivity(1, 10), 
    {
    loadOnMount: true,
    cacheKey: 'dashboard-activities',
    cacheTime: 60000, // 1分钟缓存
      onError: () => setUseMockData(true)
    }
  );

  const {
    data: performanceResponse,
    loading: performanceLoading,
    refresh: refreshPerformance,
    fetchData: fetchPerformance
  } = useApi<ApiResponse<UserPerformance[]>>(getAllUserPerformance, {
    loadOnMount: true,
    params: defaultDateFilters,
    cacheKey: 'dashboard-performance',
    cacheTime: 60000, // 1分钟缓存
    onError: () => setUseMockData(true)
  });

  // 从响应中提取活动和性能数据，如果没有数据则使用模拟数据
  const activities = activitiesResponse?.data || [];
  const performance = performanceResponse?.data || [];

  // 决定是否使用模拟数据
  const dashboardData = useMockData || !stats?.data || Object.keys(stats.data).length === 0 ? mockData : stats.data;

  // 将所有useMemo钩子移到组件顶层
  // 计算问题总数
  const totalIssues = useMemo(() => {
    return dashboardData?.status_distribution?.reduce(
      (total, item) => total + (item?.count || 0), 0
    ) || 0;
  }, [dashboardData?.status_distribution]);

  // 计算开放问题数
  const openIssues = useMemo(() => {
    return dashboardData?.status_distribution?.find(
      (item) => item?.status === 'open'
    )?.count || 0;
  }, [dashboardData?.status_distribution]);

  // 计算解决问题数
  const resolvedIssues = useMemo(() => {
    return dashboardData?.status_distribution?.find(
      (item) => item?.status === 'resolved'
    )?.count || 0;
  }, [dashboardData?.status_distribution]);

  // 计算项目总数
  const totalProjects = useMemo(() => {
    return dashboardData?.project_issue_distribution?.length || 0;
  }, [dashboardData?.project_issue_distribution]);

  // 计算解决率
  const resolutionRate = useMemo(() => {
    return totalIssues > 0 ? resolvedIssues / totalIssues : 0;
  }, [totalIssues, resolvedIssues]);

  // 设置初始日期范围
  useEffect(() => {
    setDateRange([start, end]);
  }, []);

  const handleThemeChange = (value: SegmentedValue) => {
    setTheme(value.toString() as 'light' | 'dark');
    document.body.className = value.toString() === 'dark' ? 'dark-theme' : 'light-theme';
  };

  const handleDateRangeChange = (dates: any) => {
    setDateRange(dates);
  };

  const handleFilterClick = () => {
    if (dateRange && dateRange[0] && dateRange[1]) {
      const date_filters = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD')
      };
      
      // 使用新的日期过滤条件重新获取数据
      fetchStats(date_filters);
      fetchPerformance(date_filters);
      message.success('数据已更新');
    }
  };

  const handleResetFilters = () => {
    const end = dayjs();
    const start = dayjs().subtract(30, 'day');
    setDateRange([start, end]);
    
    // 重置为默认日期过滤条件
    fetchStats(defaultDateFilters);
    fetchPerformance(defaultDateFilters);
    message.info('已重置为默认时间范围');
  };

  const handleRefreshAll = () => {
    setRefreshing(true);
    Promise.all([
      refreshStats(),
      refreshActivities(),
      refreshPerformance()
    ]).finally(() => {
      setTimeout(() => {
        setRefreshing(false);
        message.success('数据已刷新');
      }, 800);
    });
  };

  // 渲染状态分布图表
  const renderStatusDistribution = () => {
    if (!dashboardData?.status_distribution) return <Empty description="暂无数据" />;

    const data = dashboardData.status_distribution.map((item: StatusDistributionItem) => ({
      type: item.status === 'open' ? '待处理' :
            item.status === 'in_progress' ? '处理中' :
            item.status === 'resolved' ? '已解决' :
            item.status === 'verified' ? '已验证' :
            item.status === 'closed' ? '已关闭' :
            item.status === 'reopened' ? '重新打开' : '其他',
      value: item.count
    }));

    const config = {
      data,
      theme: theme === 'dark' ? 'dark' : 'light',
      angleField: 'value',
      colorField: 'type',
      radius: 0.8,
      innerRadius: 0.6,
      autoFit: true,
      appendPadding: [12, 0, 0, 0],
      legend: {
        layout: 'horizontal',
        position: 'bottom'
      },
      label: {
        type: 'spider',
        labelHeight: 40,
        formatter: (data: any) => {
          const percent = (data.percent * 100).toFixed(2);
          return `${data.type}: ${percent}%`;
        }
      },
      statistic: {
        title: {
          customHtml: () => '状态分布',
          style: {
            fontSize: '16px',
            fontWeight: 600,
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : 'rgba(0, 0, 0, 0.85)'
          }
        },
        content: {
          customHtml: (container: any, view: any, datum: any) => {
            const total = data.reduce((acc, item) => acc + item.value, 0);
            return `<span style="color: ${theme === 'dark' ? '#fff' : '#000'}; font-size: 24px; font-weight: 600;">${total}</span>`;
          }
        }
      }
    };

    return (
      <Card 
        title={<div><PieChartOutlined className="icon-pulse" style={{marginRight: 8}} /> 问题状态分布</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container">
          <Pie {...config} />
        </div>
      </Card>
    );
  };

  // 渲染类型分布图表
  const renderTypeDistribution = () => {
    if (!dashboardData?.type_distribution) return <Empty description="暂无数据" />;

    const data = dashboardData.type_distribution.map(item => ({
      type: item.issue_type === 'bug' ? '缺陷' :
            item.issue_type === 'feature' ? '功能' :
            item.issue_type === 'improvement' ? '改进' :
            item.issue_type === 'task' ? '任务' :
            item.issue_type === 'code_review' ? '代码审查' :
            item.issue_type === 'security' ? '安全问题' : '其他',
      value: item.count
    }));

    const config = {
      data,
      theme: theme === 'dark' ? 'dark' : 'light',
      xField: 'type',
      yField: 'value',
      seriesField: 'type',
      radius: 0.9,
      legend: { position: 'bottom' },
      color: ['#3b82f6', '#f97316', '#22c55e', '#8b5cf6', '#f43f5e', '#64748b'],
      pattern: ({ type }: { type: string }) => {
        return {
          type: 'line',
          cfg: {
            stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.05)',
          },
        }
      },
      label: {
        offset: -15,
        formatter: (text: any) => {
          return `${text.value}`;
        },
        style: {
          fill: theme === 'dark' ? '#fff' : '#000',
          fontSize: 14,
          fontWeight: 600,
          textShadow: theme === 'dark' ? '0 2px 4px rgba(0, 0, 0, 0.3)' : 'none',
        }
      },
      tooltip: {
        formatter: (item: any) => {
          return { name: item.type, value: item.value };
        },
        customContent: (title: string, data: any) => {
          return `<div style="padding: 8px 12px;">
            <div style="color: ${theme === 'dark' ? '#fff' : '#000'}; font-weight: bold; margin-bottom: 8px;">
              ${title}
            </div>
            ${data.map((item: any) => {
              return `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="margin-right: 16px; display: flex; align-items: center;">
                  <span style="background-color: ${item.color}; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px;"></span>
                  <span>${item.name}:</span>
                </span>
                <span style="font-weight: bold;">${item.value}</span>
              </div>`;
            }).join('')}
          </div>`;
        }
      },
      animation: {
        appear: {
          animation: 'wave-in',
          duration: 1500
        },
        update: {
          animation: 'zoom-canvas',
          duration: 1000
        }
      },
      interactions: [
        { type: 'element-active' },
        { type: 'legend-highlight' }
      ],
      sectorStyle: {
        shadowColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.1)',
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowOffsetY: 0,
        stroke: 'transparent'
      }
    };

    return (
      <Card 
        title={<div><RadarChartOutlined className="icon-pulse" style={{marginRight: 8}} /> 问题类型分布</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          <Rose {...config} />
        </div>
      </Card>
    );
  };

  // 渲染趋势分析图表
  const renderTrendAnalysis = () => {
    if (!dashboardData?.trend_analysis?.points) return <Empty description="暂无数据" />;

    const data = dashboardData.trend_analysis.points.map((point: TrendPoint) => [
      {
        date: point.date,
        value: point.new_issues,
        category: '新增问题'
      },
      {
        date: point.date,
        value: point.resolved_issues,
        category: '解决问题'
      }
    ]).flat();

    const config = {
      data,
      theme: theme === 'dark' ? 'dark' : 'light',
      xField: 'date',
      yField: 'value',
      seriesField: 'category',
      color: ['#3b82f6', '#10b981'],
      lineStyle: ({ category }: { category: string }) => {
        if (category === '新增问题') {
          return {
            lineDash: [0, 0],
            lineWidth: 3,
            stroke: '#3b82f6',
            shadowColor: 'rgba(59, 130, 246, 0.5)',
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            cursor: 'pointer'
          };
        }
        return {
          lineDash: [0, 0],
          lineWidth: 3,
          stroke: '#10b981',
          shadowColor: 'rgba(16, 185, 129, 0.5)',
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowOffsetY: 0,
          cursor: 'pointer'
        };
      },
      point: {
        size: 6,
        shape: 'diamond',
        style: ({ category }: { category: string }) => {
          return {
            fill: category === '新增问题' ? '#3b82f6' : '#10b981',
            stroke: 'white',
            lineWidth: 2,
            r: 6,
            shadowColor: category === '新增问题' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(16, 185, 129, 0.5)',
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            cursor: 'pointer'
          };
        }
      },
      tooltip: {
        showMarkers: true,
        shared: true,
        showCrosshairs: true,
        crosshairs: {
          type: 'xy',
          line: {
            style: {
              stroke: '#D9D9D9',
              lineWidth: 1,
              lineDash: [4, 4],
            }
          }
        },
        customContent: (title: string, data: any) => {
          return `<div style="padding: 8px 12px;">
            <div style="color: ${theme === 'dark' ? '#fff' : '#000'}; font-weight: bold; margin-bottom: 8px;">
              日期: ${title}
            </div>
            ${data.map((item: any) => {
              return `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="margin-right: 16px; display: flex; align-items: center;">
                  <span style="background-color: ${item.color}; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px;"></span>
                  <span>${item.name}:</span>
                </span>
                <span style="font-weight: bold;">${item.value}</span>
              </div>`;
            }).join('')}
          </div>`;
        }
      },
      smooth: true,
      animation: {
        appear: {
          animation: 'path-in',
          duration: 1200,
          easing: 'cubic-bezier(0.23, 1, 0.32, 1)'
        },
        update: {
          animation: 'scale-in-y',
          duration: 1000
        }
      },
      area: {
        style: ({ category }: { category: string }) => {
          return {
            fill: category === '新增问题'
              ? 'l(270) 0:rgba(59, 130, 246, 0.01) 0.5:rgba(59, 130, 246, 0.2) 1:rgba(59, 130, 246, 0.4)'
              : 'l(270) 0:rgba(16, 185, 129, 0.01) 0.5:rgba(16, 185, 129, 0.2) 1:rgba(16, 185, 129, 0.4)',
            fillOpacity: 0.7,
            stroke: category === '新增问题' ? '#3b82f6' : '#10b981',
            lineWidth: 0,
          };
        }
      },
      legend: {
        position: 'top-right',
        marker: {
          symbol: 'circle'
        },
        itemName: {
          style: {
            fill: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : 'rgba(0, 0, 0, 0.85)',
            fontWeight: 500
          }
        }
      },
      meta: {
        date: {
          alias: '日期',
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}月${date.getDate()}日`;
          }
        },
        value: {
          alias: '数量',
          formatter: (value: number) => `${value} 个`
        }
      },
      xAxis: {
        label: {
          autoRotate: true,
          autoHide: false,
          formatter: (text: string) => {
            const date = new Date(text);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          }
        },
        tickLine: {
          style: {
            lineWidth: 1,
            stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.15)'
          }
        },
        line: {
          style: {
            stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.15)'
          }
        },
        tickCount: 7
      },
      yAxis: {
        label: {
          formatter: (text: string) => {
            return text;
          }
        },
        grid: {
          line: {
            style: {
              stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
              lineWidth: 1,
              lineDash: [4, 4]
            }
          }
        }
      },
      interactions: [
        { type: 'element-highlight' },
        { type: 'legend-highlight' },
        { type: 'axis-label-highlight' }
      ]
    };

    return (
      <Card 
        title={<div><LineChartOutlined className="icon-pulse" style={{marginRight: 8}} /> 趋势分析</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          <Area {...config} />
        </div>
      </Card>
    );
  };

  // 渲染问题修复率趋势图表
  const renderFixRateTrend = () => {
    if (!dashboardData?.fix_rate_trend) return <Empty description="暂无数据" />;

    const data = dashboardData.fix_rate_trend.map((item: FixRatePoint) => ({
      date: item.date,
      value: item.fix_rate,
      type: '修复率(%)'
    }));

    const volumeData = dashboardData.fix_rate_trend.map((item: FixRatePoint) => [
      {
        date: item.date,
        value: item.created,
        type: '新增问题'
      },
      {
        date: item.date,
        value: item.resolved,
        type: '已解决问题'
      }
    ]).flat();

    const config = {
      data: [volumeData, data],
      theme: theme === 'dark' ? 'dark' : 'light',
      xField: 'date',
      yField: ['value', 'value'],
      geometryOptions: [
        {
          geometry: 'column',
          isGroup: true,
          seriesField: 'type',
          columnWidthRatio: 0.7,
          columnStyle: {
            radius: [4, 4, 0, 0]
          },
          color: ['#4096ff', '#15b981'],
          label: {
            position: 'middle'
          }
        },
        {
          geometry: 'line',
          color: '#f43f5e',
          lineStyle: {
            lineWidth: 3,
            lineDash: [4, 4]
          },
          point: {
            shape: 'circle',
            size: 5,
            style: {
              fill: '#f43f5e',
              stroke: '#fff',
              lineWidth: 2
            }
          },
          label: {
            formatter: (item: any) => {
              return `${item.value}%`;
            }
          }
        }
      ],
      legend: {
        position: 'top'
      },
      tooltip: {
        shared: true,
        showCrosshairs: true
      },
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 1500
        }
      }
    };

    return (
      <Card 
        title={<div><LineChartOutlined className="icon-pulse" style={{marginRight: 8}} /> 问题修复率趋势</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          <DualAxes {...config} />
        </div>
      </Card>
    );
  };

  // 渲染项目问题分布图表
  const renderProjectDistribution = () => {
    if (!dashboardData?.project_issue_distribution) return <Empty description="暂无数据" />;

    const data = [...dashboardData.project_issue_distribution]
      .sort((a, b) => b.total_issues - a.total_issues)
      .slice(0, 5)
      .map((item: ProjectDistributionItem) => ({
        project: item.project_name,
        issues: item.total_issues
      }));

    const config = {
      data,
      theme: theme === 'dark' ? 'dark' : 'light',
      xField: 'issues',
      yField: 'project',
      seriesField: 'project',
      legend: { position: 'bottom' },
      color: ({ project }: { project: string }) => {
        const colorMap: Record<string, string> = {};
        const colors = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899'];
        
        data.forEach((item, index) => {
          colorMap[item.project] = colors[index % colors.length];
        });
        
        return colorMap[project] || colors[0];
      },
      label: {
        position: 'right',
        style: {
          fill: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : 'rgba(0, 0, 0, 0.85)',
        },
      },
      barStyle: {
        radius: [0, 4, 4, 0],
      },
      animation: {
        appear: {
          animation: 'scale-in-x',
          duration: 1000,
        },
      },
    };

    return (
      <Card 
        title={<div><ProjectOutlined className="icon-pulse" style={{marginRight: 8}} /> 项目问题分布</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          {data.length > 0 ? <Column {...config} /> : <Empty description="暂无项目数据" />}
        </div>
      </Card>
    );
  };

  // 渲染团队工作负载
  const renderTeamWorkload = () => {
    if (!dashboardData?.team_workload) return <Empty description="暂无数据" />;

    const data = [...dashboardData.team_workload]
      .sort((a, b) => (b.open_count + (b.in_progress_count || 0)) - (a.open_count + (a.in_progress_count || 0)))
      .slice(0, 5)
      .map((item: TeamWorkloadItem) => [
        {
          username: item.username,
          count: item.open_count,
          type: '待处理'
        },
        {
          username: item.username,
          count: item.in_progress_count || 0,
          type: '处理中'
        }
      ]).flat();

    const config = {
      data,
      theme: theme === 'dark' ? 'dark' : 'light',
      isStack: true,
      xField: 'count',
      yField: 'username',
      seriesField: 'type',
      legend: { position: 'top-right' },
      color: ['#3b82f6', '#f59e0b'],
      label: {
        position: 'middle',
        layout: {
          type: 'adjust-color',
        },
      },
      animation: {
        appear: {
          animation: 'grow-in-x',
          duration: 1500,
          easing: 'ease-in-out',
        },
      },
      barBackground: {
        style: {
          fill: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
        },
      },
      interactions: [{ type: 'active-region' }],
    };

    return (
      <Card 
        title={<div><TeamOutlined className="icon-pulse" style={{marginRight: 8}} /> 团队工作负载</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          {data.length > 0 ? <Column {...config} /> : <Empty description="暂无团队数据" />}
        </div>
      </Card>
    );
  };

  // 渲染用户性能雷达图
  const renderPerformanceRadar = () => {
    if (!performance || performance.length === 0) return <Empty description="暂无数据" />;

    // 获取前5名用户
    const topUsers = [...performance]
      .sort((a, b) => b.quality_score - a.quality_score)
      .slice(0, 5);

    const radarData = topUsers.flatMap(user => [
      { username: user.username, category: '创建问题', value: user.total_issues_created },
      { username: user.username, category: '解决问题', value: user.resolved_issues },
      { username: user.username, category: '解决率', value: user.resolution_rate * 100 },
      { username: user.username, category: '活跃度', value: user.activity_count },
      { username: user.username, category: '质量分', value: user.quality_score * 10 },
    ]);

    const config = {
      data: radarData,
      theme: theme === 'dark' ? 'dark' : 'light',
      xField: 'category',
      yField: 'value',
      seriesField: 'username',
      meta: {
        value: {
          min: 0,
          nice: true,
        },
      },
      xAxis: {
        line: null,
        tickLine: null,
        grid: {
          line: {
            style: {
              lineDash: null,
            },
          },
        },
      },
      yAxis: {
        label: false,
        grid: {
          alternateColor: theme === 'dark' 
            ? 'rgba(255, 255, 255, 0.04)' 
            : 'rgba(0, 0, 0, 0.04)',
        },
      },
      point: {
        size: 3,
      },
      area: {
        style: {
          fillOpacity: 0.3,
        },
      },
      legend: {
        position: 'bottom',
      },
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 2000,
          easing: 'ease-in-out'
        }
      },
      color: ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6'],
    };

    return (
      <Card 
        title={<div><RadarChartOutlined className="icon-pulse" style={{marginRight: 8}} /> 用户表现雷达</div>}
        className="dashboard-card" 
        bordered={false}
      >
        <div className="chart-container" style={{height: 300}}>
          {radarData.length > 0 ? <Radar {...config} /> : <Empty description="暂无用户数据" />}
        </div>
      </Card>
    );
  };

  // 渲染统计卡片
  const renderStatisticCards = () => {
    if (!dashboardData) return null;

    const liquidConfig: any = {
      percent: resolutionRate,
      outline: {
        border: 4,
        distance: 8,
      },
      wave: {
        length: 128,
      },
      pattern: {
        type: 'line',
        cfg: {
          stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)',
        }
      },
      statistic: {
        title: {
          formatter: () => '解决率',
          style: {
            fontSize: '16px',
            fontWeight: 600,
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : undefined,
          },
        },
        content: {
          style: {
            fontSize: '20px',
            fontWeight: 700,
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : undefined,
          },
          formatter: () => `${(resolutionRate * 100).toFixed(1)}%`,
        },
      },
      liquidStyle: ({ percent }: { percent: number }) => {
        return {
          fill: percent > 0.7 
            ? 'l(270) 0:#10B981 1:#059669' 
            : percent > 0.4 
              ? 'l(270) 0:#F59E0B 1:#D97706'
              : 'l(270) 0:#EF4444 1:#DC2626',
          stroke: theme === 'dark' ? '#141414' : 'white',
          lineWidth: 3,
          shadowColor: percent > 0.7 
            ? 'rgba(16, 185, 129, 0.25)' 
            : percent > 0.4 
              ? 'rgba(245, 158, 11, 0.25)'
              : 'rgba(239, 68, 68, 0.25)',
          shadowBlur: 15,
          cursor: 'pointer'
        }
      },
      theme: theme === 'dark' ? 'dark' : 'light',
      animation: {
        appear: {
          animation: 'wave-in',
          duration: 2000,
        },
        update: {
          animation: 'wave-in',
          duration: 1000,
        }
      },
      shape: 'circle',
      waveLength: 128,
      radius: 0.8
    };

    const gaugeConfig: any = {
      percent: dashboardData?.avg_resolution_time ? Math.min(dashboardData.avg_resolution_time / 48, 1) : 0,
      range: {
        color: 'l(0) 0:#10B981 0.5:#F59E0B 1:#EF4444',
        width: 12,
      },
      indicator: {
        pointer: {
          style: {
            stroke: theme === 'dark' ? '#D0D0D0' : '#D0D0D0',
            lineWidth: 2,
            shadowColor: 'rgba(0, 0, 0, 0.25)',
            shadowBlur: 5,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
          },
        },
        pin: {
          style: {
            stroke: theme === 'dark' ? '#D0D0D0' : '#D0D0D0',
            r: 8,
            lineWidth: 3,
            fill: theme === 'dark' ? '#141414' : 'white',
            shadowColor: 'rgba(0, 0, 0, 0.25)',
            shadowBlur: 5,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
          },
        },
      },
      startAngle: Math.PI,
      endAngle: 2 * Math.PI,
      statistic: {
        title: {
          formatter: () => '平均解决时间',
          style: {
            fontSize: '16px',
            fontWeight: 600,
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : undefined,
          },
        },
        content: {
          style: {
            fontSize: '20px',
            fontWeight: 700,
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : undefined,
          },
          formatter: () => `${dashboardData?.avg_resolution_time?.toFixed(1) || 0}小时`,
        },
      },
      axis: {
        label: {
          formatter(v: any) {
            return Number(v) * 48 + 'h';
          },
          style: {
            fill: theme === 'dark' ? 'rgba(255, 255, 255, 0.65)' : undefined,
          },
        },
        tickLine: {
          style: {
            stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : undefined,
          },
        },
        subTickLine: {
          count: 4,
          length: 5,
          style: {
            stroke: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.15)',
          },
        },
      },
      theme: theme === 'dark' ? 'dark' : 'light',
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 2000,
        },
        update: {
          animation: 'fade-in',
          duration: 1000,
        }
      },
    };

    return (
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <Card className="dashboard-card" bordered={false}>
            <Statistic
              title={<span style={{ color: theme === 'dark' ? '#fff' : undefined }}>项目总数</span>}
              value={totalProjects}
              prefix={<ProjectOutlined style={{ fontSize: 24 }} />}
              valueStyle={{ color: '#1890ff' }}
              formatter={(value) => (
                <CountUp end={Number(value)} separator="," duration={2.5} />
              )}
            />
            <div className="stat-description">所有跟踪的项目数量</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="dashboard-card" bordered={false}>
            <Statistic
              title={<span style={{ color: theme === 'dark' ? '#fff' : undefined }}>问题总数</span>}
              value={totalIssues}
              prefix={<BugOutlined style={{ fontSize: 24 }} />}
              valueStyle={{ color: '#faad14' }}
              formatter={(value) => (
                <CountUp end={Number(value)} separator="," duration={2.5} />
              )}
            />
            <div className="stat-description">所有记录的问题数量</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="dashboard-card" bordered={false}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ height: '120px' }}>
                <Liquid {...liquidConfig} />
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="dashboard-card" bordered={false}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ height: '120px' }}>
                <Gauge {...gaugeConfig} />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染最近活动列表
  const renderActivities = () => {
    // 活动类型转中文文本
    const getActionLabel = (action: string) => {
      switch (action) {
        case 'create': return '创建了';
        case 'update': return '更新了';
        case 'comment': return '评论了';
        case 'resolve': return '解决了';
        case 'close': return '关闭了';
        case 'reopen': return '重新打开了';
        case 'assign': return '分配了';
        default: return '操作了';
      }
    };
    
    // 根据状态获取标签颜色
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'open': return 'blue';
        case 'in_progress': return 'orange';
        case 'resolved': return 'green';
        case 'verified': return 'cyan';
        case 'closed': return 'default';
        case 'reopened': return 'purple';
        case 'rejected': return 'red';
        default: return 'default';
      }
    };
    
    // 为用户名生成随机但一致的颜色
    const getRandomColor = (str: string) => {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      const colors = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#0ea5e9', '#f43f5e'];
      const index = Math.abs(hash) % colors.length;
      return colors[index];
    };
    
    return (
      <Card 
        title={<div><RocketOutlined className="icon-pulse" style={{marginRight: 8}} /> 最近活动</div>}
        className="dashboard-card" 
        bordered={false}
      >
        {activitiesLoading ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin />
          </div>
        ) : activities.length === 0 ? (
          <Empty description="暂无活动" />
        ) : (
      <List
            className="activity-list"
        itemLayout="horizontal"
        dataSource={activities}
            renderItem={(item: ActivityItem, index: number) => (
              <List.Item
                style={{ 
                  animationDelay: `${index * 0.1}s`,
                  animation: 'fadeInUp 0.5s backwards'
                }}
              >
            <List.Item.Meta
                  avatar={
                    <Avatar 
                      style={{ backgroundColor: getRandomColor(item.user_name) }}
                    >
                      {item.user_name.charAt(0).toUpperCase()}
                    </Avatar>
                  }
                  title={
                    <Space>
                      <span>{item.user_name}</span>
                      <span>{getActionLabel(item.action)}</span>
                      <a>{item.target_type === 'issue' ? '问题' : '评论'} #{item.target_id}</a>
            {item.status && (
                        <Tag color={getStatusColor(item.status)}>
                          {item.status === 'open' ? '待处理' :
                           item.status === 'in_progress' ? '处理中' :
                           item.status === 'resolved' ? '已解决' :
                           item.status === 'verified' ? '已验证' :
                           item.status === 'closed' ? '已关闭' :
                           item.status === 'reopened' ? '重新打开' : item.status}
              </Tag>
            )}
                    </Space>
                  }
                  description={formatDateTime(item.created_at)}
                />
          </List.Item>
        )}
      />
        )}
      </Card>
    );
  };

  const isLoading = Boolean(statsLoading) || Boolean(activitiesLoading) || Boolean(performanceLoading);

  // 显示模拟数据的提示条件
  const showMockAlert = useMockData && !statsLoading;

  return (
    <div className={`dashboard-container ${theme === 'dark' ? 'dark-theme' : 'light-theme'}`}>
      <PageHeader 
        title={
          <div style={{ display: 'flex', alignItems: 'center', animation: 'slideInDown 0.8s' }}>
            <BarChartOutlined style={{ marginRight: 12, fontSize: 24 }} className="icon-pulse" />
            <span>仪表盘数据分析</span>
          </div>
        } 
      />
      
      {showMockAlert && (
        <div style={{ marginBottom: 16 }}>
          <Alert 
            message="当前显示的是演示数据" 
            description="系统无法连接到实际数据源，正在展示模拟数据用于演示。" 
            type="info" 
            showIcon 
            closable
          />
        </div>
      )}
      
      <div className="dashboard-filters" style={{ animation: 'fadeInUp 0.8s' }}>
        <Space wrap>
          <RangePicker
            value={dateRange}
            onChange={handleDateRangeChange}
            allowClear={false}
            style={{ width: 280 }}
            placeholder={['开始日期', '结束日期']}
          />
          <Button 
            type="primary" 
            icon={<FilterOutlined />} 
            onClick={handleFilterClick}
          >
            筛选
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleResetFilters}
          >
            重置
          </Button>
          <Tooltip title="刷新所有数据">
            <Button 
              icon={<SyncOutlined spin={refreshing} />} 
              onClick={handleRefreshAll}
            >
              刷新
            </Button>
          </Tooltip>
          <Segmented
            options={[
              { label: '浅色', value: 'light', icon: <div>☀️</div> },
              { label: '深色', value: 'dark', icon: <div>🌙</div> },
            ]}
            value={theme}
            onChange={handleThemeChange as (value: SegmentedValue) => void}
          />
        </Space>
      </div>
      
      <Spin spinning={isLoading} tip="数据加载中...">
        <div className="dashboard-content">
          {/* 统计数据卡片 */}
          {renderStatisticCards()}
          
          {/* 图表和表格 */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            {renderStatusDistribution()}
          </Col>
          <Col xs={24} lg={12}>
            {renderTypeDistribution()}
          </Col>
          <Col xs={24} lg={12}>
            {renderTrendAnalysis()}
          </Col>
            <Col xs={24} lg={12}>
              {renderFixRateTrend()}
            </Col>
          <Col xs={24} lg={12}>
            {renderProjectDistribution()}
          </Col>
          <Col xs={24} lg={12}>
            {renderTeamWorkload()}
          </Col>
          <Col xs={24} lg={12}>
              {renderPerformanceRadar()}
            </Col>
            <Col xs={24}>
            {renderActivities()}
          </Col>
        </Row>
        </div>
      </Spin>
    </div>
  );
};

export default Dashboard; 