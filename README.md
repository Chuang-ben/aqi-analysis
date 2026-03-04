# 🌍 雙圖層地圖系統 - AQI測站與避難所空間分析

台灣地區空氣品質指數（AQI）測站與避難所的綜合空間分析系統，提供互動式地圖視覺化和風險評估功能。

## 🎯 專案概述

本專案建立了一個完整的空氣品質與避難所空間分析系統，整合了：
- 🗺️ **雙圖層互動地圖**：AQI測站與避難所位置標示
- 📊 **空氣品質分析**：基於距離加權的AQI評估
- 🔍 **位置合理性審計**：避難所位置品質控制
- 🚨 **風險評估系統**：三級風險分類（low risk/warning/high risk）


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
│   └── shelter_aqi_analysis.py     # 主程式腳本
├── data/                           # 資料檔案
│   └── shelters_cleaned.csv       # 清理後避難所數據
├── outputs/                        # 生成輸出
│   └── audit_report.md            # 空間審計報告
│   └── shelter_aqi_analysis.csv   # AQI分析結果
│   └── dual_layer_map.html        # 雙圖層互動地圖
├── README.md                      # 專案說明
├── reflection.md                  # 專案反思報告
├── requirements.txt               # Python依賴

```

### 執行程式
執行完之後會生成兩個檔案：
- `outputs/shelter_aqi_analysis.csv`（5,904筆分析結果）
- `outputs/dual_layer_map.html`（16.5MB互動式地圖）

#### 整合版執行（推薦）
一鍵執行所有功能，獲得完整分析結果：
```bash
python script/shelter_aqi_analysis.py
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
  - 🟢 **low risk**：3,971個（67.3%）
  - 🟡 **warning**：1,739個（29.5%）
  - 🔴 **high risk**：194個（3.3%）

### 🏢 避難所類型分佈
- **🏢 室內避難所**：5,321個（90.1%）
- **🌳 室外避難所**：583個（9.9%）

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

Chuang Ben  
國立臺灣大學土木工程學系  
RSGI 專案團隊

## 📞 聯絡方式

- **GitHub**：https://github.com/Chuang-ben/aqi-analysis
- **環境部API**：https://data.moenv.gov.tw/

---

**最後更新**：2026年3月4日  
**程式版本**：v2.0（雙圖層地圖系統）  
**Python版本**：3.12  
**資料品質**：98.8%（5,904/5,973）
