#!/usr/bin/env python3
"""
漏洞扫描看板 - 数据收集脚本
从 Strix/Nikto/Nmap 进程收集扫描状态
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 配置路径
TARGETS_FILE = "/tmp/vuln_targets.json"
OUTPUT_FILE = "/tmp/vuln_dashboard_data.json"
SCAN_PROC_DIR = "/tmp/vuln_scans"

# 工具列表
SCAN_TOOLS = ["Strix", "Nikto", "Nmap"]


def load_targets():
    """从文件加载目标列表"""
    if not os.path.exists(TARGETS_FILE):
        # 如果文件不存在，返回空列表
        return []
    
    try:
        with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('projects', [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading targets: {e}")
        return []


def get_process_status(tool_name, target_name):
    """获取指定工具对指定目标的扫描状态"""
    # 尝试从进程信息文件中读取
    proc_file = os.path.join(SCAN_PROC_DIR, f"{target_name}_{tool_name}.json")
    
    if os.path.exists(proc_file):
        try:
            with open(proc_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # 尝试通过 ps 命令查找进程
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"{tool_name}.*{target_name}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {
                "status": "scanning",
                "progress": 50,
                "scanned": 0,
                "found": 0
            }
    except Exception:
        pass
    
    # 返回默认状态
    return {
        "status": "pending",
        "progress": 0,
        "scanned": 0,
        "found": 0
    }


def get_tool_data(tool_name, target_name):
    """获取特定工具的扫描数据"""
    base_data = {
        "name": tool_name,
        "status": "pending",
        "progress": 0,
        "scanned": 0,
        "found": 0
    }
    
    if tool_name == "Strix":
        # Strix API 扫描器 - 收集端点信息
        proc_file = os.path.join(SCAN_PROC_DIR, f"{target_name}_strix.json")
        if os.path.exists(proc_file):
            try:
                with open(proc_file, 'r') as f:
                    data = json.load(f)
                    base_data.update({
                        "status": data.get("status", "pending"),
                        "progress": data.get("progress", 0),
                        "scanned": data.get("endpoints_scanned", 0),
                        "found": data.get("endpoints_found", 0),
                        "endpoints": data.get("discovered_endpoints", [])
                    })
            except Exception:
                pass
        
        # 额外尝试从日志获取
        log_file = f"/tmp/vuln_scan_{target_name}_strix.log"
        if os.path.exists(log_file):
            base_data["status"] = "scanning"
            base_data["progress"] = 60
    
    elif tool_name == "Nikto":
        # Nikto Web 漏洞扫描
        proc_file = os.path.join(SCAN_PROC_DIR, f"{target_name}_nikto.json")
        if os.path.exists(proc_file):
            try:
                with open(proc_file, 'r') as f:
                    data = json.load(f)
                    base_data.update({
                        "status": data.get("status", "pending"),
                        "progress": data.get("progress", 0),
                        "scanned": data.get("items_scanned", 0),
                        "found": data.get("vulns_found", 0),
                        "vulns": data.get("vulnerabilities", [])
                    })
            except Exception:
                pass
    
    elif tool_name == "Nmap":
        # Nmap 端口扫描
        proc_file = os.path.join(SCAN_PROC_DIR, f"{target_name}_nmap.json")
        if os.path.exists(proc_file):
            try:
                with open(proc_file, 'r') as f:
                    data = json.load(f)
                    base_data.update({
                        "status": data.get("status", "pending"),
                        "progress": data.get("progress", 0),
                        "scanned": data.get("ports_scanned", 0),
                        "found": data.get("open_ports", 0),
                        "ports": data.get("open_ports_list", [])
                    })
            except Exception:
                pass
    
    return base_data


def calculate_project_progress(targets):
    """计算项目整体进度"""
    if not targets:
        return 0
    
    total_progress = 0
    for target in targets:
        tool_progress = 0
        for tool in target.get("tools", []):
            tool_progress += tool.get("progress", 0)
        if target.get("tools"):
            tool_progress /= len(target["tools"])
        total_progress += tool_progress
    
    return int(total_progress / len(targets)) if targets else 0


def get_project_status(targets):
    """判断项目状态"""
    if not targets:
        return "pending"
    
    all_completed = True
    has_scanning = False
    
    for target in targets:
        for tool in target.get("tools", []):
            status = tool.get("status", "pending")
            if status == "scanning":
                has_scanning = True
            elif status != "completed":
                all_completed = False
    
    if has_scanning:
        return "scanning"
    elif all_completed:
        return "completed"
    else:
        return "pending"


def collect_data():
    """主数据收集函数"""
    # 确保输出目录存在
    os.makedirs(SCAN_PROC_DIR, exist_ok=True)
    
    # 加载项目列表
    project_configs = load_targets()
    
    if not project_configs:
        # 如果没有配置，生成示例数据
        project_configs = [
            {"name": "Tripadvisor", "targets": ["www.tripadvisor.com"]},
            {"name": "Example Site", "targets": ["www.example.com"]}
        ]
    
    projects = []
    
    for proj in project_configs:
        project_name = proj.get("name", "Unknown")
        target_urls = proj.get("targets", [])
        
        targets = []
        for url in target_urls:
            # 为每个目标收集各工具的数据
            tools = []
            for tool_name in SCAN_TOOLS:
                tool_data = get_tool_data(tool_name, url)
                tools.append(tool_data)
            
            target_entry = {
                "name": url,
                "tools": tools
            }
            targets.append(target_entry)
        
        # 计算项目进度和状态
        progress = calculate_project_progress(targets)
        status = get_project_status(targets)
        
        project_entry = {
            "name": project_name,
            "status": status,
            "progress": progress,
            "targets": targets,
            "last_updated": datetime.now().isoformat()
        }
        projects.append(project_entry)
    
    # 构建最终数据结构
    dashboard_data = {
        "projects": projects,
        "last_updated": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # 写入输出文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    print(f"Data collected at {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Projects: {len(projects)}")
    
    return dashboard_data


def simulate_scan_data():
    """生成模拟扫描数据（用于测试）"""
    # 确保目录存在
    os.makedirs(SCAN_PROC_DIR, exist_ok=True)
    
    # 模拟 Strix 扫描数据
    strix_data = {
        "status": "scanning",
        "progress": 50,
        "endpoints_scanned": 2100,
        "endpoints_found": 5,
        "discovered_endpoints": ["/api/", "/hotels", "/flights", "/reviews", "/search"]
    }
    with open(os.path.join(SCAN_PROC_DIR, "www.tripadvisor.com_strix.json"), 'w') as f:
        json.dump(strix_data, f)
    
    # 模拟 Nikto 扫描数据
    nikto_data = {
        "status": "scanning",
        "progress": 40,
        "items_scanned": 45,
        "vulns_found": 2,
        "vulnerabilities": ["X-Frame-Options missing", "Server-Leaks-Information via X-Powered-By"]
    }
    with open(os.path.join(SCAN_PROC_DIR, "www.tripadvisor.com_nikto.json"), 'w') as f:
        json.dump(nikto_data, f)
    
    # 模拟 Nmap 扫描数据
    nmap_data = {
        "status": "completed",
        "progress": 100,
        "ports_scanned": 1000,
        "open_ports": 5,
        "open_ports_list": [80, 443, 8080, 8443, 22]
    }
    with open(os.path.join(SCAN_PROC_DIR, "www.tripadvisor.com_nmap.json"), 'w') as f:
        json.dump(nmap_data, f)
    
    # 创建目标文件
    targets_data = {
        "projects": [
            {"name": "Tripadvisor", "targets": ["www.tripadvisor.com"]}
        ]
    }
    with open(TARGETS_FILE, 'w') as f:
        json.dump(targets_data, f)
    
    print("Simulated scan data created")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simulate":
        # 生成模拟数据用于测试
        simulate_scan_data()
    
    # 执行数据收集
    collect_data()
