# 贡献指南

感谢您考虑为代码审查系统做出贡献！本文档将指导您如何参与项目开发，从提交问题到贡献代码。

## 目录

- [行为准则](#行为准则)
- [如何参与贡献](#如何参与贡献)
- [开发流程](#开发流程)
- [提交Pull Request](#提交pull-request)
- [代码规范](#代码规范)
- [文档贡献](#文档贡献)
- [版本管理](#版本管理)
- [联系方式](#联系方式)

## 行为准则

本项目采用贡献者公约（Contributor Covenant）作为行为准则。我们希望所有贡献者都能创造一个积极、包容的环境。所有参与者都应该遵循以下原则：

- 使用友好、包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

## 如何参与贡献

### 贡献类型

您可以通过多种方式为项目做出贡献：

1. **报告Bug**：如果您发现Bug，请检查问题列表确认是否已被报告，然后创建一个新issue
2. **建议新功能**：如果您有好的想法，欢迎提交功能建议
3. **改进文档**：修正错别字、补充说明、添加示例等
4. **提交代码**：修复Bug或实现新功能
5. **代码审查**：参与审查其他贡献者的PR
6. **回答问题**：在issue中帮助其他用户解决问题

### 提交Issue

在创建新issue前，请先搜索现有issue，避免重复。创建issue时，请提供详细信息：

- **Bug报告**：描述Bug、复现步骤、预期结果、实际结果、环境信息等
- **功能建议**：描述功能、使用场景、为何需要此功能等

## 开发流程

### 环境设置

1. Fork项目仓库
2. 克隆您的Fork到本地
   ```bash
   git clone https://github.com/您的用户名/code-review.git
   cd code-review
   ```
3. 添加上游仓库
   ```bash
   git remote add upstream https://github.com/原作者/code-review.git
   ```
4. 创建新分支
   ```bash
   git checkout -b feature/your-feature-name
   # 或者
   git checkout -b fix/bug-description
   ```

### 开发建议

1. **保持分支同步**：经常从上游仓库拉取更新
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **小步提交**：提交小而有针对性的变更，便于审查和合并

3. **编写测试**：为新功能或Bug修复添加测试

4. **本地测试**：提交前确保所有测试通过且不引入新问题

## 提交Pull Request

1. **更新您的分支**：确保与主仓库同步
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **推送到您的仓库**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **创建Pull Request**：访问GitHub仓库页面，点击"New pull request"

4. **填写PR信息**：
   - 标题简明扼要地描述变更
   - 在描述中解释变更的目的和实现方式
   - 关联相关issue（如适用）
   - 添加任何需要审查者特别注意的事项

5. **持续跟进**：回应审查意见，根据需要更新PR

6. **PR合并后**：删除特性分支
   ```bash
   git branch -d feature/your-feature-name
   ```

## 代码规范

### 通用规范

- 遵循[DRY(Don't Repeat Yourself)](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)原则
- 代码应该自我解释，必要时添加注释
- 保持代码简洁明了
- 添加适当的日志记录

### 后端API (Python)

- 遵循[PEP 8](https://www.python.org/dev/peps/pep-0008/)风格指南
- 使用[Black](https://github.com/psf/black)格式化代码
- 使用类型注解
- 编写单元测试，保持测试覆盖率
- 遵循RESTful API设计原则

示例：
```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, q: Optional[str] = None):
    """
    获取单个项目的详细信息。
    
    参数:
        item_id: 项目ID
        q: 可选查询参数
    """
    item = get_item_from_db(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### 前端Web (TypeScript/React)

- 使用[ESLint](https://eslint.org/)和[Prettier](https://prettier.io/)
- 遵循函数式组件和Hooks模式
- 适当拆分组件，保持单一职责原则
- 使用TypeScript类型

示例：
```tsx
import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { fetchItems } from '../store/actions';

interface Item {
  id: number;
  name: string;
}

interface ItemListProps {
  projectId: number;
}

export const ItemList: React.FC<ItemListProps> = ({ projectId }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();
  
  useEffect(() => {
    const loadItems = async () => {
      try {
        const result = await dispatch(fetchItems(projectId));
        setItems(result);
      } finally {
        setLoading(false);
      }
    };
    
    loadItems();
  }, [projectId, dispatch]);
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
};
```

### IntelliJ IDEA插件 (Kotlin)

- 遵循[Kotlin编码约定](https://kotlinlang.org/docs/reference/coding-conventions.html)
- 使用扩展函数简化代码
- 适当使用空安全特性

示例：
```kotlin
class MyAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        ApplicationManager.getApplication().runWriteAction {
            // 执行操作
        }
    }
    
    override fun update(e: AnActionEvent) {
        // 更新操作状态
        val project = e.project
        e.presentation.isEnabled = project != null
    }
}
```

## 文档贡献

文档同样重要！以下是贡献文档的一些建议：

- 确保文档清晰、准确，适合目标读者
- 添加代码示例和截图，帮助理解
- 修正任何错误或过时的内容
- 遵循Markdown语法规范

### README文件

项目中的README文件应包含：

- 项目概述
- 安装/部署步骤
- 使用说明
- 开发指南
- 许可证信息

### API文档

- 使用明确的术语描述API端点
- 包含请求/响应示例
- 说明参数类型和限制
- 列出可能的错误代码和处理方法

## 版本管理

本项目使用[语义化版本控制](https://semver.org/)：

- **主版本号**：不兼容的API变更
- **次版本号**：向后兼容的功能添加
- **修订号**：向后兼容的问题修复

### 分支管理

- `main`：主分支，包含稳定版本
- `dev`：开发分支，包含下一版本的开发内容
- `feature/*`：特性分支，用于开发新功能
- `fix/*`：修复分支，用于修复Bug
- `release/*`：发布分支，用于版本发布准备

### 提交信息规范

我们使用[约定式提交](https://www.conventionalcommits.org/)规范：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

类型包括：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档变更
- `style`: 不影响代码含义的变更（如格式化）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变更

示例：
```
feat(auth): 添加用户角色管理功能

实现了基于角色的权限控制系统，包括：
- 角色创建和管理
- 为用户分配角色
- 基于角色检查权限

closes #123
```

## 联系方式

如有任何问题，请通过以下方式联系我们：

- GitHub Issue
- 邮件：support@example.com
- 开发者社区：[社区链接]

感谢您的贡献，我们期待与您共同改进代码审查系统！ 