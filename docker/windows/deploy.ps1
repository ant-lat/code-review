# 进入docker目录
cd $PSScriptRoot\..

# 检查docker-compose是否存在
$dockerComposeExists = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerComposeExists) {
    Write-Host "错误：未找到docker-compose命令" -ForegroundColor Red
    Write-Host "请安装docker-compose后再尝试部署" -ForegroundColor Red
    exit 1
}

# 停止并移除现有容器
Write-Host "停止现有容器..." -ForegroundColor Yellow
docker-compose down

# 启动新容器
Write-Host "启动新容器..." -ForegroundColor Green
docker-compose up -d

# 检查容器状态
Write-Host "检查容器状态..." -ForegroundColor Cyan
docker-compose ps

Write-Host "部署完成！" -ForegroundColor Green
Write-Host "前端应用可通过 http://localhost 访问" -ForegroundColor Cyan
Write-Host "后端API可通过 http://localhost/api 访问" -ForegroundColor Cyan 