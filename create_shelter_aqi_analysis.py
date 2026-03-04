import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩點之間的距離（公里）"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球半徑（公里）
    return c * r

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
        'avg_aqi': weighted_aqi,
        'station_count': len(nearby_stations),
        'nearest_station': nearest_station,
        'nearest_distance': nearest_station['distance']
    }

def get_risk_level(aqi):
    """根據AQI值判斷風險程度"""
    if pd.isna(aqi) or aqi == '':
        return '未知'
    elif aqi <= 50:
        return '低風險'
    elif aqi <= 100:
        return '中等風險'
    else:
        return '高風險'

def create_shelter_aqi_analysis():
    """創建避難所空氣品質分析CSV (50公里範圍)"""
    
    print("開始創建 shelter_aqi_analysis.csv (50公里範圍)...")
    
    # 讀取資料
    try:
        shelter_df = pd.read_csv('data/shelters_cleaned.csv')
        print(f"✓ 成功讀取避難所資料: {len(shelter_df)} 筆記錄")
    except FileNotFoundError:
        print("✗ 找不到 shelters_cleaned.csv 檔案")
        return False
    
    try:
        aqi_df = pd.read_csv('data/aqi_report.csv')
        print(f"✓ 成功讀取 AQI 數據: {len(aqi_df)} 筆測站")
        
        # 情境注入：將大寮和林園測站的AQI值強行拉高到150
        print("🚨 情境注入：將大寮和林園測站的AQI值拉高到150...")
        aqi_df.loc[aqi_df['sitename'] == '大寮', 'aqi'] = 150
        aqi_df.loc[aqi_df['sitename'] == '林園', 'aqi'] = 150
        
        # 確認修改
        modified_stations = aqi_df[aqi_df['sitename'].isin(['大寮', '林園'])]
        for _, station in modified_stations.iterrows():
            print(f"   - {station['sitename']}: AQI {station['aqi']} ({station['county']})")
        
    except FileNotFoundError:
        print("✗ 找不到 AQI 數據檔案")
        return False
    
    # 分析結果
    analysis_results = []
    
    print("開始分析避難所周圍空氣品質 (50公里範圍)...")
    
    for idx, shelter in shelter_df.iterrows():
        shelter_name = shelter['避難收容處所名稱']
        shelter_lat = shelter['緯度']
        shelter_lon = shelter['經度']
        shelter_type = '室內' if shelter['is_indoor'] else '室外'
        shelter_location = f"{shelter.get('縣市及鄉鎮市區', '未知')}"
        
        # 獲取周圍AQI資訊 (50公里範圍)
        aqi_info = get_nearby_aqi_info(shelter_lat, shelter_lon, aqi_df)
        
        if aqi_info:
            avg_aqi = aqi_info['avg_aqi']
            risk_level = get_risk_level(avg_aqi)
            nearest_station = aqi_info['nearest_station']
            
            analysis_results.append({
                '測站序號': idx + 1,
                '測站名稱': shelter_name,
                '測站位置': shelter_location,
                '室內室外': shelter_type,
                '經度': shelter_lon,
                '緯度': shelter_lat,
                '周圍空汙指數': round(avg_aqi, 2),
                '風險程度': risk_level,
                '最近測站': nearest_station['sitename'],
                '測站距離': round(nearest_station['distance'], 2),
                '監測站數量': aqi_info['station_count']
            })
        else:
            analysis_results.append({
                '測站序號': idx + 1,
                '測站名稱': shelter_name,
                '測站位置': shelter_location,
                '室內室外': shelter_type,
                '經度': shelter_lon,
                '緯度': shelter_lat,
                '周圍空汙指數': '無資料',
                '風險程度': '未知',
                '最近測站': '無',
                '測站距離': '無',
                '監測站數量': 0
            })
        
        if (idx + 1) % 1000 == 0:
            print(f"已處理 {idx + 1}/{len(shelter_df)} 個避難所...")
    
    # 創建DataFrame
    analysis_df = pd.DataFrame(analysis_results)
    
    # 保存到CSV
    output_file = 'outputs/shelter_aqi_analysis.csv'
    analysis_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✓ 已保存分析結果: {output_file}")
    
    # 統計資訊
    print(f"\n📊 分析統計 (50公里範圍):")
    print(f"   總避難所數量: {len(analysis_df)} 個")
    print(f"   有AQI資料: {len(analysis_df[analysis_df['周圍空汙指數'] != '無資料'])} 個")
    print(f"   無AQI資料: {len(analysis_df[analysis_df['周圍空汙指數'] == '無資料'])} 個")
    
    # 風險程度統計
    risk_stats = analysis_df[analysis_df['風險程度'] != '未知']['風險程度'].value_counts()
    print(f"\n🎯 風險程度分佈:")
    for risk, count in risk_stats.items():
        print(f"   {risk}: {count} 個")
    
    # 監測站數量統計
    station_stats = analysis_df[analysis_df['監測站數量'] > 0]['監測站數量'].value_counts().sort_index()
    print(f"\n📡 監測站數量分佈:")
    for count, frequency in station_stats.head(10).items():
        print(f"   {count} 個測站: {frequency} 個避難所")
    
    # 室內室外統計
    type_stats = analysis_df['室內室外'].value_counts()
    print(f"\n🏢 避難所類型分佈:")
    for shelter_type, count in type_stats.items():
        print(f"   {shelter_type}: {count} 個")
    
    # 高風險避難所詳細資訊
    high_risk_shelters = analysis_df[analysis_df['風險程度'] == '高風險']
    if len(high_risk_shelters) > 0:
        print(f"\n🚨 高風險避難所 ({len(high_risk_shelters)} 個):")
        for _, shelter in high_risk_shelters.head(10).iterrows():
            print(f"   - {shelter['測站名稱']}: AQI {shelter['周圍空汙指數']}, 最近測站 {shelter['最近測站']} ({shelter['測站距離']}km)")
        if len(high_risk_shelters) > 10:
            print(f"   ... 還有 {len(high_risk_shelters) - 10} 個")
    
    return True

if __name__ == "__main__":
    create_shelter_aqi_analysis()
