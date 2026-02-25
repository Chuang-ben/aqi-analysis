# AQI 分析系統

台灣環境部空氣品質指數（AQI）數據取得與視覺化分析系統。

## ✨ 功能特性

### 1. 即時數據取得
- 串接環境部 API (aqx_p_432) 獲取全台 AQI 數據
- 自動處理 API 認證和錯誤處理

### 2. 地圖視覺化
- 使用 Folium 在地圖上標示所有測站位置
- 互動式地圖：點擊測站查看詳細信息
- 懸停提示：站名 + AQI 即時預覽

### 3. 分色顯示系統
- 🟢 AQI 0-50：綠色（良好）
- 🟡 AQI 51-100：黃色（普通）
- 🔴 AQI 101+：紅色（不健康）

### 4. 空間計算
- 計算每個測站到台北車站 (25.0478°N, 121.5170°E) 的地理距離
- 使用 Haversine 公式確保計算精度

### 5. 數據分析與報告
- 生成 CSV 報告，包含：
  - 測站名稱、所在縣市
  - 即時 AQI 值
  - 污染物狀態
  - 經緯度
  - **距台北車站距離（公里）**
  - 發布時間
- 自動按距離排序

## 🚀 快速開始

### 環境設置

```bash
# 創建 conda 環境（已完成）
conda create -n RSGI python=3.12

# 啟動環境
conda activate RSGI

# 安裝依賴
pip install -r requirements.txt
```

### 配置 API

在 `.env` 檔案中設置環境部 API Key：
```
MOENV_API_KEY=09aca59d-4ff8-4dfd-9130-a4c2f4135469
```

### 運行程式

```bash
python main.py
```

## 📊 輸出文件

### aqi_map.html
- 互動式 Folium 地圖
- 85 個空氣品質測站標記
- 按 AQI 等級著色
- 點擊標記查看詳細信息
- 右下角色彩圖例

### aqi_report.csv
數據報告示例（前5筆）：
```
sitename,county,aqi,pollutant,status,latitude,longitude,距台北車站(公里),publishtime
萬華,臺北市,31,,良好,25.046503,121.507972,0.92,2026/02/25 16:00:00
大同,臺北市,52,二氧化氮,普通,25.063315,121.513421,1.76,2026/02/25 16:00:00
中山,臺北市,46,,良好,25.062361,121.526528,1.88,2026/02/25 16:00:00
古亭,臺北市,37,,良好,25.020608,121.529556,3.28,2026/02/25 16:00:00
```

信息一覽：
- 📍 最近測站：**萬華（0.92 公里）**
- 📈 最遠測站：**蘇澳（460+ 公里）**
- 📊 總測站數：**85 個**

## 📁 項目結構

```
python-project/
├── main.py                  # 主程式（API取得+地圖+報告）
├── github_setup.py          # GitHub設置腳本（舊版本）
├── setup_github.py          # GitHub初始化腳本（新版本）
├── .env                     # 環境變數（API Key）
├── .gitignore              # Git忽略規則
├── requirements.txt         # Python依賴列表
├── README.md               # 本文件
├── data/                   # 數據目錄
└── outputs/
    ├── aqi_map.html        # 互動式地圖
    └── aqi_report.csv      # 數據報告
```

## 🛠 技術棧

| 用途 | 工具/庫 | 版本 |
|------|---------|------|
| Python | Python | 3.12 |
| 環境管理 | Conda | - |
| API 請求 | Requests | ≥2.31.0 |
| 環境變數 | python-dotenv | ≥1.0.0 |
| 地圖可視化 | Folium | ≥0.14.0 |
| 數據處理 | Pandas | ≥2.0.0 |

## 🔢 算法說明

### Haversine 距離公式
計算兩點間的地理距離（地球表面）：

```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × asin(√a)
distance = R × c
```

其中 R 為地球平均半徑（6371 公里）

## 🌐 API 文檔

- 資料來源：[環境部開放資料平台](https://data.moenv.gov.tw/)
- API 端點：`https://data.moenv.gov.tw/api/v2/aqx_p_432`
- 數據類型：空氣污染指標（AQI）
- 更新頻率：每小時

## 📤 雲端備份（GitHub）

### 設置步驟

1. **安裝工具**
   - Git：https://git-scm.com/download/win
   - GitHub CLI（可選）：https://cli.github.com/

2. **初始化本地倉庫**
   ```bash
   git init
   git config user.email "your_email@example.com"
   git config user.name "Ben"
   git add .
   git commit -m "Initial commit: AQI analysis system"
   ```

3. **建立 GitHub 倉庫**
   - 訪問：https://github.com/new
   - 倉庫名：`aqi-analysis`
   - 設為 Public（公開）

4. **推送代碼**
   
   方式 A（推薦）：
   ```bash
   gh auth login
   gh repo create aqi-analysis --public --source=. --remote=origin --push
   ```
   
   方式 B（手動）：
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aqi-analysis.git
   git push -u origin main
   ```

## 💡 使用技巧

### 查看最近的污染源
```bash
# CSV 報告已按距離排序，最近的測站在最前面
head -2 outputs/aqi_report.csv
```

### 生成更新的數據
```bash
# 程式會自動獲取最新數據並更新地圖和報告
python main.py
```

### 自定義環境
修改 `main.py` 中的設置：
```python
# 改變地圖中心點
center_lat = 23.5
center_lon = 121

# 改變目標距離計算點
taipei_station_lat = 25.0478
taipei_station_lon = 121.5170
```

## ⚙️ 自動化裝置

程式已內建自動套件安裝功能：
```python
def setup_packages():
    """自動檢查並安裝必要的 Python 套件"""
```

如果缺少依賴，程式會自動安裝。

## 🐛 故障排除

| 問題 | 解決方案 |
|-------|---------|
| API Key 無效 | 檢查 .env 文件中的 MOENV_API_KEY |
| 沒有有效測站數據 | 檢查網路連線和 API 狀態 |
| 地圖無法打開 | 確保 outputs 目錄存在且有寫入權限 |
| CSV 編碼問題 | 文件已使用 UTF-8 with BOM 編碼 |

## 📄 許可證

MIT License

## 👤 作者

Ben  
國立臺灣大學地理環境資源學系

## 📞 聯絡方式

- 環境部 API：https://data.moenv.gov.tw/
- GitHub：https://github.com/

---

**最後更新**：2026年2月25日  
**程式版本**：1.0  
**Python 版本**：3.12
