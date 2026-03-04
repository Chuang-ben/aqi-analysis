"""
Spatial Audit 工具
檢查座標是二度分帶（EPSG:3826）還是經緯度（EPSG:4326）
偵測位在台灣邊界外或為 (0,0) 的異常點位
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyproj import CRS, Transformer
import folium
from shapely.geometry import Point, Polygon
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

class SpatialAudit:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = None
        self.taiwan_bounds = {
            'min_lon': 118.0,  # 台灣最西邊界 (包含金門)
            'max_lon': 123.0,  # 台灣最東邊界
            'min_lat': 20.0,   # 台灣最南邊界 (包含南沙)
            'max_lat': 27.0    # 台灣最北邊界 (包含釣魚台)
        }
        
        # 台灣主要地區的精確邊界
        self.taiwan_regions = {
            'taiwan_north': {
                'min_lon': 120.1, 'max_lon': 122.4,
                'min_lat': 24.3, 'max_lat': 25.4
            },
            'taiwan_central': {
                'min_lon': 119.9, 'max_lon': 121.7,
                'min_lat': 23.2, 'max_lat': 24.5
            },
            'taiwan_south': {
                'min_lon': 119.5, 'max_lon': 121.5,
                'min_lat': 21.7, 'max_lat': 23.4
            },
            'penghu': {
                'min_lon': 119.2, 'max_lon': 119.8,
                'min_lat': 23.2, 'max_lat': 23.9
            },
            'kinmen': {
                'min_lon': 118.2, 'max_lon': 118.5,
                'min_lat': 24.2, 'max_lat': 24.6
            },
            'matsu': {
                'min_lon': 119.8, 'max_lon': 120.4,
                'min_lat': 25.8, 'max_lat': 26.4
            },
            'lanyu': {
                'min_lon': 121.48, 'max_lon': 121.62,
                'min_lat': 21.95, 'max_lat': 22.12
            }
        }
        
        # 台灣二度分帶範圍 (TWD97/EPSG:3826)
        self.twd97_bounds = {
            'min_x': 170000,   # 約台灣最西
            'max_x': 350000,   # 約台灣最東
            'min_y': 2400000,  # 約台灣最南
            'max_y': 2750000   # 約台灣最北
        }
        
    def is_in_taiwan_region(self, lon, lat):
        """判斷點位是否在台灣地區內"""
        # 檢查是否在任何一個台灣地區範圍內
        for region_name, bounds in self.taiwan_regions.items():
            if (bounds['min_lon'] <= lon <= bounds['max_lon'] and 
                bounds['min_lat'] <= lat <= bounds['max_lat']):
                return True, region_name
        
        return False, "unknown"
    
    def load_data(self):
        """載入 CSV 資料"""
        try:
            self.data = pd.read_csv(self.csv_file)
            print(f"✓ 成功載入資料: {len(self.data)} 筆記錄")
            print(f"資料欄位: {list(self.data.columns)}")
            return True
        except Exception as e:
            print(f"✗ 載入資料失敗: {e}")
            return False
    
    def detect_coordinate_system(self):
        """檢測座標系統"""
        print("\n=== 座標系統檢測 ===")
        
        # 假設欄位名稱
        lon_col = None
        lat_col = None
        
        # 嘗試常見的經緯度欄位名稱
        possible_lon_names = ['經度', 'lon', 'longitude', 'lng', 'X', 'x']
        possible_lat_names = ['緯度', 'lat', 'latitude', 'Y', 'y']
        
        for col in self.data.columns:
            if any(name.lower() in col.lower() for name in possible_lon_names):
                lon_col = col
            if any(name.lower() in col.lower() for name in possible_lat_names):
                lat_col = col
        
        if not lon_col or not lat_col:
            print("✗ 無法識別經緯度欄位")
            return None, None, "unknown"
        
        print(f"識別欄位: 經度='{lon_col}', 緯度='{lat_col}'")
        
        # 取樣本檢查座標範圍
        sample_lons = self.data[lon_col].dropna().head(100)
        sample_lats = self.data[lat_col].dropna().head(100)
        
        lon_min, lon_max = sample_lons.min(), sample_lons.max()
        lat_min, lat_max = sample_lats.min(), sample_lats.max()
        
        print(f"經度範圍: {lon_min:.3f} ~ {lon_max:.3f}")
        print(f"緯度範圍: {lat_min:.3f} ~ {lat_max:.3f}")
        
        # 判斷座標系統
        coordinate_system = "unknown"
        
        # 檢查是否為經緯度 (EPSG:4326)
        if (lon_min >= self.taiwan_bounds['min_lon'] and lon_max <= self.taiwan_bounds['max_lon'] and
            lat_min >= self.taiwan_bounds['min_lat'] and lat_max <= self.taiwan_bounds['max_lat']):
            coordinate_system = "EPSG:4326 (經緯度)"
            print("✓ 判斷為經緯度座標系統 (EPSG:4326)")
        
        # 檢查是否為二度分帶 (EPSG:3826)
        elif (lon_min >= self.twd97_bounds['min_x'] and lon_max <= self.twd97_bounds['max_x'] and
              lat_min >= self.twd97_bounds['min_y'] and lat_max <= self.twd97_bounds['max_y']):
            coordinate_system = "EPSG:3826 (二度分帶)"
            print("✓ 判斷為二度分帶座標系統 (EPSG:3826)")
        else:
            print("? 座標範圍不明確，需要進一步檢查")
            print(f"詳細範圍檢查:")
            print(f"  經度: {lon_min:.3f} ~ {lon_max:.3f} (台灣範圍: {self.taiwan_bounds['min_lon']} ~ {self.taiwan_bounds['max_lon']})")
            print(f"  緯度: {lat_min:.3f} ~ {lat_max:.3f} (台灣範圍: {self.taiwan_bounds['min_lat']} ~ {self.taiwan_bounds['max_lat']})")
            print(f"  二度分帶 X: {lon_min:.0f} ~ {lon_max:.0f} (台灣範圍: {self.twd97_bounds['min_x']} ~ {self.twd97_bounds['max_x']})")
            print(f"  二度分帶 Y: {lat_min:.0f} ~ {lat_max:.0f} (台灣範圍: {self.twd97_bounds['min_y']} ~ {self.twd97_bounds['max_y']})")
        
        return lon_col, lat_col, coordinate_system
    
    def detect_anomalies(self, lon_col, lat_col, coordinate_system):
        """偵測異常點"""
        print("\n=== 異常點偵測 ===")
        
        anomalies = {
            'zero_points': [],
            'out_of_bounds': [],
            'invalid_coordinates': [],
            'sea_points': []  # 新增：海上點位
        }
        
        region_stats = {}
        
        for idx, row in self.data.iterrows():
            try:
                lon = float(row[lon_col]) if pd.notna(row[lon_col]) else None
                lat = float(row[lat_col]) if pd.notna(row[lat_col]) else None
                
                if lon is None or lat is None:
                    continue
                
                # 檢查 (0,0) 點
                if abs(lon) < 0.001 and abs(lat) < 0.001:
                    anomalies['zero_points'].append({
                        'index': idx,
                        'lon': lon,
                        'lat': lat,
                        'reason': '原點 (0,0)'
                    })
                
                # 使用精確的台灣地區判斷
                is_in_taiwan, region = self.is_in_taiwan_region(lon, lat)
                
                if is_in_taiwan:
                    # 統計各地區的點數
                    region_stats[region] = region_stats.get(region, 0) + 1
                else:
                    # 檢查是否在台灣大邊界內但不在具體地區
                    if (self.taiwan_bounds['min_lon'] <= lon <= self.taiwan_bounds['max_lon'] and
                        self.taiwan_bounds['min_lat'] <= lat <= self.taiwan_bounds['max_lat']):
                        anomalies['sea_points'].append({
                            'index': idx,
                            'lon': lon,
                            'lat': lat,
                            'reason': f'台灣邊界內但不在陸地區域 ({lon:.3f}, {lat:.3f})'
                        })
                    else:
                        anomalies['out_of_bounds'].append({
                            'index': idx,
                            'lon': lon,
                            'lat': lat,
                            'reason': f'超出台灣邊界 ({lon:.3f}, {lat:.3f})'
                        })
                
                # 檢查無效座標
                if abs(lon) > 180 or abs(lat) > 90:
                    anomalies['invalid_coordinates'].append({
                        'index': idx,
                        'lon': lon,
                        'lat': lat,
                        'reason': f'無效座標範圍 ({lon:.3f}, {lat:.3f})'
                    })
                    
            except (ValueError, TypeError):
                continue
        
        # 輸出地區統計
        print("\n=== 地區分布統計 ===")
        for region, count in region_stats.items():
            region_names = {
                'taiwan_north': '台灣北部',
                'taiwan_central': '台灣中部',
                'taiwan_south': '台灣南部',
                'kinmen': '金門',
                'matsu': '馬祖',
                'penghu': '澎湖',
                'lanyu': '蘭嶼'
            }
            print(f"{region_names.get(region, region)}: {count} 個點")
        
        # 統計異常點
        print(f"\n原點 (0,0) 異常點: {len(anomalies['zero_points'])} 筆")
        print(f"海上點位: {len(anomalies['sea_points'])} 筆")
        print(f"邊界外異常點: {len(anomalies['out_of_bounds'])} 筆")
        print(f"無效座標異常點: {len(anomalies['invalid_coordinates'])} 筆")
        print(f"總異常點數量: {sum(len(v) for v in anomalies.values())} 筆")
        
        return anomalies
    
    def create_anomaly_map(self, lon_col, lat_col, coordinate_system, anomalies):
        """創建異常點地圖"""
        print("\n=== 創建異常點地圖 ===")
        
        # 計算地圖中心
        valid_points = self.data[(self.data[lon_col].notna()) & (self.data[lat_col].notna())]
        center_lat = valid_points[lat_col].median()
        center_lon = valid_points[lon_col].median()
        
        # 創建地圖
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
        
        # 添加正常點（綠色）
        for idx, row in valid_points.iterrows():
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=3,
                color='green',
                fill=True,
                popup=f"正常點 {idx}",
                opacity=0.6
            ).add_to(m)
        
        # 添加異常點（紅色和橙色）
        all_anomalies = (anomalies['zero_points'] + 
                       anomalies['out_of_bounds'] + 
                       anomalies['invalid_coordinates'])
        
        for anomaly in all_anomalies:
            folium.CircleMarker(
                location=[anomaly['lat'], anomaly['lon']],
                radius=5,
                color='red',
                fill=True,
                popup=f"異常點 {anomaly['index']}: {anomaly['reason']}",
                opacity=0.8
            ).add_to(m)
        
        # 添加海上點位（橙色）
        for sea_point in anomalies['sea_points']:
            folium.CircleMarker(
                location=[sea_point['lat'], sea_point['lon']],
                radius=5,
                color='orange',
                fill=True,
                popup=f"海上點 {sea_point['index']}: {sea_point['reason']}",
                opacity=0.8
            ).add_to(m)
        
        # 添加台灣邊界（如果是經緯度）
        if coordinate_system == "EPSG:4326 (經緯度)":
            # 簡化的台灣邊界多邊形
            taiwan_polygon = [
                [21.5, 119.0], [21.5, 122.5], [25.5, 122.5], 
                [25.5, 119.0], [21.5, 119.0]
            ]
            folium.Polygon(
                locations=taiwan_polygon,
                color='blue',
                fill=False,
                weight=2,
                opacity=0.5,
                popup="台灣邊界"
            ).add_to(m)
        
        # 保存地圖
        map_file = 'spatial_audit_map.html'
        m.save(map_file)
        print(f"✓ 異常點地圖已保存: {map_file}")
        
        return map_file
    
    def create_summary_report(self, lon_col, lat_col, coordinate_system, anomalies):
        """創建摘要報告"""
        print("\n=== 生成摘要報告 ===")
        
        total_points = len(self.data)
        total_anomalies = sum(len(v) for v in anomalies.values())
        valid_points = total_points - total_anomalies
        
        report = f"""
