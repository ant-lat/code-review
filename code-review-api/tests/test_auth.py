"""
测试认证功能
@author: pgao
@date: 2024-03-16
"""
import os
import sys
import requests
import json
from typing import Dict, Any, Optional

# 设置API基础URL
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    测试登录接口
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        Dict[str, Any]: 包含token的响应，如果失败则为None
    """
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": username,
        "password": password,
        "remember_me": False
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("登录成功！")
            print("只返回了Token信息:")
            print(json.dumps(result["data"], indent=2))
            return result["data"]
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None


def get_current_user(access_token: str) -> None:
    """
    测试获取当前用户信息接口
    
    Args:
        access_token: 访问令牌
    """
    url = f"{BASE_URL}/api/v1/auth/get_current_user"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"获取用户信息响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("获取用户信息成功！")
            print("用户信息:")
            print(json.dumps(result["data"], indent=2))
        else:
            print(f"获取用户信息失败: {response.text}")
    except Exception as e:
        print(f"请求异常: {str(e)}")


def refresh_token(refresh_token_str: str) -> Optional[Dict[str, Any]]:
    """
    测试刷新令牌接口
    
    Args:
        refresh_token_str: 刷新令牌
        
    Returns:
        Dict[str, Any]: 包含新token的响应，如果失败则为None
    """
    url = f"{BASE_URL}/api/v1/auth/refresh-token"
    data = {
        "refresh_token": refresh_token_str
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"刷新令牌响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("刷新令牌成功！")
            print("新的Token信息:")
            print(json.dumps(result["data"], indent=2))
            return result["data"]
        else:
            print(f"刷新令牌失败: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None


def main():
    """主测试流程"""
    print("=== 开始测试认证流程 ===")
    
    # 1. 测试登录
    username = input("请输入用户名: ") or "admin"
    password = input("请输入密码: ") or "admin123"
    
    print(f"\n1. 测试登录接口 - 用户名: {username}")
    token_info = login(username, password)
    
    if not token_info:
        print("登录测试失败，退出测试")
        return
    
    # 2. 使用获得的token测试获取用户信息
    print("\n2. 测试获取用户信息接口")
    get_current_user(token_info["access_token"])
    
    # 3. 测试刷新令牌
    print("\n3. 测试刷新令牌接口")
    new_token_info = refresh_token(token_info["refresh_token"])
    
    if new_token_info:
        # 4. 使用刷新后的token再次获取用户信息
        print("\n4. 使用刷新后的token测试获取用户信息接口")
        get_current_user(new_token_info["access_token"])
    
    print("\n=== 认证流程测试完成 ===")


if __name__ == "__main__":
    main() 