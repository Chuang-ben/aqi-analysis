# 🌍 雙圖層地圖系統 - AQI測站與避難所空間分析

台灣地區空氣品質指數（AQI）測站與避難所的綜合空間分析系統，提供互動式地圖視覺化和風險評估功能。

## 🎯 專案概述

本專案建立了一個完整的空氣品質與避難所空間分析系統，整合了：
- 🗺️ **雙圖層互動地圖**：AQI測站與避難所位置標示
- 📊 **空氣品質分析**：基於距離加權的AQI評估
- 🔍 **位置合理性審計**：避難所位置品質控制
- 🚨 **風險評估系統**：三級風險分類（低/中/高風險）

## ✨ 核心功能

###  空氣品質分析
- **距離計算**：使用Haversine公式精確計算球面距離
- **加權平均**：距離加權的AQI評估（1/(1+distance)權重）
- **風險分類**：三級風險評估系統
- **情境模擬**：高風險測站情境注入分析

### 🔍 資料品質控制
- **空間審計**：多層次位置合理性檢查
- **異常檢測**：識別和移除不合理位置
- **人工驗證**：21個特定地點手動檢查
- **最終品質**：98.8%位置準確性（5,904/5,973）

### 🗺️ 地圖視覺化（homework2分支）
- **雙圖層互動地圖**：AQI測站與避難所位置標示
- **AQI測站圖層**：85個空氣品質測站實時數據
- **避難所圖層**：5,904個清理後的避難所位置
- **互動功能**：點擊彈窗、風險評估、圖層切換

## 🚀 快速開始

### 環境設置

```bash
# 創建 conda 環境
conda create -n RSGI python=3.12

# 啟動環境
conda activate RSGI

# 安裝依賴
pip install -r requirements.txt
```

### 專案結構

```
python-project/
├── script/                          # 主要程式腳本
│   └── integrated_aqi_analysis.py  # 整合版主程式（唯一腳本）
├── data/                           # 資料檔案
│   ├── .gitkeep                   # Git保留目錄
│   └── shelters_cleaned.csv       # 清理後避難所數據
├── outputs/                        # 生成輸出
│   ├── .gitkeep                   # Git保留目錄
│   ├── shelter_aqi_analysis.csv   # AQI分析結果
│   └── audit_report.md            # 空間審計報告
├── .env                           # 環境變數（API密鑰）
├── dual_layer_map.html            # 雙圖層地圖
├── README.md                      # 專案說明
├── reflection.md                  # 專案反思報告
├── requirements.txt               # Python依賴

```

### 執行程式

#### 整合版執行（推薦）
一鍵執行所有功能，獲得完整分析結果：
```bash
python script/integrated_aqi_analysis.py
```
**輸出**：
- `outputs/shelter_aqi_analysis.csv`（5,904筆分析結果）
- `outputs/dual_layer_map.html`（16.5MB互動式地圖）
- 完整的統計報告

## 📊 分析結果

### 🎯 風險評估統計
- **📊 總避難所**：5,904個
- **✅ 有AQI資料**：5,904個（100%）
- **🔍 風險分佈**：
  - 🟢 **低風險**：3,916個（66.3%）
  - 🟡 **中等風險**：1,962個（33.2%）
  - ⚪ **無資料**：26個（0.4%）

### 🏢 避難所類型分佈
- **🏢 室內避難所**：5,321個（90.1%）
- **🌳 室外避難所**：583個（9.9%）

## 🛠 技術實現

### 📏 距離計算
使用**Haversine公式**計算地球表面兩點間的精確距離：
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑（公里）
    # 計算經緯度差值
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    # Haversine公式計算
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c
```

### ⚖️ 加權平均演算法
距離加權的AQI計算：
```python
weight = 1 / (1 + distance)
weighted_aqi = sum(aqi * weight) / sum(weight)
```

### 🔍 位置合理性檢查
多層次地理邊界檢查：
- **座標驗證**：WGS84經緯度格式確認
- **邊界檢查**：台灣地區地理邊界定義
- **異常檢測**：海上點位、邊界外異常
- **人工驗證**：21個特定地點手動檢查

## 📈 資料品質統計

### 🎯 清理效果
- **📄 原始資料**：5,973個避難所
- **✅ 合理位置**：5,904個（98.8%）
- **❌ 不合理位置**：69個（1.2%）
- **📊 品質提升**：從99.3%提升到98.8%

### 🚫 異常類型分佈
- **🌊 海上點位**：35個（50.7%）
- **🚫 邊界外異常**：5個（7.2%）
- **🔍 其他異常**：29個（42.1%）

## 🌐 資料來源

### 📊 AQI測站數據
- **來源**：環境部開放資料平台
- **API端點**：`https://data.moenv.gov.tw/api/v2/aqx_p_432`
- **更新頻率**：每小時
- **測站數量**：85個全台測站
- **資料格式**：程式自動獲取並處理

