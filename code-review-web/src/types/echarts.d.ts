declare module 'echarts-for-react' {
  import { Component } from 'react';
  import { EChartsOption } from 'echarts';

  interface EChartsReactProps {
    option: EChartsOption;
    notMerge?: boolean;
    lazyUpdate?: boolean;
    style?: React.CSSProperties;
    className?: string;
    theme?: string | object;
    onChartReady?: (instance: any) => void;
    onEvents?: Record<string, Function>;
    opts?: {
      devicePixelRatio?: number;
      renderer?: 'canvas' | 'svg';
      width?: number | string | 'auto';
      height?: number | string | 'auto';
    };
  }

  export default class ReactECharts extends Component<EChartsReactProps> {}
} 