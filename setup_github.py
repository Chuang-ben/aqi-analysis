"""
GitHub 倉庫初始化和推送腳本
無需系統 Git 即可工作 - 提供詳細說明步驟
"""

import os
from pathlib import Path


def create_project_files():
    """創建項目必要文件"""
    
    repo_dir = Path.cwd()
    
    # .gitignore
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

# Outputs
outputs/*.html
outputs/

# Data
data/
*.log
"""
        gitignore_path.write_text(gitignore_content)
        print("✓ .gitignore 已創建")
    
    # README.md
    readme_path = repo_dir / 'README.md'
    if not readme_path.exists():
        readme_content = """# AQI 分析系統

台灣環境部空氣品質指數（AQI）數據取得與視覺化分析系統。

## 功能特性

- **即時數據取得**：串接環境部 API 獲取全台 AQI 數據
- **地圖視覺化**：使用 Folium 在地圖上標示所有測站位置
- **分色顯示**：AQI 0-50 綠色、51-100 黃色、101+ 紅色
- **距離計算**：計算每個測站到台北車站的距離
- **數據分析**：生成 CSV 報告（含距離資訊、自動排序）

## 快速開始

### 環境設置

```bash
conda create -n aqi_env python=3.12
conda activate aqi_env
pip install -r requirements.txt
```

### 使用

```bash
python main.py
```

輸出文件：
- `outputs/aqi_map.html` - 互動式地圖
- `outputs/aqi_report.csv` - 數據報告（按距台北車站排序）

## 項目結構

```
.
├── main.py              # 主程式
├── requirements.txt     # 依賴列表
├── .env                 # API 密鑰配置
├── README.md
└── outputs/             # 輸出目錄
    ├── aqi_map.html     # 互動式地圖
    └── aqi_report.csv   # 數據報告
```

## 配置

在 `.env` 文件中設置環境部 API Key：
```
MOENV_API_KEY=your_api_key_here
```

## 技術棧

- Python 3.12
- Folium - 地圖可視化
- Pandas - 數據處理
- Requests - HTTP 請求
- Python-dotenv - 環境變數管理

## 作者

Ben
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        print("✓ README.md 已創建")
    
    # requirements.txt
    req_path = repo_dir / 'requirements.txt'
    if not req_path.exists():
        req_content = """requests>=2.31.0
python-dotenv>=1.0.0
folium>=0.14.0
pandas>=2.0.0
"""
        req_path.write_text(req_content)
        print("✓ requirements.txt 已創建")


def print_setup_instructions():
    """打印完整的設置說明"""
    
    print("\n" + "=" * 75)
    print("GitHub 倉庫初始化和推送說明")
    print("=" * 75)
    
    print("\n📝 步驟 1：安裝必要工具")
    print("-" * 75)
    print("□ Git：https://git-scm.com/download/win")
    print("□ GitHub CLI（可選但推薦）：https://cli.github.com/")
    
    print("\n📁 步驟 2：初始化本地 Git 倉庫")
    print("-" * 75)
    print("在項目目錄（本終端中）運行以下命令：")
    print()
    print("  git init")
    print("  git config user.email 'your_email@example.com'")
    print("  git config user.name 'Ben'")
    print("  git add .")
    print("  git commit -m 'Initial commit: AQI analysis system'")
    print()
    
    print("🚀 步驟 3：推送到 GitHub")
    print("-" * 75)
    print("\n方式 A：使用 GitHub CLI（推薦）")
    print("  a) 首先登入 GitHub：")
    print("     gh auth login")
    print()
    print("  b) 創建並推送倉庫：")
    print("     gh repo create aqi-analysis --public --source=. --remote=origin --push")
    print()
    print("\n方式 B：網頁 + Git 命令")
    print("  a) 訪問：https://github.com/new")
    print("  b) 填寫信息：")
    print("     • Repository name：aqi-analysis")
    print("     • Description：Taiwan AQI Analysis System")
    print("     • Public（選擇公開）")
    print("  c) 建立倉庫後，運行：")
    print("     git branch -M main")
    print("     git remote add origin https://github.com/YOUR_USERNAME/aqi-analysis.git")
    print("     git push -u origin main")
    print()
    print("  💡 提示：將 YOUR_USERNAME 更換為您的 GitHub 用戶名")
    
    print("\n" + "=" * 75)
    print("完成步驟後，您的代碼將備份到：")
    print("https://github.com/YOUR_USERNAME/aqi-analysis")
    print("=" * 75)
    print()


if __name__ == '__main__':
    print("=" * 75)
    print("GitHub 倉庫初始化")
    print("=" * 75)
    
    create_project_files()
    print_setup_instructions()