# Spatial Audit 報告

## 資料概覽
- **資料檔案**: {self.csv_file}
- **總點數**: {total_points}
- **有效點數**: {valid_points}
- **異常點數**: {total_anomalies}
- **資料品質**: {(valid_points/total_points)*100:.1f}%

## 座標系統分析
- **檢測結果**: {coordinate_system}
- **經度欄位**: {lon_col}
- **緯度欄位**: {lat_col}

## 異常點統計

### 原點異常點 (0,0)
- **數量**: {len(anomalies['zero_points'])}
- **比例**: {(len(anomalies['zero_points'])/total_points)*100:.2f}%
"""
        
        if anomalies['zero_points']:
            report += "\n#### 異常點列表:\n"
            for i, point in enumerate(anomalies['zero_points'][:10], 1):
                report += f"{i}. 索引 {point['index']}: ({point['lon']}, {point['lat']})\n"
            if len(anomalies['zero_points']) > 10:
                report += f"... 還有 {len(anomalies['zero_points'])-10} 筆\n"
        
        report += f"""
### 海上點位
- **數量**: {len(anomalies['sea_points'])}
- **比例**: {(len(anomalies['sea_points'])/total_points)*100:.2f}%
- **說明**: 台灣邊界內但不在陸地區域的點位
"""
        
        if anomalies['sea_points']:
            report += "\n#### 海上點位列表:\n"
            for i, point in enumerate(anomalies['sea_points'][:10], 1):
                report += f"{i}. 索引 {point['index']}: {point['reason']}\n"
            if len(anomalies['sea_points']) > 10:
                report += f"... 還有 {len(anomalies['sea_points'])-10} 筆\n"
        
        report += f"""
