import pandas as pd
import folium
import numpy as np
from folium import plugins

def get_nearby_aqi_info(shelter_lat, shelter_lon, aqi_data, max_distance=0.1):
    """獲取避難所周圍的空氣品質資訊"""
    nearby_stations = []
    for _, station in aqi_data.iterrows():
        if pd.notna(station['latitude']) and pd.notna(station['longitude']):
            distance = np.sqrt(
                (shelter_lat - station['latitude'])**2 + 
                (shelter_lon - station['longitude'])**2
            )
            if distance <= max_distance:
                nearby_stations.append({
                    'station': station,
                    'distance': distance
                })
    
    if not nearby_stations:
        return None
    
    # 計算加權平均 AQI（距離越近權重越高）
    total_weight = 0
    weighted_aqi = 0
    for station_info in nearby_stations:
        weight = 1 / (station_info['distance'] + 0.01)  # 避免除零
        weighted_aqi += station_info['station']['aqi'] * weight
        total_weight += weight
    
    avg_aqi = weighted_aqi / total_weight
    
    # 找出最近的測站
    nearest_station = min(nearby_stations, key=lambda x: x['distance'])
    
    return {
        'avg_aqi': avg_aqi,
        'nearest_station': nearest_station['station'],
        'nearest_distance': nearest_station['distance'],
        'station_count': len(nearby_stations)
    }

def create_dual_layer_map():
    """建立雙圖層地圖：AQI 測站 + 避難收容所"""
    
    print("讀取資料...")
    
    # 讀取 AQI 數據
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
        return
    
    # 讀取避難所資料 (使用位置合理性檢查後的檔案)
    try:
        shelter_df = pd.read_csv('data/shelters_cleaned.csv')
        print(f"✓ 成功讀取避難所資料: {len(shelter_df)} 筆記錄")
    except FileNotFoundError:
        print("✗ 找不到 shelters_cleaned.csv 檔案")
        return None
    
    # shelter_with_correct_area.csv 已經是經過篩選的合理位置避難所
    valid_shelters = shelter_df.copy()
    print(f"✓ 合理位置避難所: {len(valid_shelters)} 個")
    
    # 過濾有效座標 (已經在位置合理性檢查中處理過)
    valid_shelters = valid_shelters[
        (valid_shelters['經度'].notna()) & 
        (valid_shelters['緯度'].notna()) &
        (valid_shelters['經度'] != 0) & 
        (valid_shelters['緯度'] != 0)
    ].copy()
    
    print(f"✓ 有效避難所: {len(valid_shelters)} 個")
    
    # 計算中心點
    center_lat = valid_shelters['緯度'].mean()
    center_lon = valid_shelters['經度'].mean()
    
    # 建立地圖
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # === 圖層 A: AQI 測站 ===
    aqi_layer = folium.FeatureGroup(name="圖層 A: AQI 測站", show=True)  # 預設開啟
    
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
                    <strong>狀態:</strong> {row['status']}<br>
                    <strong>縣市:</strong> {row['county']}
                </div>
            </div>
        </div>
        """
        
        # 添加圓形標記
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
    indoor_shelters = valid_shelters[valid_shelters['is_indoor'] == True]
    outdoor_shelters = valid_shelters[valid_shelters['is_indoor'] == False]
    
    print(f"室內避難所: {len(indoor_shelters)} 個")
    print(f"室外避難所: {len(outdoor_shelters)} 個")
    
    # 添加室內避難所 (藍色小圓點)
    for _, shelter in indoor_shelters.iterrows():
        # 獲取周圍空氣品質資訊
        aqi_info = get_nearby_aqi_info(shelter['緯度'], shelter['經度'], aqi_clean)
        
        # 根據空氣品質決定彈窗背景色
        if aqi_info:
            avg_aqi = aqi_info['avg_aqi']
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
                    <strong>收容人數:</strong> {shelter['預計收容人數']}<br>
                    <strong>適用災害:</strong> {shelter['適用災害類別']}
                </div>
            </div>
        """
        
        # 如果有空氣品質資訊，添加到彈窗
        if aqi_info:
            # 根據平均AQI決定空氣品質彈窗的背景色
            avg_aqi = aqi_info['avg_aqi']
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
                    <strong>平均 AQI:</strong> {aqi_info['avg_aqi']:.1f}<br>
                    <strong>風險程度:</strong> <span style="color: {'green' if aqi_info['avg_aqi'] <= 50 else 'orange' if aqi_info['avg_aqi'] <= 100 else 'red'};">{risk_level}</span><br>
                    <strong>最近測站:</strong> {aqi_info['nearest_station']['sitename']}<br>
                    <strong>測站 AQI:</strong> {aqi_info['nearest_station']['aqi']}<br>
                    <strong>距離:</strong> {aqi_info['nearest_distance']*111:.1f} 公里<br>
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
            avg_aqi = aqi_info['avg_aqi']
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
                    <strong>收容人數:</strong> {shelter['預計收容人數']}<br>
                    <strong>適用災害:</strong> {shelter['適用災害類別']}
                </div>
            </div>
        """
        
        # 如果有空氣品質資訊，添加到彈窗
        if aqi_info:
            # 根據平均AQI決定空氣品質彈窗的背景色
            avg_aqi = aqi_info['avg_aqi']
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
                    <strong>平均 AQI:</strong> {aqi_info['avg_aqi']:.1f}<br>
                    <strong>風險程度:</strong> <span style="color: {'green' if aqi_info['avg_aqi'] <= 50 else 'orange' if aqi_info['avg_aqi'] <= 100 else 'red'};">{risk_level}</span><br>
                    <strong>最近測站:</strong> {aqi_info['nearest_station']['sitename']}<br>
                    <strong>測站 AQI:</strong> {aqi_info['nearest_station']['aqi']}<br>
                    <strong>距離:</strong> {aqi_info['nearest_distance']*111:.1f} 公里<br>
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
    
    # 儲存地圖
    output_file = 'dual_layer_map.html'
    m.save(output_file)
    
    # 檢查檔案大小
    import os
    file_size = os.path.getsize(output_file)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\n✓ 雙圖層地圖已儲存: {output_file}")
    print(f"✓ 檔案大小: {file_size_mb:.2f} MB")
    
    # 生成統計報告
    generate_dual_layer_report(aqi_clean, indoor_shelters, outdoor_shelters)
    
    return m

def generate_dual_layer_report(aqi_data, indoor_shelters, outdoor_shelters):
    
    # AQI 統計
    aqi_stats = {
        '良好': len(aqi_data[aqi_data['aqi'] <= 50]),
        '中等': len(aqi_data[(aqi_data['aqi'] > 50) & (aqi_data['aqi'] <= 100)]),
        '對敏感群體不健康': len(aqi_data[(aqi_data['aqi'] > 100) & (aqi_data['aqi'] <= 150)]),
        '不健康': len(aqi_data[(aqi_data['aqi'] > 150) & (aqi_data['aqi'] <= 200)]),
        '非常不健康': len(aqi_data[aqi_data['aqi'] > 200])
    }
    
    # 找出污染最嚴重的測站
    worst_station = aqi_data.loc[aqi_data['aqi'].idxmax()]
    
    report = f"""
