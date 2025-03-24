import React from 'react';
import { Table as AntTable } from 'antd';
import type { TableProps } from 'antd';

// 定义我们自己的Table组件，使用JavaScript默认参数代替defaultProps
export function Table<RecordType extends object = any>({
  size = 'middle',
  bordered = false,
  loading = false,
  showHeader = true,
  ...restProps
}: TableProps<RecordType>) {
  return (
    <AntTable<RecordType>
      size={size}
      bordered={bordered}
      loading={loading}
      showHeader={showHeader}
      {...restProps}
    />
  );
}

export default Table; 