### 邊界外異常點
- **數量**: {len(anomalies['out_of_bounds'])}
- **比例**: {(len(anomalies['out_of_bounds'])/total_points)*100:.2f}%
"""
        
        if anomalies['out_of_bounds']:
            report += "\n#### 異常點列表:\n"
            for i, point in enumerate(anomalies['out_of_bounds'][:10], 1):
                report += f"{i}. 索引 {point['index']}: {point['reason']}\n"
            if len(anomalies['out_of_bounds']) > 10:
                report += f"... 還有 {len(anomalies['out_of_bounds'])-10} 筆\n"
        
        report += f"""
### 無效座標異常點
- **數量**: {len(anomalies['invalid_coordinates'])}
- **比例**: {(len(anomalies['invalid_coordinates'])/total_points)*100:.2f}%
"""
        
        if anomalies['invalid_coordinates']:
            report += "\n#### 異常點列表:\n"
            for i, point in enumerate(anomalies['invalid_coordinates'][:10], 1):
                report += f"{i}. 索引 {point['index']}: {point['reason']}\n"
        
        report += f"""
## 建議
1. **檢查座標系統**: 確認資料是否使用正確的座標系統
2. **清理異常點**: 移除或修正原點和邊界外的點
3. **驗證海上點位**: 檢查海上點位是否為有效的海上設施或資料錯誤
4. **資料驗證**: 確保所有座標都在合理範圍內
5. **座標轉換**: 如需要，使用 pyproj 進行座標轉換

