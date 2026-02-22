# 🛡️ 漏洞扫描监控看板

实时监控漏洞扫描进度的可视化看板。

## 功能

- 📊 实时显示扫描进程数 (Strix/Nikto/Nmap)
- 📋 目标列表管理
- 🔍 筛选功能 (全部/扫描中/已完成/等待中)
- 📄 分页导航
- 🔄 自动刷新

## 使用方法

1. 启动本地服务器:
```bash
python3 -m http.server 8888
```

2. 浏览器访问:
```
http://localhost:8888/vuln_scan_dashboard.html
```

## 技术栈

- HTML5
- CSS3 (自定义样式)
- JavaScript (原生)

## 截图

![Dashboard](screenshot.png)

## License

MIT
