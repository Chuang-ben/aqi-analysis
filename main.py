"""
環境部 AQI 數據取得與地圖視覺化程式
串接環境部 API (aqx_p_432) 獲取全台即時 AQI 數據，並用 folium 在地圖上標示所有測站位置
"""

import os
import sys
import subprocess
import json
import math
from pathlib import Path
from typing import List, Dict, Optional

import requests
from dotenv import load_dotenv

# 自動安裝必要的套件
def setup_packages():
    """自動檢查並安裝必要的 Python 套件"""
    required_packages = {
        'requests': 'requests',
        'dotenv': 'python-dotenv',
        'folium': 'folium',
        'pandas': 'pandas'
    }
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name} 已安裝")
        except ImportError:
            print(f"✗ 正在安裝 {package_name}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name, '-q'])
            print(f"✓ {package_name} 安裝完成")

# 執行套件設置
setup_packages()

import folium
import pandas as pd


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """使用 Haversine 公式計算兩點間的地理距離
    
    Args:
        lat1, lon1: 第一點的經緯度
        lat2, lon2: 第二點的經緯度（目標點）
        
    Returns:
        距离（公里）
    """
    R = 6371  # 地球平均半徑（公里）
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    
    return round(distance, 2)


class AQIDataFetcher:
    """環境部 AQI 數據取得類別"""
    
    BASE_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    
    def __init__(self, api_key: str):
        """初始化 API 取得器
        
        Args:
            api_key: 環境部 API Key
        """
        self.api_key = api_key
        self.session = requests.Session()
        
    def fetch_aqi_data(self, limit: int = 1000) -> Optional[List[Dict]]:
        """取得全台 AQI 數據
        
        Args:
            limit: 取得數據筆數上限
            
        Returns:
            AQI 數據列表，若失敗則返回 None
        """
        params = {
            'api_key': self.api_key,
            'limit': limit,
            'sort': 'ImportDate',
            'order': 'desc'
        }
        
        try:
            print("⏳ 正在取得環境部 AQI 數據...")
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
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
            
            print(f"✓ 成功取得 {len(records)} 筆測站數據")
            return records
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 網路請求失敗: {e}")
            return None
        except json.JSONDecodeError:
            print("✗ 無法解析 API 回應")
            return None
    
    def close(self):
        """關閉 session"""
        self.session.close()


class AQIMapVisualizer:
    """AQI 數據地圖視覺化類別"""
    
    # AQI 指標值（簡化三色系統）
    AQI_LEVELS = [
        (0, 50, '良好', '#2ecc71'),      # 綠色
        (51, 100, '普通', '#ffd700'),    # 黃色
        (101, 500, '不健康', '#ff4444')  # 紅色
    ]
    
    def __init__(self, output_dir: str = 'outputs'):
        """初始化地圖視覺化器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_aqi_level(self, aqi: float) -> tuple:
        """根據 AQI 值取得對應等級
        
        Args:
            aqi: AQI 值
            
        Returns:
            (等級名稱, 顏色) 的 tuple
        """
        try:
            aqi_val = float(aqi) if aqi else 0
        except (ValueError, TypeError):
            return '未知', '#95a5a6'
        
        for min_val, max_val, level, color in self.AQI_LEVELS:
            if min_val <= aqi_val <= max_val:
                return level, color
        
        return '危害', '#4b0082'
    
    def create_map(self, records: List[Dict], output_file: str = 'aqi_map.html') -> str:
        """根據 AQI 數據創建地圖
        
        Args:
            records: AQI 數據記錄列表
            output_file: 輸出檔案名稱
            
        Returns:
            輸出檔案路徑
        """
        # 篩選有效的測站數據（處理大小寫變化）
        valid_records = [
            r for r in records 
            if r.get('latitude') and r.get('longitude') and r.get('sitename')
        ]
        
        if not valid_records:
            print("✗ 沒有有效的測站數據")
            return None
        
        print(f"⏳ 正在創建地圖，共 {len(valid_records)} 個測站...")
        
        # 計算中心點（台灣中心大約是 23.5°N, 121°E）
        center_lat = 23.5
        center_lon = 121
        
        # 創建地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加測站標記
        for record in valid_records:
            try:
                lat = float(record['latitude'])
                lon = float(record['longitude'])
                site_name = record.get('sitename', '未知測站')
                county = record.get('county', '')
                aqi = record.get('aqi', 'N/A')
                
                level, color = self.get_aqi_level(aqi)
                
                # 創建簡潔的 popup 內容
                popup_text = f"""
                <div style="font-family: 微軟正黑體, sans-serif; width: 180px;">
                <p style="margin: 5px 0; font-size: 14px; font-weight: bold;">{site_name}</p>
                <p style="margin: 3px 0; font-size: 12px; color: #666;">{county}</p>
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">
                <p style="margin: 5px 0; font-size: 16px; font-weight: bold; color: {color};">AQI: {aqi}</p>
                <p style="margin: 3px 0; font-size: 12px;">{level}</p>
                </div>
                """
                
                # 添加圓形標記
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    popup=folium.Popup(popup_text, max_width=200),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.8,
                    weight=2,
                    tooltip=f"{site_name} - AQI: {aqi}"
                ).add_to(m)
                
            except (ValueError, TypeError) as e:
                print(f"⚠ 跳過無效數據: {record.get('SiteName', 'Unknown')} - {e}")
                continue
        
        # 添加簡潔圖例
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px;
                    background-color: white; border: 2px solid #333; z-index: 9999; 
                    font-size: 13px; padding: 12px; border-radius: 5px;
                    font-family: 微軟正黑體, sans-serif;">
        <p style="margin: 0 0 8px 0; font-weight: bold; text-align: center;">AQI 空氣品質等級</p>
        <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">
        <p style="margin: 5px 0;"><span style="background-color: #2ecc71; padding: 4px 10px; border-radius: 3px; font-weight: bold;">0-50</span> 良好</p>
        <p style="margin: 5px 0;"><span style="background-color: #ffd700; padding: 4px 10px; border-radius: 3px; font-weight: bold;">51-100</span> 普通</p>
        <p style="margin: 5px 0;"><span style="background-color: #ff4444; padding: 4px 10px; border-radius: 3px; font-weight: bold; color: white;">101+</span> 不健康</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 保存地圖
        output_path = self.output_dir / output_file
        m.save(str(output_path))
        print(f"✓ 地圖已保存: {output_path}")
        
        return str(output_path)
    
    def create_data_report(self, records: List[Dict], output_file: str = 'aqi_report.csv'):
        """創建 AQI 數據報告，包含距台北車站的距離
        
        Args:
            records: AQI 數據記錄列表
            output_file: 輸出檔案名稱
        """
        try:
            df = pd.DataFrame(records)
            
            # 台北車站座標
            taipei_station_lat = 25.0478
            taipei_station_lon = 121.5170
            
            # 計算距離
            df['距台北車站(公里)'] = df.apply(
                lambda row: calculate_distance(
                    float(row['latitude']), 
                    float(row['longitude']),
                    taipei_station_lat,
                    taipei_station_lon
                ) if pd.notna(row['latitude']) and pd.notna(row['longitude']) else None,
                axis=1
            )
            
            # 選擇重要欄位
            columns = ['sitename', 'county', 'aqi', 'pollutant', 'status', 'latitude', 'longitude', '距台北車站(公里)', 'publishtime']
            available_columns = [col for col in columns if col in df.columns]
            df_output = df[available_columns]
            
            # 按距離排序
            df_output = df_output.sort_values('距台北車站(公里)')
            
            output_path = self.output_dir / output_file
            df_output.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✓ 數據報告已保存: {output_path}")
            print(f"  最近測站: {df_output.iloc[0]['sitename']} ({df_output.iloc[0]['距台北車站(公里)']} 公里)")
            
        except Exception as e:
            print(f"⚠ 創建數據報告失敗: {e}")


def main():
    """主程式"""
    print("=" * 60)
    print("環境部 AQI 數據取得與地圖視覺化")
    print("=" * 60)
    
    # 加載環境變數
    load_dotenv()
    api_key = os.getenv('MOENV_API_KEY')
    
    if not api_key:
        print("✗ 錯誤: 未在 .env 檔案中找到 MOENV_API_KEY")
        print("  請在 .env 檔案中添加: MOENV_API_KEY=你的API金鑰")
        return
    
    # 取得數據
    fetcher = AQIDataFetcher(api_key)
    records = fetcher.fetch_aqi_data()
    fetcher.close()
    
    if not records:
        print("✗ 無法取得 AQI 數據")
        return
    
    # 視覺化
    visualizer = AQIMapVisualizer()
    
    # 創建地圖
    map_file = visualizer.create_map(records)
    
    # 創建報告
    visualizer.create_data_report(records)
    
    print("=" * 60)
    print("✓ 程式執行完成！")
    if map_file:
        print(f"  地圖位置: {map_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
