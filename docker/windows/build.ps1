# 进入docker目录
cd $PSScriptRoot\..

Write-Host "构建前端Docker镜像..." -ForegroundColor Green
docker build -t code-review-web:latest -f frontend/Dockerfile ../code-review-web

Write-Host "前端Docker镜像构建完成！" -ForegroundColor Green

# 如果后端项目存在则构建后端镜像
if (Test-Path -Path "../code-review-api") {
    Write-Host "构建后端Docker镜像..." -ForegroundColor Green
    docker build -t code-review-api:latest -f backend/Dockerfile ../code-review-api
    Write-Host "后端Docker镜像构建完成！" -ForegroundColor Green
}

Write-Host "所有Docker镜像构建完成！" -ForegroundColor Green 