# 代码审查系统 - IntelliJ IDEA插件

<div align="center">

![Kotlin](https://img.shields.io/badge/Kotlin-1.8+-blue)
![IntelliJ Platform](https://img.shields.io/badge/IntelliJ%20Platform-2022.3+-orange)
![JVM](https://img.shields.io/badge/JVM-17+-green)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

## 插件概述

代码审查系统IntelliJ IDEA插件是基于IntelliJ平台SDK开发的IDE扩展工具，让开发人员能在IDE中完成代码审核工作，无需切换到Web界面。通过此插件，开发人员可以直接在代码编辑器中查看、创建和回复代码审核评论，大幅提高团队协作效率。

### 主要功能

- **IDE内代码审核**：直接在IntelliJ IDEA中执行代码审核流程
- **行内评论**：为特定代码行添加评论和建议
- **代码对比**：简单直观的代码差异比较
- **审核状态跟踪**：实时查看代码审核状态
- **评论分类**：按严重程度和类型分类评论
- **离线工作**：支持离线撰写评论，稍后同步
- **通知提醒**：接收新评论和状态变更通知
- **一键修复**：支持直接应用评论中的修改建议
- **多文件支持**：支持审核涉及多个文件的变更

## 兼容性

- 支持IntelliJ Platform 2022.3及以上版本
- 适用于所有基于IntelliJ平台的IDE:
  - IntelliJ IDEA
  - WebStorm
  - PyCharm
  - PhpStorm
  - Android Studio
  - GoLand
  - CLion等

## 技术栈

- **开发语言**: Kotlin 1.8+
- **UI框架**: IntelliJ Platform UI组件
- **网络通信**: OkHttp + Retrofit
- **JSON处理**: Gson / Kotlinx Serialization
- **异步处理**: Kotlin协程
- **构建工具**: Gradle + IntelliJ Platform Plugin

## 项目结构

```
code-r-plugin/
├── build.gradle.kts        # Gradle构建配置
├── gradle/                 # Gradle包装器
├── src/
│   ├── main/
│   │   ├── kotlin/         # Kotlin源代码
│   │   │   ├── actions/    # 插件动作定义
│   │   │   ├── api/        # API通信
│   │   │   ├── config/     # 插件配置
│   │   │   ├── listeners/  # 事件监听器
│   │   │   ├── models/     # 数据模型
│   │   │   ├── services/   # 服务实现
│   │   │   ├── toolwindow/ # 工具窗口
│   │   │   ├── ui/         # UI组件
│   │   │   └── utils/      # 工具类
│   │   ├── resources/      # 资源文件
│   │   │   ├── META-INF/   # 插件注册
│   │   │   └── icons/      # 图标资源
│   │   └── java/           # Java源代码(如需)
│   └── test/               # 测试代码
├── gradle.properties       # Gradle属性
└── plugin.xml              # IntelliJ插件描述
```

## 安装指南

### 从JetBrains插件仓库安装

1. 打开IntelliJ IDEA (或其他JetBrains IDE)
2. 转到 `File` -> `Settings` -> `Plugins`
3. 点击 `Marketplace` 选项卡
4. 搜索 "Code Review Plugin"
5. 点击 `Install` 按钮
6. 重启IDE完成安装

### 手动安装

1. 下载最新的插件发布版本 (.zip或.jar文件)
2. 打开IntelliJ IDEA
3. 转到 `File` -> `Settings` -> `Plugins`
4. 点击齿轮图标，选择 `Install Plugin from Disk...`
5. 选择下载的插件文件
6. 重启IDE完成安装

## 配置指南

### 连接到代码审查服务器

1. 安装插件后，打开IDE设置 (`File` -> `Settings`)
2. 找到 `Tools` -> `Code Review Plugin` 部分
3. 输入以下信息:
   - 服务器URL: 代码审查系统API的基础URL (例如 `http://your-server:8000/api`)
   - 用户名: 您的代码审查系统用户名
   - 密码或API令牌: 您的认证凭据
4. 点击 `Test Connection` 验证连接
5. 点击 `Apply` 保存设置

### 配置提醒和通知

1. 在插件设置页面
2. 找到 `Notifications` 部分
3. 配置提醒频率和通知类型
4. 选择何时接收通知 (新评论、状态变更等)
5. 点击 `Apply` 保存设置

## 使用指南

### 创建代码审核

1. 右键点击项目视图中的文件
2. 选择 `Code Review` -> `Create Review`
3. 输入审核标题和描述
4. 选择要包含的文件
5. 指定审核人员
6. 点击 `Create` 提交审核请求

### 添加行内评论

1. 在编辑器中打开需要评审的文件
2. 在相关代码行上点击行号左侧的小图标 (或右键点击行并选择 `Add Comment`)
3. 在弹出的对话框中输入评论
4. 选择评论类型 (建议、问题、错误等)
5. 点击 `Post` 发布评论

### 回复评论

1. 点击评论旁边的 `Reply` 按钮
2. 输入回复内容
3. 点击 `Post` 发布回复

### 解决问题

1. 当您完成对评论的处理后
2. 点击评论旁边的 `Resolve` 按钮
3. 可选择添加解决说明
4. 点击 `Resolve` 完成

### 工具窗口

插件提供了专门的工具窗口，可通过以下方式访问:

1. 点击IDE右侧的 `Code Review` 工具窗口按钮
2. 或通过 `View` -> `Tool Windows` -> `Code Review` 菜单

工具窗口提供:
- 当前项目的所有代码审核列表
- 未处理的评论概览
- 审核状态统计

## 开发环境设置

### 前置条件

- IntelliJ IDEA Ultimate或Community (版本2022.3+)
- JDK 17或更高版本
- Kotlin插件 (已包含在IDEA中)
- Gradle 7.6或更高版本

### 设置步骤

1. 克隆仓库:
   ```bash
   git clone [仓库地址]
   cd code-r-plugin
   ```

2. 使用IntelliJ IDEA打开项目
   - 打开IDEA
   - 选择 `File` -> `Open` 
   - 导航到仓库目录并打开

3. Gradle同步
   - 当项目首次打开时，IDEA会自动同步Gradle设置
   - 如果没有自动同步，可以点击工具栏中的 `Sync` 按钮

### 运行和调试

1. 创建运行配置:
   - 在IDEA中，导航到 `Run` -> `Edit Configurations`
   - 点击 `+` 按钮并选择 `Gradle`
   - 设置以下参数:
     - Gradle project: 选择当前项目
     - Tasks: `runIde`
   - 点击 `Apply` 然后 `OK`

2. 运行插件:
   - 从工具栏选择刚创建的运行配置
   - 点击 `Run` 按钮
   - 这将启动一个包含该插件的IDE实例

3. 调试插件:
   - 在代码中设置断点
   - 点击 `Debug` 按钮而不是 `Run`
   - 调试会话将会启动，允许你检查变量和程序流程

## 构建和部署

### 构建插件

```bash
./gradlew buildPlugin
```

构建后的插件将位于 `build/distributions/` 目录

### 发布到JetBrains插件仓库

1. 获取JetBrains插件仓库的API令牌
2. 配置Gradle属性:
   ```
   intellijPublishToken=your-token-here
   ```

3. 使用Gradle任务发布:
   ```bash
   ./gradlew publishPlugin
   ```

### 创建发布版本

1. 更新版本号:
   - 在 `build.gradle.kts` 中更新 `version` 属性
   - 更新 `plugin.xml` 中的版本信息

2. 构建发布版本:
   ```bash
   ./gradlew buildPlugin
   ```

3. 测试发布版本:
   ```bash
   ./gradlew runPluginVerifier
   ```

## 故障排除

### 连接服务器问题

**问题**: 插件无法连接到代码审查服务器

**解决方案**:
1. 检查服务器URL配置是否正确
2. 确认API服务器是否运行
3. 验证防火墙设置
4. 检查IDE代理设置
5. 启用插件日志查看详细错误信息:
   - 帮助 -> 诊断工具 -> 调试日志设置
   - 添加 `#com.coder.codereview`

### 中文显示问题

**问题**: 中文字符显示为乱码

**解决方案**:
1. 确认IDE使用UTF-8编码:
   - 文件 -> 设置 -> 编辑器 -> 文件编码
   - 将全局编码和项目编码设置为UTF-8
2. 检查插件请求头和响应处理:
   - 确保HTTP请求头包含正确的Content-Type和charset
   - 在插件设置中启用"强制UTF-8编码"选项

### 插件冲突

**问题**: 插件与其他插件冲突

**解决方案**:
1. 更新到最新版本
2. 禁用可能冲突的插件，然后逐个启用以确定冲突源
3. 清理IDE缓存:
   - 文件 -> 失效缓存和重启

## 贡献和开发

### 报告问题

如果您发现任何Bug或希望请求新功能，请在项目的Issue跟踪器中创建新Issue。

### Pull Requests

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 编码标准

- 遵循Kotlin官方编码规范
- 使用有意义的变量和函数名
- 为公共API添加文档注释
- 包含适当的单元测试

## 许可证

本项目采用MIT许可证，详见LICENSE文件。 