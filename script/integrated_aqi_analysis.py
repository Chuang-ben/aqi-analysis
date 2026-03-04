#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AQI分析與雙圖層地圖系統 - 整合版
整合所有功能於一個腳本，讓教授可以直接運行得到完整結果

功能包含：
1. 空間審計和資料品質控制
2. 室內外避難所分類
3. AQI分析與風險評估
4. 雙圖層互動地圖生成

作者：Ben
國立臺灣大學地理環境資源學系
"""

import pandas as pd
import numpy as np
import folium
import requests
import os
import warnings
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
from folium import plugins
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# 載入環境變數
load_dotenv()

# ==================== 距離計算 ====================
def haversine_distance(lat1, lon1, lat2, lon2):
    """使用Haversine公式計算兩點間的精確距離（公里）"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球半徑（公里）
    return c * r

# ==================== 室內外分類 ====================
def classify_shelter_type(shelter_name, indoor_col=None, outdoor_col=None):
    """
    根據避難收容所名稱判斷室內外
    
    室內 (True): 中心、辦工處、大廳、館、穿堂、收容所、大樓、學校、小學
    室外 (False): 營區、廣場、公園
    如果沒有匹配到關鍵字，則參考現有的室內和室外欄位
    """
    if pd.isna(shelter_name):
        return False
    
    shelter_name = str(shelter_name).strip()
    
    # 室內關鍵字
    indoor_keywords = ['中心', '辦工處', '大廳', '館', '穿堂', '所', '大樓', '學校', '小學', '教會', '家', '室內']
    
    # 室外關鍵字
    outdoor_keywords = ['營區', '廣場', '公園', '場', '室外']
    
    # 檢查室內關鍵字
    for keyword in indoor_keywords:
        if keyword in shelter_name:
            return True
    
    # 檢查室外關鍵字
    for keyword in outdoor_keywords:
        if keyword in shelter_name:
            return False
    
    # 如果沒有匹配到關鍵字，參考現有的室內和室外欄位
    if indoor_col is not None and outdoor_col is not None:
        indoor_val = str(indoor_col).strip() if not pd.isna(indoor_col) else ""
        outdoor_val = str(outdoor_col).strip() if not pd.isna(outdoor_col) else ""
        
        # 如果室內欄位為"是"，則為室內
        if indoor_val == "是":
            return True
        # 如果室外欄位為"是"，則為室外
        elif outdoor_val == "是":
            return False
        # 如果室內室外都寫"是"或都寫"否"，則為室內 (True)
        elif (indoor_val == "是" and outdoor_val == "是") or (indoor_val == "否" and outdoor_val == "否"):
            return True
        # 其他情況預設為室內
        else:
            return True
    
    # 預設為室內
    return True

# ==================== 空間審計 ====================
def validate_shelter_locations(shelter_df):
    """
    驗證避難所位置的合理性
    
    參數：
    shelter_df: 避難所DataFrame
    
    返回：
    tuple: (清理後的DataFrame, 統計資訊)
    """
    print("🔍 開始空間審計...")
    
    # 台灣地區邊界
    taiwan_bounds = {
        'min_lon': 118.0,  # 台灣最西邊界 (包含金門)
        'max_lon': 123.0,  # 台灣最東邊界
        'min_lat': 20.0,   # 台灣最南邊界 (包含南沙)
        'max_lat': 27.0    # 台灣最北邊界 (包含釣魚台)
    }
    
    # 台灣主要地區的精確邊界
    taiwan_regions = {
        'taiwan_north': {'min_lon': 120.2, 'max_lon': 122.4, 'min_lat': 24.3, 'max_lat': 25.4},
        'taiwan_central': {'min_lon': 119.9, 'max_lon': 121.7, 'min_lat': 23.2, 'max_lat': 24.5},
        'taiwan_south': {'min_lon': 119.5, 'max_lon': 121.5, 'min_lat': 21.7, 'max_lat': 23.4},
        'penghu': {'min_lon': 119.2, 'max_lon': 119.8, 'min_lat': 23.2, 'max_lat': 23.9},
        'kinmen': {'min_lon': 118.2, 'max_lon': 118.5, 'min_lat': 24.2, 'max_lat': 24.6},
        'matsu': {'min_lon': 119.9, 'max_lon': 120.5, 'min_lat': 25.9, 'max_lat': 26.5}
    }
    
    original_count = len(shelter_df)
    print(f"📊 原始避難所數量: {original_count}")
    
    # 1. 檢查座標格式和缺失值
    valid_coords = shelter_df[
        (shelter_df['經度'].notna()) & 
        (shelter_df['緯度'].notna()) &
        (shelter_df['經度'] != 0) & 
        (shelter_df['緯度'] != 0)
    ].copy()
    
    invalid_coords_count = original_count - len(valid_coords)
    print(f"❌ 無效座標: {invalid_coords_count} 個")
    
    # 2. 檢查是否在台灣邊界內
    def is_in_taiwan(lon, lat):
        # 檢查是否在台灣大邊界內
        if not (taiwan_bounds['min_lon'] <= lon <= taiwan_bounds['max_lon'] and
                taiwan_bounds['min_lat'] <= lat <= taiwan_bounds['max_lat']):
            return False
        
        # 檢查是否在台灣主要地區邊界內
        for region, bounds in taiwan_regions.items():
            if (bounds['min_lon'] <= lon <= bounds['max_lon'] and
                bounds['min_lat'] <= lat <= bounds['max_lat']):
                return True
        
        return False
    
    # 3. 應用位置驗證
    valid_coords['is_valid'] = valid_coords.apply(
        lambda row: is_in_taiwan(row['經度'], row['緯度']), axis=1
    )
    
    # 4. 統計結果
    valid_count = valid_coords['is_valid'].sum()
    invalid_count = len(valid_coords) - valid_count
    
    print(f"✅ 合理位置: {valid_count} 個")
    print(f"❌ 不合理位置: {invalid_count} 個")
    print(f"📊 品質百分比: {(valid_count/original_count)*100:.1f}%")
    
    # 5. 返回清理後的資料
    cleaned_shelters = valid_coords[valid_coords['is_valid']].copy()
    
    # 移除臨時欄位
    cleaned_shelters = cleaned_shelters.drop('is_valid', axis=1)
    
    stats = {
        'original_count': original_count,
        'invalid_coords': invalid_coords_count,
        'invalid_locations': invalid_count,
        'final_count': len(cleaned_shelters),
        'quality_percentage': (len(cleaned_shelters)/original_count)*100
    }
    
    return cleaned_shelters, stats