# 雙圖層地圖分析報告

## 🌍 圖層 A: AQI 測站分析

### AQI 分佈統計
"""
    
    for level, count in aqi_stats.items():
        percentage = (count / len(aqi_data)) * 100
        report += f"- **{level}**: {count} 個測站 ({percentage:.1f}%)\n"
    
    report += f"""
### 污染最嚴重測站
- **測站名稱**: {worst_station['sitename']}
- **所在縣市**: {worst_station['county']}
- **AQI 值**: {worst_station['aqi']}
- **狀態**: {worst_station['status']}
- **主要污染物**: {worst_station.get('pollutant', '無資料')}

## 🏢 圖層 B: 避難收容所分析

### 避難所類型統計
- **🏢 室內避難所**: {len(indoor_shelters)} 個 ({len(indoor_shelters)/(len(indoor_shelters)+len(outdoor_shelters))*100:.1f}%)
- **🌳 室外避難所**: {len(outdoor_shelters)} 個 ({len(outdoor_shelters)/(len(indoor_shelters)+len(outdoor_shelters))*100:.1f}%)
- **總計**: {len(indoor_shelters) + len(outdoor_shelters)} 個

### 室內避難所分佈
"""
    
    # 統計室內避難所的縣市分佈
    indoor_county_stats = indoor_shelters['縣市及鄉鎮市區'].value_counts().head(5)
    for county, count in indoor_county_stats.items():
        report += f"- **{county}**: {count} 個\n"
    
    report += f"""
### 室外避難所分佈
"""
    
    # 統計室外避難所的縣市分佈
    outdoor_county_stats = outdoor_shelters['縣市及鄉鎮市區'].value_counts().head(5)
    for county, count in outdoor_county_stats.items():
        report += f"- **{county}**: {count} 個\n"
    
    report += f"""

## 📊 地圖使用指南

### 如何觀察風險程度
1. **圓形顏色**: 綠色→黃色→橙色→紅色→紫色 (污染程度遞增)
2. **圓形大小**: 圓形越大 = AQI 值越高 = 污染越嚴重
3. **圖標區分**: 藍色房屋 = 室內避難所，綠色樹木 = 室外避難所
4. **圖層切換**: 右上角可獨立開關 AQI 或避難所圖層

### 重點觀察區域
- **🔴 高污染區**: 尋找紅色和紫色圓形集中的區域
- **🏢 室內避難所**: 藍色圓點，通常位於人口密集區
- **🌳 室外避難所**: 綠色圓點，通常位於郊區或公園
- **⚠️ 交集分析**: 同時開啟兩圖層觀察環境與避難所關聯

---
**報告生成時間**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析工具**: 雙圖層視覺化系統 v1.0
"""
    
    # 儲存報告
    with open('dual_layer_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ 雙圖層統計報告已儲存: dual_layer_report.md")

if __name__ == "__main__":
    print("開始建立雙圖層地圖...")
    create_dual_layer_map()
    print("雙圖層地圖建立完成！")
