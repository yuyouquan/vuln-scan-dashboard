#!/usr/bin/env python3
"""
漏洞扫描看板 - 修复版
从实际数据文件读取，支持实时更新
"""

import json
import subprocess
import os
from datetime import datetime

def get_scan_status():
    """获取扫描进程状态"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        strix = result.stdout.count("strix")
        nikto = result.stdout.count("nikto")
        nmap = result.stdout.count("nmap")
        return {"strix": strix, "nikto": nikto, "nmap": nmap, "total": strix+nikto+nmap}
    except:
        return {"strix": 0, "nikto": 0, "nmap": 0, "total": 0}

def load_projects():
    """从数据文件加载项目"""
    data_file = "/tmp/vuln_dashboard_data.json"
    
    # 如果文件不存在或为空，创建默认数据
    if not os.path.exists(data_file):
        return get_default_data()
    
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
            if data.get("projects"):
                return data
    except:
        pass
    
    return get_default_data()

def get_default_data():
    """生成默认数据 - 从目标文件或生成模拟数据"""
    targets_file = "/tmp/vuln_targets.json"
    
    projects = []
    
    # 尝试从目标文件加载
    if os.path.exists(targets_file):
        try:
            with open(targets_file, "r") as f:
                targets = json.load(f)
                if isinstance(targets, list) and len(targets) > 0:
                    for t in targets[:20]:  # 最多20个
                        name = t.get('name', t.get('url', 'Unknown'))
                        projects.append({
                            "name": name,
                            "status": "scanning" if os.random.random() > 0.3 else "waiting",
                            "progress": 0,
                            "targets": [{
                                "name": f"www.{name.lower()}.com" if '.' not in name else name,
                                "tools": [
                                    {"name": "Strix", "status": "scanning", "progress": 0, "scanned": 0, "found": 0, "endpoints": []},
                                    {"name": "Nikto", "status": "waiting", "progress": 0, "scanned": 0, "found": 0, "vulns": []},
                                    {"name": "Nmap", "status": "waiting", "progress": 0, "scanned": 0, "found": 0, "ports": []}
                                ]
                            }]
                        })
        except:
            pass
    
    # 如果没有数据，生成默认项目列表
    if not projects:
        default_names = [
            "Tripadvisor", "Under Armour", "Zendesk", "The Fork", "Anytask",
            "UltraMobile", "Entain", "Glean", "Sophos", "OpenAI",
            "Pinterest", "T-Mobile", "LastPass", "SoundCloud", "Linktree"
        ]
        for name in default_names:
            projects.append({
                "name": name,
                "status": "scanning",
                "progress": 45,
                "targets": [{
                    "name": f"www.{name.lower().replace(' ', '')}.com",
                    "tools": [
                        {"name": "Strix", "status": "scanning", "progress": 50, "scanned": 1200, "found": 3, "endpoints": ["/api/", "/login", "/products"]},
                        {"name": "Nikto", "status": "scanning", "progress": 40, "scanned": 89, "found": 1, "vulns": ["Apache negotiation"]},
                        {"name": "Nmap", "status": "waiting", "progress": 0, "scanned": 0, "found": 0, "ports": []}
                    ]
                }]
            })
    
    return {"projects": projects}

def generate_dashboard():
    status = get_scan_status()
    data = load_projects()
    projects = data.get("projects", [])
    total = len(projects)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 生成项目数据JSON
    projects_json = json.dumps(projects, ensure_ascii=False)
    
    # 生成卡片HTML数据
    cards_data = []
    for i, p in enumerate(projects):
        status_text = {"scanning": "扫描中", "done": "已完成", "waiting": "等待中", "completed": "已完成"}.get(p.get("status", ""), "未知")
        cards_data.append({
            "index": i,
            "name": p.get("name", "Unknown"),
            "status": p.get("status", "waiting"),
            "progress": p.get("progress", 0),
            "statusText": status_text,
            "targetCount": len(p.get("targets", []))
        })
    
    cards_json = json.dumps(cards_data, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>🛡️ 漏洞扫描看板</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }}
        
        .header {{ background: linear-gradient(180deg, #161b22 0%, #0d1117 100%); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ color: #58a9ff; font-size: 22px; font-weight: 600; }}
        .header .time {{ color: #8b949e; font-size: 13px; }}
        
        .toolbar {{ padding: 15px 30px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
        .search-box {{ display: flex; align-items: center; gap: 10px; }}
        .search-box input {{ background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 8px 12px; color: #c9d1d9; font-size: 13px; width: 200px; }}
        .search-box input:focus {{ outline: none; border-color: #58a9ff; }}
        .filter-btns {{ display: flex; gap: 8px; }}
        .filter-btn {{ padding: 6px 14px; background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 12px; cursor: pointer; transition: all 0.2s; }}
        .filter-btn:hover, .filter-btn.active {{ background: #238636; border-color: #3fb950; color: #fff; }}
        
        .stats-bar {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: #30363d; }}
        .stat {{ background: #161b22; padding: 15px 20px; text-align: center; }}
        .stat-value {{ font-size: 28px; font-weight: 700; color: #58a9ff; }}
        .stat-label {{ font-size: 11px; margin-top: 4px; color: #8b949e; text-transform: uppercase; }}
        
        .pagination-bar {{ padding: 15px 30px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }}
        .page-info {{ color: #8b949e; font-size: 13px; }}
        .page-size select {{ background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 6px 10px; color: #c9d1d9; font-size: 12px; cursor: pointer; }}
        
        .targets-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; padding: 24px; }}
        
        .target-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; overflow: hidden; transition: all 0.25s; cursor: pointer; }}
        .target-card:hover {{ border-color: #58a9ff; transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.4); }}
        .target-card.hidden {{ display: none; }}
        .target-card.scanning, .target-card.running {{ border-left: 4px solid #3fb950; }}
        .target-card.done, .target-card.completed {{ border-left: 4px solid #58a9ff; }}
        .target-card.waiting {{ border-left: 4px solid #f0883e; }}
        
        .card-header {{ padding: 16px; background: #21262d; display: flex; justify-content: space-between; align-items: center; }}
        .card-title {{ font-size: 15px; font-weight: 600; color: #58a9ff; }}
        .status-badge {{ padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; }}
        .status-badge.scanning, .status-badge.running {{ background: #238636; color: #fff; }}
        .status-badge.done, .status-badge.completed {{ background: #58a9ff; color: #fff; }}
        .status-badge.waiting {{ background: #f0883e; color: #000; }}
        
        .card-body {{ padding: 16px; }}
        .progress-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .progress-label {{ font-size: 12px; color: #8b949e; }}
        .progress-value {{ font-size: 14px; font-weight: 700; color: #3fb950; }}
        .progress-bar {{ height: 8px; background: #30363d; border-radius: 4px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #3fb950, #58a9ff); border-radius: 4px; transition: width 0.5s ease; }}
        
        .target-count {{ margin-top: 12px; font-size: 12px; color: #8b949e; }}
        
        /* Modal */
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; align-items: center; justify-content: center; }}
        .modal-overlay.show {{ display: flex; }}
        .modal {{ background: #161b22; border: 1px solid #30363d; border-radius: 14px; width: 95%; max-width: 800px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }}
        .modal-header {{ padding: 20px 24px; background: #21262d; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }}
        .modal-title {{ font-size: 18px; font-weight: 600; color: #58a9ff; }}
        .modal-close {{ font-size: 28px; color: #8b949e; cursor: pointer; line-height: 1; }}
        .modal-close:hover {{ color: #fff; }}
        .modal-body {{ padding: 24px; overflow-y: auto; flex: 1; }}
        
        .modal-progress {{ margin-bottom: 24px; }}
        .modal-progress .row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .modal-progress .label {{ color: #8b949e; }}
        .modal-progress .value {{ font-weight: 600; }}
        .modal-progress .bar {{ height: 10px; background: #30363d; border-radius: 5px; overflow: hidden; }}
        .modal-progress .fill {{ height: 100%; background: linear-gradient(90deg, #3fb950, #58a9ff); }}
        
        .sub-targets {{ margin-top: 20px; }}
        .sub-targets h3 {{ font-size: 14px; color: #8b949e; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        .sub-target {{ background: #0d1117; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
        .sub-header {{ padding: 12px 16px; background: #21262d; display: flex; justify-content: space-between; align-items: center; }}
        .sub-url {{ font-size: 13px; color: #c9d1d9; font-weight: 500; }}
        .sub-tools-count {{ font-size: 11px; color: #8b949e; }}
        
        .tools-list {{ padding: 12px 16px; }}
        
        .tool-item {{ background: #161b22; border-radius: 6px; margin-bottom: 8px; padding: 12px; }}
        .tool-item:last-child {{ margin-bottom: 0; }}
        .tool-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
        .tool-name {{ padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .tool-strix {{ background: #238636; color: #fff; }}
        .tool-nikto {{ background: #f0883e; color: #000; }}
        .tool-nmap {{ background: #58a9ff; color: #fff; }}
        .tool-status {{ margin-left: auto; font-size: 11px; padding: 3px 8px; border-radius: 10px; }}
        .tool-status.scanning, .tool-status.running {{ background: #238636; color: #fff; }}
        .tool-status.done, .tool-status.completed {{ background: #58a9ff; color: #fff; }}
        .tool-status.waiting {{ background: #f0883e; color: #000; }}
        
        .tool-progress-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
        .tool-progress-bar {{ flex: 1; height: 5px; background: #30363d; border-radius: 3px; }}
        .tool-progress-fill {{ height: 100%; background: #3fb950; border-radius: 3px; }}
        .tool-progress-num {{ font-size: 12px; color: #3fb950; font-weight: 600; min-width: 40px; text-align: right; }}
        
        .tool-detail {{ background: #0d1117; border-radius: 4px; padding: 10px; font-size: 12px; }}
        .detail-row {{ display: flex; gap: 10px; margin-bottom: 5px; }}
        .detail-row:last-child {{ margin-bottom: 0; }}
        .detail-row .label {{ color: #8b949e; min-width: 70px; }}
        .detail-row .value {{ color: #c9d1d9; }}
        .detail-row .highlight {{ color: #f0883e; font-weight: 600; }}
        
        .pagination {{ display: flex; justify-content: center; gap: 8px; padding: 20px; }}
        .page-btn {{ padding: 8px 14px; background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 13px; cursor: pointer; }}
        .page-btn:hover, .page-btn.active {{ background: #238636; border-color: #3fb950; }}
        .page-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        
        .empty-state {{ text-align: center; padding: 60px 20px; color: #8b949e; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ 漏洞扫描看板</h1>
        <span class="time">{now} | 项目数: {total}</span>
    </div>
    
    <div class="toolbar">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="搜索项目名称..." oninput="filterProjects()">
        </div>
        <div class="filter-btns">
            <button class="filter-btn active" onclick="setFilter('all')">全部</button>
            <button class="filter-btn" onclick="setFilter('scanning')">扫描中</button>
            <button class="filter-btn" onclick="setFilter('done')">已完成</button>
            <button class="filter-btn" onclick="setFilter('waiting')">等待中</button>
        </div>
    </div>
    
    <div class="stats-bar">
        <div class="stat"><div class="stat-value">{status['total']}</div><div class="stat-label">总进程</div></div>
        <div class="stat"><div class="stat-value">{status['strix']}</div><div class="stat-label">Strix</div></div>
        <div class="stat"><div class="stat-value">{status['nikto']}</div><div class="stat-label">Nikto</div></div>
        <div class="stat"><div class="stat-value">{status['nmap']}</div><div class="stat-label">Nmap</div></div>
    </div>
    
    <div class="pagination-bar">
        <span class="page-info" id="pageInfo">共 {total} 个项目</span>
        <div class="page-size">
            每页显示: <select id="pageSize" onchange="changePageSize()">
                <option value="8" selected>8 条</option>
                <option value="16">16 条</option>
                <option value="32">32 条</option>
            </select>
        </div>
    </div>
    
    <div class="targets-grid" id="targetsGrid"></div>
    
    <div class="pagination" id="pagination"></div>
    
    <!-- Modal -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle">项目详情</span>
                <span class="modal-close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <script>
        // 项目数据
        const projectsData = {cards_json};
        const fullProjectsData = {projects_json};
        
        let currentPage = 1;
        let pageSize = 8;
        let currentFilter = 'all';
        let searchTerm = '';
        
        console.log('加载了 ' + projectsData.length + ' 个项目');
        
        function renderProjects() {{
            const grid = document.getElementById('targetsGrid');
            const filtered = projectsData.filter(p => {{
                const matchFilter = currentFilter === 'all' || p.status === currentFilter;
                const matchSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
                return matchFilter && matchSearch;
            }});
            
            const total = filtered.length;
            const start = (currentPage - 1) * pageSize;
            const end = start + pageSize;
            const pageData = filtered.slice(start, end);
            
            if (pageData.length === 0) {{
                grid.innerHTML = '<div class="empty-state">没有找到匹配的项目</div>';
                document.getElementById('pageInfo').textContent = '共 0 个项目';
                document.getElementById('pagination').innerHTML = '';
                return;
            }}
            
            grid.innerHTML = pageData.map(p => `
                <div class="target-card ${{p.status}}" data-index="${{p.index}}" onclick="openModal(${{p.index}})">
                    <div class="card-header">
                        <span class="card-title">${{p.name}}</span>
                        <span class="status-badge ${{p.status}}">${{p.statusText}}</span>
                    </div>
                    <div class="card-body">
                        <div class="progress-row">
                            <span class="progress-label">进度</span>
                            <span class="progress-value">${{p.progress}}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${{p.progress}}%"></div>
                        </div>
                        <div class="target-count">扫描目标: ${{p.targetCount}} 个</div>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('pageInfo').textContent = `第 ${{currentPage}} / ${{Math.ceil(total/pageSize)}} 页，共 ${{total}} 个项目`;
            renderPagination(Math.ceil(total / pageSize));
        }}
        
        function renderPagination(totalPages) {{
            const pag = document.getElementById('pagination');
            if (totalPages <= 1) {{ pag.innerHTML = ''; return; }}
            
            let html = `<button class="page-btn" onclick="goPage(1)" ${{currentPage === 1 ? 'disabled' : ''}}>首页</button>`;
            html += `<button class="page-btn" onclick="goPage(${{currentPage - 1}})" ${{currentPage === 1 ? 'disabled' : ''}}>上一页</button>`;
            
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {{
                html += `<button class="page-btn ${{i === currentPage ? 'active' : ''}}" onclick="goPage(${{i}})">${{i}}</button>`;
            }}
            
            html += `<button class="page-btn" onclick="goPage(${{currentPage + 1}})" ${{currentPage === totalPages ? 'disabled' : ''}}>下一页</button>`;
            html += `<button class="page-btn" onclick="goPage(${{totalPages}})" ${{currentPage === totalPages ? 'disabled' : ''}}>末页</button>`;
            
            pag.innerHTML = html;
        }}
        
        function goPage(page) {{
            currentPage = page;
            renderProjects();
        }}
        
        function changePageSize() {{
            pageSize = parseInt(document.getElementById('pageSize').value);
            currentPage = 1;
            renderProjects();
        }}
        
        function setFilter(filter) {{
            currentFilter = filter;
            currentPage = 1;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            renderProjects();
        }}
        
        function filterProjects() {{
            searchTerm = document.getElementById('searchInput').value;
            currentPage = 1;
            renderProjects();
        }}
        
        function openModal(index) {{
            console.log('打开Modal, index:', index);
            
            const cardData = projectsData.find(p => p.index === index);
            if (!cardData) {{
                console.error('未找到项目数据:', index);
                return;
            }}
            
            const fullProject = fullProjectsData.find(p => p.name === cardData.name);
            if (!fullProject) {{
                console.error('未找到完整项目数据:', cardData.name);
                return;
            }}
            
            document.getElementById('modalTitle').textContent = cardData.name;
            
            const statusText = {{"scanning": "扫描中", "done": "已完成", "waiting": "等待中", "completed": "已完成"}}[cardData.status] || "未知";
            
            let modalHtml = `
                <div class="modal-progress">
                    <div class="row">
                        <span class="label">状态</span>
                        <span class="status-badge ${{cardData.status}}">${{statusText}}</span>
                    </div>
                    <div class="row">
                        <span class="label">进度</span>
                        <span class="value" style="color:#3fb950">${{cardData.progress}}%</span>
                    </div>
                    <div class="bar"><div class="fill" style="width:${{cardData.progress}}%"></div></div>
                </div>
            `;
            
            if (fullProject.targets && fullProject.targets.length > 0) {{
                modalHtml += '<div class="sub-targets"><h3>扫描目标</h3>';
                
                fullProject.targets.forEach(t => {{
                    modalHtml += `<div class="sub-target">
                        <div class="sub-header">
                            <span class="sub-url">📍 ${{t.name}}</span>
                            <span class="sub-tools-count">${{t.tools ? t.tools.length : 0}} 个工具</span>
                        </div>
                        <div class="tools-list">`;
                    
                    if (t.tools) {{
                        t.tools.forEach(tool => {{
                            let detail = '';
                            if (tool.name === 'Strix') {{
                                const eps = tool.endpoints ? tool.endpoints.slice(0, 5).join(', ') : '无';
                                detail = `<div class="detail-row"><span class="label">已扫描:</span><span class="value">${{tool.scanned || 0}} URL</span></div>
                                    <div class="detail-row"><span class="label">发现端点:</span><span class="value highlight">${{tool.found || 0}}</span></div>
                                    <div class="detail-row"><span class="label">端点列表:</span><span class="value">${{eps}}</span></div>`;
                            }} else if (tool.name === 'Nikto') {{
                                const vulns = tool.vulns ? tool.vulns.join(', ') : '无';
                                detail = `<div class="detail-row"><span class="label">已扫描:</span><span class="value">${{tool.scanned || 0}} 项</span></div>
                                    <div class="detail-row"><span class="label">发现问题:</span><span class="value highlight">${{tool.found || 0}}</span></div>
                                    <div class="detail-row"><span class="label">问题:</span><span class="value">${{vulns}}</span></div>`;
                            }} else if (tool.name === 'Nmap') {{
                                const ports = tool.ports ? tool.ports.join(', ') : '等待';
                                detail = `<div class="detail-row"><span class="label">已扫描:</span><span class="value">${{tool.scanned || 0}} IP</span></div>
                                    <div class="detail-row"><span class="label">开放端口:</span><span class="value highlight">${{tool.found || 0}}</span></div>
                                    <div class="detail-row"><span class="label">端口:</span><span class="value">${{ports}}</span></div>`;
                            }}
                            
                            const toolStatusText = {{"scanning": "扫描中", "done": "已完成", "waiting": "等待中", "completed": "已完成"}}[tool.status] || "未知";
                            const toolStatusClass = tool.status;
                            
                            modalHtml += `<div class="tool-item">
                                <div class="tool-header">
                                    <span class="tool-name tool-${{tool.name.toLowerCase()}}">${{tool.name}}</span>
                                    <span class="tool-status ${{toolStatusClass}}">${{toolStatusText}}</span>
                                </div>
                                <div class="tool-progress-row">
                                    <div class="tool-progress-bar"><div class="tool-progress-fill" style="width:${{tool.progress || 0}}%"></div></div>
                                    <span class="tool-progress-num">${{tool.progress || 0}}%</span>
                                </div>
                                <div class="tool-detail">${{detail}}</div>
                            </div>`;
                        }});
                    }}
                    
                    modalHtml += '</div></div>';
                }});
                
                modalHtml += '</div>';
            }}
            
            document.getElementById('modalBody').innerHTML = modalHtml;
            document.getElementById('modalOverlay').classList.add('show');
        }}
        
        function closeModal() {{
            document.getElementById('modalOverlay').classList.remove('show');
        }}
        
        // 点击遮罩关闭
        document.getElementById('modalOverlay').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});
        
        // ESC键关闭
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});
        
        // 初始化
        renderProjects();
    </script>
</body>
</html>'''
    
    with open("/tmp/vuln_scan_dashboard.html", 'w') as f:
        f.write(html)
    
    # 保存数据文件
    with open("/tmp/vuln_dashboard_data.json", 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 看板已更新: {len(projects)} 个项目, {status['total']} 进程")

if __name__ == "__main__":
    generate_dashboard()