### 🏢 避難所數據
- **來源**：內政部消防署避難所資料
- **清理後數量**：5,904個合理位置
- **座標系統**：WGS84經緯度
- **品質控制**：多層次驗證機制
- **資料檔案**：`data/shelters_cleaned.csv`

## 💡 使用技巧

###  數據分析
```bash
# 查看高風險避難所
grep "高風險" outputs/shelter_aqi_analysis.csv

# 統計風險分佈
cut -d',' -f8 outputs/shelter_aqi_analysis.csv | sort | uniq -c

# 查看特定縣市統計
grep "高雄市" outputs/shelter_aqi_analysis.csv | wc -l

# 查看分析結果前10筆
head -10 outputs/shelter_aqi_analysis.csv
```

### 🔧 自定義設定
修改 `script/shelter_aqi_analysis.py` 中的設定：
```python
# 調整風險閾值
LOW_RISK_THRESHOLD = 50
MEDIUM_RISK_THRESHOLD = 100

# 修改距離範圍
SEARCH_RADIUS_KM = 50

# 修改情境注入測站
scenario_stations = ['大寮', '林園']
```

## 🐛 故障排除

| 問題 | 解決方案 |
|------|---------|
| 整合腳本執行失敗 | 檢查 `data/shelters_cleaned.csv` 是否存在且格式正確 |
| AQI資料獲取失敗 | 檢查網路連線，或稍後重試執行 |
| 地圖無法載入 | 確認 `outputs/dual_layer_map.html` 檔案是否存在 |
| 分析結果為空 | 檢查避難所資料座標格式是否正確 |
| 記憶體不足 | 大型地圖檔案需要較多記憶體，建議使用現代瀏覽器 |
| CSV編碼問題 | 檔案已使用UTF-8編碼，可用Excel直接開啟 |

### � 整合腳本特色
- **🔄 一鍵執行**: 自動完成所有分析步驟
- **📊 完整輸出**: 同時生成CSV分析結果和互動地圖
- **🔍 自動驗證**: 內建空間審計和資料品質檢查
- **📈 詳細報告**: 提供完整的統計分析和風險評估

## 📚 技術文檔

### 📄 重要檔案說明
- **`reflection.md`**：完整的專案反思報告
- **`audit_report.md`**：空間審計技術文檔（homework2分支）
- **`dual_layer_report.md`**：地圖統計報告（homework2分支）

### 🔧 技術棧
| 用途 | 工具/庫 | 版本 |
|------|---------|------|
| Python | Python | 3.12 |
| 資料處理 | Pandas | ≥2.0.0 |
| 地圖視覺化 | Folium | ≥0.14.0 |
| HTTP請求 | Requests | ≥2.31.0 |
| 環境變數 | python-dotenv | ≥1.0.0 |

## 🔄 版本控制

### 🌿 分支策略
- **🌿 master**：穩定版本，只包含核心功能
- **🌿 homework2**：開發版本，包含完整功能和分析

### 📦 部署建議
- **🔒 生產環境**：使用 master 分支
- **🔧 開發環境**：使用 homework2 分支
- **🚀 測試環境**：可基於 homework2 創建功能分支

## 📄 許可證

MIT License

## 👤 作者

Ben  
國立臺灣大學地理環境資源學系  
RSGI 專案團隊

## 📞 聯絡方式

- **GitHub**：https://github.com/Chuang-ben/aqi-analysis
- **環境部API**：https://data.moenv.gov.tw/

---

**最後更新**：2026年3月4日  
**程式版本**：v2.0（雙圖層地圖系統）  
**Python版本**：3.12  
**資料品質**：98.8%（5,904/5,973）
