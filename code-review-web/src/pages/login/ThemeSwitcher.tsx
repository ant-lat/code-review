import React from 'react';
import { Radio, Tooltip } from 'antd';
import {
  BulbOutlined,
  CodeOutlined,
  HeatMapOutlined,
  BgColorsOutlined,
  BorderOutlined,
} from '@ant-design/icons';
import './ThemeSwitcher.css';

// 定义可用的登录主题类型
export type LoginTheme = 'tech' | 'dark' | 'light' | 'gradient' | 'minimal';

// 组件属性接口
interface ThemeSwitcherProps {
  currentTheme: LoginTheme;
  onChange: (theme: LoginTheme) => void;
}

/**
 * 登录主题切换组件
 */
const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({
  currentTheme,
  onChange,
}) => {
  const themes: { value: LoginTheme; icon: React.ReactNode; tooltip: string }[] = [
    { value: 'tech', icon: <CodeOutlined />, tooltip: '科技风格' },
    { value: 'dark', icon: <HeatMapOutlined />, tooltip: '暗色主题' },
    { value: 'light', icon: <BulbOutlined />, tooltip: '明亮主题' },
    { value: 'gradient', icon: <BgColorsOutlined />, tooltip: '渐变效果' },
    { value: 'minimal', icon: <BorderOutlined />, tooltip: '极简设计' },
  ];

  return (
    <div className="theme-switcher">
      <div className="theme-radio-group">
        {themes.map((theme) => (
          <Tooltip key={theme.value} title={theme.tooltip} placement="bottom">
            <div 
              className={`theme-radio-button ${currentTheme === theme.value ? 'active' : ''}`}
              onClick={() => onChange(theme.value)}
            >
              <div className="theme-icon-wrapper">
                {theme.icon}
                <div className={`theme-preview ${theme.value}`}></div>
              </div>
            </div>
          </Tooltip>
        ))}
      </div>
    </div>
  );
};

export default ThemeSwitcher; 