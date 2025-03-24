declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}

declare module '*.less';

declare module 'antd/dist/reset.css'; 