# ==================== AQI資料獲取 ====================
def fetch_aqi_data():
    """從環境部API獲取AQI資料（使用API密鑰認證）"""
    print("🌐 獲取AQI資料...")
    
    # 環境部API端點
    url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    
    # 獲取API密鑰
    api_key = os.getenv('MOENV_API_KEY')
    if not api_key:
        print("❌ 未找到 MOENV_API_KEY 環境變數")
        print("🔄 使用模擬AQI資料進行測試...")
        return create_mock_aqi_data()
    
    try:
        print("⏳ 正在取得環境部 AQI 數據...")
        
        # 設定請求參數
        params = {
            'api_key': api_key,
            'limit': 1000,
            'sort': 'ImportDate',
            'order': 'desc'
        }
        
        # 設定請求標頭
        headers = {
            'User-Agent': 'AQI-Analysis-System/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # API 可能直接返回列表或包含 records 的字典
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            if data.get('success'):
                records = data.get('records', [])
            else:
                print(f"✗ API 返回錯誤: {data.get('message', '未知錯誤')}")
                return None
        else:
            print("✗ 無效的 API 返回格式")
            return None
        
        print(f"✅ 成功獲取 {len(records)} 筆AQI測站資料")
        
        # 轉換為DataFrame並處理數值欄位
        aqi_df = pd.DataFrame(records)
        
        # 轉換數值欄位
        numeric_columns = ['aqi', 'pm25', 'pm10', 'o3', 'no2', 'so2', 'co', 'latitude', 'longitude']
        for col in numeric_columns:
            if col in aqi_df.columns:
                aqi_df[col] = pd.to_numeric(aqi_df[col], errors='coerce')
        
        return aqi_df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ 網路請求失敗: {e}")
        print("🔄 使用模擬AQI資料進行測試...")
        return create_mock_aqi_data()
    except Exception as e:
        print(f"✗ 獲取AQI資料失敗: {e}")
        print("🔄 使用模擬AQI資料進行測試...")
        return create_mock_aqi_data()

def apply_scenario_injection(aqi_df):
    """應用情境注入，將大寮和林園測站的AQI值拉高到150"""
    print("🚨 情境注入：將大寮和林園測站的AQI值拉高到150...")
    
    # 檢查是否有這些測站
    original_daliao = aqi_df.loc[aqi_df['sitename'] == '大寮', 'aqi'].values
    original_linyuan = aqi_df.loc[aqi_df['sitename'] == '林園', 'aqi'].values
    
    # 應用情境注入
    aqi_df.loc[aqi_df['sitename'] == '大寮', 'aqi'] = 150
    aqi_df.loc[aqi_df['sitename'] == '林園', 'aqi'] = 150
    
    # 確認修改
    modified_stations = aqi_df[aqi_df['sitename'].isin(['大寮', '林園'])]
    for _, station in modified_stations.iterrows():
        original_aqi = original_daliao[0] if station['sitename'] == '大寮' else original_linyuan[0] if len(original_linyuan) > 0 else 'N/A'
        print(f"   - {station['sitename']}: AQI {original_aqi} → 150 ({station['county']})")
    
    return aqi_df

def create_mock_aqi_data():
    """創建模擬AQI資料用於測試"""
    print("📊 創建模擬AQI資料...")
    
    # 台灣主要城市和測站資料
    mock_stations = [
        {'sitename': '台北', 'county': '臺北市', 'latitude': 25.0330, 'longitude': 121.5654, 'aqi': 45},
        {'sitename': '新北', 'county': '新北市', 'latitude': 25.0173, 'longitude': 121.4628, 'aqi': 52},
        {'sitename': '桃園', 'county': '桃園市', 'latitude': 24.9936, 'longitude': 121.3009, 'aqi': 38},
        {'sitename': '台中', 'county': '臺中市', 'latitude': 24.1477, 'longitude': 120.6736, 'aqi': 65},
        {'sitename': '台南', 'county': '臺南市', 'latitude': 22.9999, 'longitude': 120.2269, 'aqi': 48},
        {'sitename': '高雄', 'county': '高雄市', 'latitude': 22.6273, 'longitude': 120.3014, 'aqi': 72},
        {'sitename': '基隆', 'county': '基隆市', 'latitude': 25.1276, 'longitude': 121.7392, 'aqi': 41},
        {'sitename': '新竹', 'county': '新竹市', 'latitude': 24.8138, 'longitude': 120.9675, 'aqi': 35},
        {'sitename': '嘉義', 'county': '嘉義市', 'latitude': 23.4801, 'longitude': 120.4491, 'aqi': 42},
        {'sitename': '宜蘭', 'county': '宜蘭縣', 'latitude': 24.7578, 'longitude': 121.7601, 'aqi': 28},
        {'sitename': '花蓮', 'county': '花蓮縣', 'latitude': 23.8224, 'longitude': 121.4327, 'aqi': 25},
        {'sitename': '台東', 'county': '臺東縣', 'latitude': 22.7560, 'longitude': 121.1608, 'aqi': 22},
        {'sitename': '澎湖', 'county': '澎湖縣', 'latitude': 23.5697, 'longitude': 119.5813, 'aqi': 18},
        {'sitename': '金門', 'county': '金門縣', 'latitude': 24.4329, 'longitude': 118.3222, 'aqi': 20},
        {'sitename': '馬祖', 'county': '連江縣', 'latitude': 26.1619, 'longitude': 119.9495, 'aqi': 15},
        # 添加更多測站以覆蓋全台
        {'sitename': '板橋', 'county': '新北市', 'latitude': 25.0146, 'longitude': 121.4621, 'aqi': 55},
        {'sitename': '三重', 'county': '新北市', 'latitude': 25.0857, 'longitude': 121.4880, 'aqi': 58},
        {'sitename': '中和', 'county': '新北市', 'latitude': 25.0042, 'longitude': 121.4827, 'aqi': 51},
        {'sitename': '永和', 'county': '新北市', 'latitude': 25.0079, 'longitude': 121.5132, 'aqi': 49},
        {'sitename': '新莊', 'county': '新北市', 'latitude': 25.0329, 'longitude': 121.4569, 'aqi': 53},
        {'sitename': '樹林', 'county': '新北市', 'latitude': 25.0015, 'longitude': 121.4169, 'aqi': 46},
        {'sitename': '大寮', 'county': '高雄市', 'latitude': 22.6061, 'longitude': 120.3950, 'aqi': 150},  # 高風險測站
        {'sitename': '林園', 'county': '高雄市', 'latitude': 22.5019, 'longitude': 120.4167, 'aqi': 150},  # 高風險測站
        {'sitename': '鳳山', 'county': '高雄市', 'latitude': 22.6290, 'longitude': 120.3568, 'aqi': 85},
        {'sitename': '左營', 'county': '高雄市', 'latitude': 22.6900, 'longitude': 120.3014, 'aqi': 78},
        {'sitename': '楠梓', 'county': '高雄市', 'latitude': 22.7597, 'longitude': 120.3269, 'aqi': 68},
        {'sitename': '三民', 'county': '高雄市', 'latitude': 22.6477, 'longitude': 120.2998, 'aqi': 75},
        {'sitename': '前鎮', 'county': '高雄市', 'latitude': 22.5987, 'longitude': 120.3155, 'aqi': 82},
        {'sitename': '苓雅', 'county': '高雄市', 'latitude': 22.6312, 'longitude': 120.3014, 'aqi': 79},
        {'sitename': '小港', 'county': '高雄市', 'latitude': 22.5665, 'longitude': 120.3562, 'aqi': 88},
    ]
    
    # 為每個測站添加更多詳細資訊
    for station in mock_stations:
        station.update({
            'pm25': station['aqi'] * 0.7 if station['aqi'] > 50 else station['aqi'] * 0.5,
            'pm10': station['aqi'] * 1.2 if station['aqi'] > 50 else station['aqi'] * 0.8,
            'o3': station['aqi'] * 0.3,
            'no2': station['aqi'] * 0.2,
            'so2': station['aqi'] * 0.1,
            'co': station['aqi'] * 0.05,
            'publishtime': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            'pollutant': 'PM2.5' if station['aqi'] > 50 else 'O3',
            'status': '普通' if station['aqi'] <= 100 else '不健康'
        })
    
    aqi_df = pd.DataFrame(mock_stations)
    print(f"✅ 創建 {len(aqi_df)} 筆模擬AQI測站資料")
    
    return aqi_df

# ==================== AQI分析 ====================
def get_nearby_aqi_info(shelter_lat, shelter_lon, aqi_df, max_distance=50):
    """獲取避難所周圍的AQI資訊 (50公里範圍，確保無遺漏)"""
    nearby_stations = []
    
    for _, aqi_row in aqi_df.iterrows():
        if pd.isna(aqi_row['latitude']) or pd.isna(aqi_row['longitude']):
            continue
            
        distance = haversine_distance(
            shelter_lat, shelter_lon,
            aqi_row['latitude'], aqi_row['longitude']
        )
        
        if distance <= max_distance:
            aqi_value = aqi_row['aqi']
            if pd.isna(aqi_value) or aqi_value == '':
                aqi_value = 0
            
            weight = 1 / (1 + distance)  # 距離越近權重越高
            nearby_stations.append({
                'sitename': aqi_row['sitename'],
                'aqi': aqi_value,
                'distance': distance,
                'weight': weight,
                'county': aqi_row['county']
            })
    
    if not nearby_stations:
        return None
    
    # 計算加權平均AQI
    total_weight = sum(station['weight'] for station in nearby_stations)
    weighted_aqi = sum(station['aqi'] * station['weight'] for station in nearby_stations) / total_weight
    
    # 找到最近的測站
    nearest_station = min(nearby_stations, key=lambda x: x['distance'])
    
    return {
        'weighted_aqi': weighted_aqi,
        'nearest_station': nearest_station,
        'station_count': len(nearby_stations),
        'nearby_stations': nearby_stations
    }

def assess_risk_level(aqi_value):
    """評估風險等級"""
    if pd.isna(aqi_value) or aqi_value == 0:
        return "無資料"
    elif aqi_value <= 50:
        return "低風險"
    elif aqi_value <= 100:
        return "中等風險"
    else:
        return "高風險"

def analyze_shelter_aqi(shelter_df, aqi_df):
    """分析避難所的AQI狀況"""
    print("📊 開始AQI分析...")
    
    results = []
    
    for idx, shelter in shelter_df.iterrows():
        shelter_lat = shelter['緯度']
        shelter_lon = shelter['經度']
        shelter_name = shelter['避難收容處所名稱']
        
        # 獲取周圍AQI資訊
        aqi_info = get_nearby_aqi_info(shelter_lat, shelter_lon, aqi_df)
        
        if aqi_info:
            result = {
                '避難收容處所名稱': shelter_name,
                '避難收容處所地址': shelter['避難收容處所地址'],
                '經度': shelter_lon,
                '緯度': shelter_lat,
                '室內室外': shelter['室內室外'],
                '可容納人數': shelter['預計收容人數'],
                '最近測站ID': aqi_info['nearest_station']['sitename'],
                '最近測站名稱': aqi_info['nearest_station']['sitename'],
                '最近測站位置': f"({aqi_info['nearest_station']['county']})",
                '周圍空氣污染指數': round(aqi_info['weighted_aqi'], 2),
                '風險等級': assess_risk_level(aqi_info['weighted_aqi']),
                '最近測站距離(km)': round(aqi_info['nearest_station']['distance'], 2),
                '影響測站數量': aqi_info['station_count']
            }
        else:
            result = {
                '避難收容處所名稱': shelter_name,
                '避難收容處所地址': shelter['避難收容處所地址'],
                '經度': shelter_lon,
                '緯度': shelter_lat,
                '室內室外': shelter['室內室外'],
                '可容納人數': shelter['預計收容人數'],
                '最近測站ID': '無',
                '最近測站名稱': '無',
                '最近測站位置': '無',
                '周圍空氣污染指數': '無',
                '風險等級': '無資料',
                '最近測站距離(km)': '無',
                '影響測站數量': 0
            }
        
        results.append(result)
        
        # 進度顯示
        if (idx + 1) % 1000 == 0:
            print(f"  已處理 {idx + 1}/{len(shelter_df)} 個避難所...")
    
    return pd.DataFrame(results)

# ==================== 雙圖層地圖生成 ====================
def create_dual_layer_map(shelter_df, aqi_df):
    """建立雙圖層地圖：AQI測站 + 避難收容所（參考dual_layer_map.py寫法）"""
    print("🗺️ 生成雙圖層地圖...")
    
    # 計算中心點
    center_lat = shelter_df['緯度'].mean()
    center_lon = shelter_df['經度'].mean()
    
    # 建立地圖
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # === 圖層 A: AQI 測站 ===
    aqi_layer = folium.FeatureGroup(name="圖層 A: AQI 測站", show=True)
    
    def get_aqi_color(aqi):
        """根據 AQI 值返回顏色"""
        if pd.isna(aqi) or aqi == '':
            return '#808080'  # 灰色
        elif aqi <= 50:
            return '#00FF00'  # 綠色 - 良好
        elif aqi <= 100:
            return '#FFFF00'  # 黃色 - 普通
        else:
            return '#FF0000'  # 紅色 - 不健康
    
    def get_aqi_status(aqi):
        if pd.isna(aqi):
            return '無資料'
        elif aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '普通'
        else:
            return '不健康'
    
    # 清理 AQI 數據
    aqi_clean = aqi_df.dropna(subset=['aqi', 'latitude', 'longitude']).copy()
    
    # 添加 AQI 測站
    for _, row in aqi_clean.iterrows():
        aqi_value = row['aqi']
        color = get_aqi_color(aqi_value)
        
        # 根據污染程度調整圓形大小
        if aqi_value > 100:
            radius = 8000
            weight = 3
        elif aqi_value > 50:
            radius = 6000
            weight = 2
        else:
            radius = 4000
            weight = 1
        
        # 創建彈窗內容
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <div style="background: {color}; color: black; padding: 8px; border-radius: 4px; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 14px;">{row['sitename']}</h3>
                <div style="font-size: 12px;">
                    <strong>AQI:</strong> {aqi_value}<br>
                    <strong>狀態:</strong> {get_aqi_status(aqi_value)}<br>
                    <strong>縣市:</strong> {row['county']}
                </div>
            </div>
        </div>
        """
        
        folium.Circle(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_content, max_width=250),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.4,
            weight=weight,
            tooltip=f"{row['sitename']} - AQI: {aqi_value}"
        ).add_to(aqi_layer)
    
    aqi_layer.add_to(m)
    
    # === 圖層 B: 避難收容所 ===
    shelter_layer = folium.FeatureGroup(name="圖層 B: 避難收容所", show=True)
    
    # 分離室內外避難所
    indoor_shelters = shelter_df[shelter_df['室內室外'] == True]
    outdoor_shelters = shelter_df[shelter_df['室內室外'] == False]
    
    print(f"室內避難所: {len(indoor_shelters)} 個")
    print(f"室外避難所: {len(outdoor_shelters)} 個")
    
    # 添加室內避難所 (藍色小圓點)
    for _, shelter in indoor_shelters.iterrows():
        # 獲取周圍空氣品質資訊
        aqi_info = get_nearby_aqi_info(shelter['緯度'], shelter['經度'], aqi_clean)
        
        # 根據空氣品質決定彈窗背景色
        if aqi_info:
            avg_aqi = aqi_info['weighted_aqi']
            if avg_aqi <= 50:
                bg_color = '#e8f5e8'  # 淺綠色
                risk_level = "低風險"
            elif avg_aqi <= 100:
                bg_color = '#fff3cd'  # 淺黃色
                risk_level = "中等風險"
            else:
                bg_color = '#ffb3ba'  # 淺紅色
                risk_level = "高風險"
        else:
            bg_color = '#e8f5e8'  # 淺綠色
            risk_level = "無資料"
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; min-width: 280px;">
            <!-- 基本資訊區塊 -->
            <div style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #1976d2;">
                <h3 style="margin: 0 0 8px 0; color: #1976d2; font-size: 16px;">🏢 {shelter['避難收容處所名稱']}</h3>
                <div style="font-size: 13px; line-height: 1.5;">
                    <strong>類型:</strong> 室內<br>
                    <strong>地址:</strong> {shelter['避難收容處所地址']}<br>
                    <strong>收容人數:</strong> {shelter['預計收容人數']}
                </div>
            </div>
        """
        
        # 如果有空氣品質資訊，添加到彈窗
        if aqi_info:
            # 根據平均AQI決定空氣品質彈窗的背景色
            avg_aqi = aqi_info['weighted_aqi']
            if avg_aqi <= 50:
                aqi_bg_color = '#e8f5e8'  # 淺綠色 - 對應良好AQI
                aqi_border_color = '#4caf50'  # 綠色邊框
            elif avg_aqi <= 100:
                aqi_bg_color = '#fff3cd'  # 淺黃色 - 對應普通AQI
                aqi_border_color = '#ffc107'  # 黃色邊框
            else:
                aqi_bg_color = '#ffb3ba'  # 淺紅色 - 對應不健康AQI
                aqi_border_color = '#dc3545'  # 紅色邊框
            
            popup_content += f"""
            <div style="background: {aqi_bg_color}; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid {aqi_border_color};">
                <h4 style="margin: 0; color: #000000; font-size: 14px;">🌍 周圍空氣品質影響</h4>
                <div style="font-size: 12px;">
                    <strong>平均 AQI:</strong> {aqi_info['weighted_aqi']:.1f}<br>
                    <strong>風險程度:</strong> <span style="color: {'green' if aqi_info['weighted_aqi'] <= 50 else 'orange' if aqi_info['weighted_aqi'] <= 100 else 'red'};">{risk_level}</span><br>
                    <strong>最近測站:</strong> {aqi_info['nearest_station']['sitename']}<br>
                    <strong>測站 AQI:</strong> {aqi_info['nearest_station']['aqi']}<br>
                    <strong>距離:</strong> {aqi_info['nearest_station']['distance']:.1f} 公里<br>
                    <strong>監測站數量:</strong> {aqi_info['station_count']} 個
                </div>
            </div>
            """
        
        popup_content += """
        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 11px; text-align: center;">
            <strong>💡 提示:</strong> 點擊 AQI 圓形查看詳細空氣品質資訊
        </div>
        </div>
        """
        
        folium.Circle(
            location=[shelter['緯度'], shelter['經度']],
            radius=499,  # 縮小1px
            popup=folium.Popup(popup_content, max_width=300),
            color='#1976d2',  # 深藍色邊框
            fill=True,
            fill_color='#4285f4',  # 藍色填充
            fill_opacity=0.8,
            weight=2,
            tooltip=f"室內: {shelter['避難收容處所名稱']} (點擊查看空氣品質影響)"
        ).add_to(shelter_layer)
    
    # 添加室外避難所 (綠色小圓點)
    for _, shelter in outdoor_shelters.iterrows():
        # 獲取周圍空氣品質資訊
        aqi_info = get_nearby_aqi_info(shelter['緯度'], shelter['經度'], aqi_clean)
        
        # 根據空氣品質決定彈窗背景色
        if aqi_info:
            avg_aqi = aqi_info['weighted_aqi']
            if avg_aqi <= 50:
                bg_color = '#e8f5e8'  # 淺綠色
                risk_level = "低風險"
            elif avg_aqi <= 100:
                bg_color = '#fff3cd'  # 淺黃色
                risk_level = "中等風險"
            else:
                bg_color = '#ffb3ba'  # 淺紅色
                risk_level = "高風險"
        else:
            bg_color = '#f8f9fa'
            risk_level = "無資料"
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; min-width: 280px;">
            <!-- 基本資訊區塊 -->
            <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #6c757d;">
                <h3 style="margin: 0 0 8px 0; color: #6c757d; font-size: 16px;">🌳 {shelter['避難收容處所名稱']}</h3>
                <div style="font-size: 13px; line-height: 1.5;">
                    <strong>類型:</strong> 室外<br>
                    <strong>地址:</strong> {shelter['避難收容處所地址']}<br>
                    <strong>收容人數:</strong> {shelter['預計收容人數']}
                </div>
            </div>
        """
        
        # 如果有空氣品質資訊，添加到彈窗
        if aqi_info:
            # 根據平均AQI決定空氣品質彈窗的背景色
            avg_aqi = aqi_info['weighted_aqi']
            if avg_aqi <= 50:
                aqi_bg_color = '#e8f5e8'  # 淺綠色 - 對應良好AQI
                aqi_border_color = '#4caf50'  # 綠色邊框
            elif avg_aqi <= 100:
                aqi_bg_color = '#fff3cd'  # 淺黃色 - 對應普通AQI
                aqi_border_color = '#ffc107'  # 黃色邊框
            else:
                aqi_bg_color = '#ffb3ba'  # 淺紅色 - 對應不健康AQI
                aqi_border_color = '#dc3545'  # 紅色邊框
            
            popup_content += f"""
            <div style="background: {aqi_bg_color}; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid {aqi_border_color};">
                <h4 style="margin: 0; color: #000000; font-size: 14px;">🌍 周圍空氣品質影響</h4>
                <div style="font-size: 12px;">
                    <strong>平均 AQI:</strong> {aqi_info['weighted_aqi']:.1f}<br>
                    <strong>風險程度:</strong> <span style="color: {'green' if aqi_info['weighted_aqi'] <= 50 else 'orange' if aqi_info['weighted_aqi'] <= 100 else 'red'};">{risk_level}</span><br>
                    <strong>最近測站:</strong> {aqi_info['nearest_station']['sitename']}<br>
                    <strong>測站 AQI:</strong> {aqi_info['nearest_station']['aqi']}<br>
                    <strong>距離:</strong> {aqi_info['nearest_station']['distance']:.1f} 公里<br>
                    <strong>監測站數量:</strong> {aqi_info['station_count']} 個
                </div>
            </div>
            """
        
        popup_content += """
        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 11px; text-align: center;">
            <strong>⚠️ 室外避難所注意:</strong> 空氣品質不佳時，請考慮室內替代方案
        </div>
        </div>
        """
        
        folium.Circle(
            location=[shelter['緯度'], shelter['經度']],
            radius=499,  # 縮小1px
            popup=folium.Popup(popup_content, max_width=300),
            color='#6c757d',  # 深灰色邊框
            fill=True,
            fill_color='#adb5bd',  # 淺灰色填充
            fill_opacity=0.8,
            weight=2,
            tooltip=f"室外: {shelter['避難收容處所名稱']} (點擊查看空氣品質影響)"
        ).add_to(shelter_layer)
    
    shelter_layer.add_to(m)
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 300px; height: 400px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:11px; padding: 12px; font-family: Arial, sans-serif; 
                overflow-y: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
    
    <h4 style="margin: 0 0 12px 0; color: #333; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px;">🗺️ 地圖圖例</h4>
    
    <div style="margin-bottom: 15px;">
        <h5 style="margin: 0 0 8px 0; color: #666; font-size: 12px;"> 圖層 A: AQI 測站</h5>
        <div style="display: grid; grid-template-columns: 1fr; gap: 4px;">
            <p style="margin: 2px 0; padding: 4px; background: #f8f9fa; border-radius: 3px; font-size: 11px;">
                <span style="display:inline-block;width:12px;height:12px;background-color:#00FF00;border-radius:50%;margin-right:6px;vertical-align:middle;"></span> 
                🟢 良好 (0-50)
            </p>
            <p style="margin: 2px 0; padding: 4px; background: #f8f9fa; border-radius: 3px; font-size: 11px;">
                <span style="display:inline-block;width:12px;height:12px;background-color:#FFFF00;border-radius:50%;margin-right:6px;vertical-align:middle;"></span> 
                🟡 普通 (51-100)
            </p>
            <p style="margin: 2px 0; padding: 4px; background: #f8f9fa; border-radius: 3px; font-size: 11px;">
                <span style="display:inline-block;width:12px;height:12px;background-color:#FF0000;border-radius:50%;margin-right:6px;vertical-align:middle;"></span> 
                🔴 不健康 (101+)
            </p>
        </div>
    </div>
    
    <div style="margin-bottom: 15px;">
        <h5 style="margin: 0 0 8px 0; color: #666; font-size: 12px;"> 圖層 B: 避難收容所</h5>
        <div style="display: grid; grid-template-columns: 1fr; gap: 4px;">
            <p style="margin: 2px 0; padding: 4px; background: #f8f9fa; border-radius: 3px; font-size: 11px;">
                <span style="display:inline-block;width:12px;height:12px;background-color:#4285f4;border-radius:50%;margin-right:6px;vertical-align:middle;"></span> 
                🏢 室內避難所 (藍色圓點)
            </p>
            <p style="margin: 2px 0; padding: 4px; background: #f8f9fa; border-radius: 3px; font-size: 11px;">
                <span style="display:inline-block;width:12px;height:12px;background-color:#adb5bd;border-radius:50%;margin-right:6px;vertical-align:middle;"></span> 
                🌳 室外避難所 (淺灰色圓點)
            </p>
        </div>
    </div>
    
    <div style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-radius: 6px; font-size: 10px; border-left: 4px solid #1976d2;">
        <h6 style="margin: 0 0 6px 0; color: #1976d2; font-size: 11px;">💡 使用提示</h6>
        <div style="line-height: 1.4;">
            • 點擊圓形查看 AQI 詳情<br>
            • 點擊避難所查看空氣品質影響<br>
            • 右上角可切換圖層顯示<br>
            • 圓形大小 = 污染嚴重程度
        </div>
    </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 添加圖層控制
    folium.LayerControl().add_to(m)
    
    # 添加全螢幕功能
    plugins.Fullscreen().add_to(m)
    
    # 保存地圖
    output_path = 'outputs/dual_layer_map.html'
    m.save(output_path)
    
    # 獲取檔案大小
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ 雙圖層地圖已儲存: {output_path} ({file_size_mb:.2f} MB)")
    
    return output_path

# ==================== 統計報告 ====================
def generate_statistics_report(shelter_analysis, shelter_count):
    """生成統計報告"""
    print("📊 生成統計報告...")
    
    # 風險評估統計
    risk_stats = shelter_analysis['風險等級'].value_counts()
    total_shelters = len(shelter_analysis)
    
    # 室內外統計
    indoor_outdoor_stats = shelter_analysis['室內室外'].value_counts()
    
    print("\n" + "="*50)
    print("📊 AQI分析統計報告")
    print("="*50)
    print(f"📊 總避難所: {shelter_count} 個")
    print(f"✅ 有AQI資料: {total_shelters} 個")
    
    print("\n🔍 風險分佈:")
    for risk_level, count in risk_stats.items():
        percentage = (count / shelter_count) * 100
        print(f"  {risk_level}: {count} 個 ({percentage:.1f}%)")
    
    print("\n🏢 室內外分佈:")
    for shelter_type, count in indoor_outdoor_stats.items():
        type_name = "室內" if shelter_type else "室外"
        percentage = (count / shelter_count) * 100
        print(f"  {type_name}避難所: {count} 個 ({percentage:.1f}%)")
    
    print("\n🚨 高風險避難所:")
    high_risk = shelter_analysis[shelter_analysis['風險等級'] == '高風險']
    if not high_risk.empty:
        for _, shelter in high_risk.head(5).iterrows():
            print(f"  - {shelter['避難收容處所名稱']}: AQI {shelter['周圍空氣污染指數']}")
    
    print("\n" + "="*50)
    print("� 資料來源說明")
    print("="*50)
    print(f"📄 避難所資料: data/shelters_cleaned.csv ({shelter_count} 個)")
    print(f"🌐 AQI資料: 環境部API ({len(shelter_analysis)} 個有資料)")
    print("="*50)

# ==================== 主程式 ====================
def main():
    """主執行程式"""
    print("🌍 AQI分析與雙圖層地圖系統 - 整合版")
    print("="*50)
    print("開始執行完整分析流程...")
    
    # 1. 讀取避難所資料
    print("\n📁 讀取避難所資料...")
    try:
        shelter_df = pd.read_csv('data/shelters_cleaned.csv')
        print(f"✅ 成功讀取避難所資料: {len(shelter_df)} 筆記錄")
    except FileNotFoundError:
        print("❌ 找不到 data/shelters_cleaned.csv 檔案")
        print("請確認檔案存在於 data/ 目錄中")
        return
    
    # 2. 室內外分類
    print("\n🏢 進行室內外分類...")
    shelter_df['室內室外'] = shelter_df.apply(
        lambda row: classify_shelter_type(
            row['避難收容處所名稱'], 
            row.get('室內'), 
            row.get('室外')
        ), 
        axis=1
    )
    
    indoor_count = shelter_df['室內室外'].sum()
    outdoor_count = len(shelter_df) - indoor_count
    print(f"🏢 室內避難所: {indoor_count} 個")
    print(f"🌳 室外避難所: {outdoor_count} 個")
    
    # 3. 直接使用全部避難所資料（不進行空間審計過濾）
    print("\n� 使用避難所資料...")
    cleaned_shelters = shelter_df.copy()
    print(f"✅ 使用全部避難所: {len(cleaned_shelters)} 個")
    
    # 4. 獲取AQI資料
    print("\n🌐 獲取AQI資料...")
    aqi_df = fetch_aqi_data()
    if aqi_df is None:
        print("❌ 無法獲取AQI資料，程式終止")
        return
    
    # 5. 應用情境注入
    aqi_df = apply_scenario_injection(aqi_df)
    
    # 6. AQI分析
    print("\n📊 進行AQI分析...")
    shelter_analysis = analyze_shelter_aqi(cleaned_shelters, aqi_df)
    
    # 6. 保存分析結果
    print("\n💾 保存分析結果...")
    output_file = 'outputs/shelter_aqi_analysis.csv'
    shelter_analysis.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ AQI分析結果已保存: {output_file}")
    
    # 7. 生成雙圖層地圖
    print("\n🗺️ 生成雙圖層地圖...")
    map_file = create_dual_layer_map(cleaned_shelters, aqi_df)
    
    # 8. 生成統計報告
    print("\n📊 生成統計報告...")
    generate_statistics_report(shelter_analysis, len(cleaned_shelters))
    
    # 9. 完成提示
    print("\n" + "="*50)
    print("🎉 分析完成！")
    print("="*50)
    print(f"📊 分析結果: {output_file}")
    print(f"🗺️ 雙圖層地圖: {map_file}")
    print(f"📈 統計報告: 已顯示於上方")
    print("\n💡 使用提示:")
    print("  - 在瀏覽器中開啟 dual_layer_map.html 查看互動地圖")
    print("  - 使用 Excel 開啟 shelter_aqi_analysis.csv 查看詳細分析")
    print("  - 地圖右上角可切換圖層顯示")
    print("  - 點擊地圖上的標記查看詳細資訊")
    print("="*50)

if __name__ == "__main__":
    main()
