"""
GitHub 倉庫初始化和推送腳本
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_git_repo(repo_path: str, repo_name: str = 'aqi-analysis'):
    """使用命令行初始化 Git 仓库并推送到 GitHub
    
    Args:
        repo_path: 本地仓库路径
        repo_name: GitHub 仓库名称
    """
    
    print("=" * 60)
    print("GitHub 倉庫初始化和推送")
    print("=" * 60)
    
    repo_dir = Path(repo_path)
    os.chdir(repo_dir)
    
    # 檢查是否已有 .git 目錄
    if (repo_dir / '.git').exists():
        print("✓ Git 倉庫已存在")
    else:
        print("⏳ 初始化 Git 倉庫...")
        
        # 初始化倉庫
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        print("✓ Git 倉庫已初始化")
        
        # 配置用户信息
        try:
            subprocess.run(
                ['git', 'config', 'user.email', 'ben@example.com'],
                check=True, capture_output=True
            )
            subprocess.run(
                ['git', 'config', 'user.name', 'Ben'],
                check=True, capture_output=True
            )
            print("✓ Git 用户信息已配置")
        except subprocess.CalledProcessError:
            pass
    
    # 創建 .gitignore
    gitignore_path = repo_dir / '.gitignore'
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Data
outputs/
data/
*.log
"""
        gitignore_path.write_text(gitignore_content)
        print("✓ .gitignore 已創建")
    
    # 創建 README.md
    readme_path = repo_dir / 'README.md'
    if not readme_path.exists():
        readme_content = """# AQI 分析系統

台灣環境部空氣品質指數（AQI）數據取得與視覺化分析系統。

## 功能特性

- **即時數據取得**：串接環境部 API (aqx_p_432) 獲取全台 AQI 數據
- **地圖視覺化**：使用 Folium 在地圖上標示所有測站位置
- **分色顯示**：
  - 🟢 AQI 0-50：綠色（良好）
  - 🟡 AQI 51-100：黃色（普通）
  - 🔴 AQI 101+：紅色（不健康）
- **距離計算**：計算每個測站到台北車站的距離
- **數據分析**：生成 CSV 報告含距離、AQI 值等信息

## 使用方式

### 環境設置

```bash
# 創建 conda 環境
conda create -n aqi_env python=3.12

# 啟動環境
conda activate aqi_env

# 安裝依賴
pip install requests python-dotenv folium pandas
```

### 配置 API

在 `.env` 檔案中設置環境部 API Key：

```
MOENV_API_KEY=your_api_key_here
```

### 運行程式

```bash
python main.py
```

## 輸出文件

- `outputs/aqi_map.html` - 互動式地圖
- `outputs/aqi_report.csv` - 包含距離信息的數據報告

## 項目結構

```
.
├── main.py                  # 主程式
├── github_setup.py          # GitHub 初始化腳本
├── .env                     # 環境變數設置
├── .gitignore              # Git 忽略文件
├── README.md               # 項目說明
├── data/                   # 數據目錄
└── outputs/                # 輸出目錄
    ├── aqi_map.html        # 地圖文件
    └── aqi_report.csv      # 報告文件
```

## 技術棧

- Python 3.12
- Folium - 地圖可視化
- Pandas - 數據處理
- Requests - HTTP 請求
- Python-dotenv - 環境變數管理

## API 文檔

- [環境部開放資料平台](https://data.moenv.gov.tw/)
- API 端點：`https://data.moenv.gov.tw/api/v2/aqx_p_432`

## 許可證

MIT

## 作者

Ben
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        print("✓ README.md 已創建")
    
    # 添加所有文件
    print("⏳ 正在添加文件到 Git...")
    try:
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        print("✓ 文件已添加")
    except subprocess.CalledProcessError as e:
        print(f"⚠ 添加文件失敗: {e}")
        return False
    
    # 檢查是否有未提交的更改
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, check=True
        )
        
        if result.stdout.strip():
            # 提交更改
            print("⏳ 正在提交更改...")
            subprocess.run(
                ['git', 'commit', '-m', 'Initial commit: AQI analysis system'],
                check=True, capture_output=True
            )
            print("✓ 更改已提交")
        else:
            print("✓ 沒有新的更改")
    except subprocess.CalledProcessError as e:
        print(f"⚠ 提交失敗: {e}")
    
    # 打印指令給用戶
    print("\n" + "=" * 60)
    print("GitHub 倉庫推送說明")
    print("=" * 60)
    print(f"\n1. 在 GitHub 上創建新倉庫: {repo_name}")
    print("   網址: https://github.com/new")
    print(f"   倉庫名: {repo_name}")
    print("   描述: Taiwan AQI Analysis System")
    print("   設置為 Public（公開）")
    print("\n2. 配置遠端倉庫並推送：")
    print(f"   git remote add origin https://github.com/YOUR_USERNAME/{repo_name}.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("\n3. 使用 GitHub CLI：")
    print("   gh repo create aqi-analysis --public --source=. --remote=origin --push")
    print("\n" + "=" * 60)
    
    return True


if __name__ == '__main__':
    repo_path = os.path.dirname(os.path.abspath(__file__))
    setup_git_repo(repo_path)