## 生成檔案
- `spatial_audit_map.html` - 異常點視覺化地圖
- `spatial_audit_report.md` - 詳細分析報告

## 地圖說明
- **綠色點**: 正常的避難收容處所
- **紅色點**: 異常點（原點、邊界外、無效座標）
- **橙色點**: 海上點位（台灣邊界內但不在陸地區域）
- **藍色邊界**: 台灣地理邊界
"""
        
        # 保存報告
        with open('spatial_audit_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ 摘要報告已保存: spatial_audit_report.md")
        return report
    
    def run_audit(self):
        """執行完整的 Spatial Audit"""
        print("開始 Spatial Audit 分析...")
        
        # 載入資料
        if not self.load_data():
            return False
        
        # 檢測座標系統
        lon_col, lat_col, coordinate_system = self.detect_coordinate_system()
        
        if coordinate_system == "unknown":
            print("✗ 無法確定座標系統，停止分析")
            return False
        
        # 偵測異常點
        anomalies = self.detect_anomalies(lon_col, lat_col, coordinate_system)
        
        # 創建地圖
        self.create_anomaly_map(lon_col, lat_col, coordinate_system, anomalies)
        
        # 生成報告
        self.create_summary_report(lon_col, lat_col, coordinate_system, anomalies)
        
        print("\n✓ Spatial Audit 完成!")
        return True

def main():
    """主函數"""
    import os
    
    # 設定中文字體
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 設定 shelter.csv 檔案路徑
    csv_file = 'data/shelter.csv'
    if not os.path.exists(csv_file):
        print(f"✗ 找不到檔案: {csv_file}")
        print("請確保 data/shelter.csv 存在")
        return
    
    # 執行 Spatial Audit
    auditor = SpatialAudit(csv_file)
    auditor.run_audit()

if __name__ == "__main__":
    main()
