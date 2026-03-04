import pandas as pd
import re

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
    
    # 室內關鍵字 (包含學校和小學)
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
    
    # 如果沒有現有欄位可參考，預設為室內
    return True

def add_is_indoor_column():
    """在 shelter.csv 中新增 is_indoor 欄位"""
    
    # 讀取原始資料
    print("讀取 shelter.csv...")
    df = pd.read_csv('data/shelter.csv')
    
    print(f"原始資料: {len(df)} 筆記錄")
    print(f"欄位: {list(df.columns)}")
    
    # 新增 is_indoor 欄位
    print("\n分析避難收容所名稱...")
    df['is_indoor'] = df.apply(
        lambda row: classify_shelter_type(
            row['避難收容處所名稱'], 
            row.get('室內'), 
            row.get('室外')
        ), 
        axis=1
    )
    
    # 統計結果
    indoor_count = df['is_indoor'].sum()
    outdoor_count = len(df) - indoor_count
    
    print(f"\n分類結果:")
    print(f"室內避難所: {indoor_count} 個")
    print(f"室外避難所: {outdoor_count} 個")
    print(f"室內比例: {indoor_count/len(df)*100:.1f}%")
    
    # 顯示一些範例
    print("\n室內避難所範例:")
    indoor_examples = df[df['is_indoor'] == True]['避難收容處所名稱'].head(5).tolist()
    for i, name in enumerate(indoor_examples, 1):
        print(f"  {i}. {name}")
    
    print("\n室外避難所範例:")
    outdoor_examples = df[df['is_indoor'] == False]['避難收容處所名稱'].head(5).tolist()
    for i, name in enumerate(outdoor_examples, 1):
        print(f"  {i}. {name}")
    
    # 檢查學校相關避難所
    schools = df[df['避難收容處所名稱'].str.contains('學校|小學', na=False)]
    print(f'\n學校相關避難所檢查:')
    print(f'總計學校相關: {len(schools)} 個')
    print(f'其中室內: {schools["is_indoor"].sum()} 個')
    print(f'其中室外: {len(schools) - schools["is_indoor"].sum()} 個')
    
    # 檢查現有欄位分佈
    print(f'\n現有欄位分佈:')
    print('室內欄位:', df['室內'].value_counts().to_dict())
    print('室外欄位:', df['室外'].value_counts().to_dict())
    
    # 顯示一些具體例子
    print(f'\n具體分類範例:')
    sample = df[['避難收容處所名稱', '室內', '室外', 'is_indoor']].head(10)
    for i, (idx, row) in enumerate(sample.iterrows(), 1):
        print(f'{i}. {row["避難收容處所名稱"]} - 室內:{row["室內"]} 室外:{row["室外"]} -> is_indoor:{row["is_indoor"]}')
    
    # 儲存更新後的資料
    print("\n儲存更新後的資料...")
    df.to_csv('data/shelter.csv', index=False, encoding='utf-8')
    print("✓ 已成功新增 is_indoor 欄位到 data/shelter.csv")
    
    # 顯示更新後的欄位
    print(f"\n更新後欄位: {list(df.columns)}")
    
    # 檢查特殊情況的分類邏輯
    print(f'\n檢查特殊情況的分類邏輯:')
    print('=' * 50)
    
    # 找出室內室外都寫"是"的案例
    both_yes = df[(df['室內'] == '是') & (df['室外'] == '是')]
    print(f'室內室外都寫"是"的案例: {len(both_yes)} 個')
    if len(both_yes) > 0:
        for i, (idx, row) in enumerate(both_yes.head(3).iterrows(), 1):
            print(f'  {i}. {row["避難收容處所名稱"]} -> is_indoor: {row["is_indoor"]}')
    
    # 找出室內室外都寫"否"的案例
    both_no = df[(df['室內'] == '否') & (df['室外'] == '否')]
    print(f'\n室內室外都寫"否"的案例: {len(both_no)} 個')
    if len(both_no) > 0:
        for i, (idx, row) in enumerate(both_no.head(3).iterrows(), 1):
            print(f'  {i}. {row["避難收容處所名稱"]} -> is_indoor: {row["is_indoor"]}')
    
    # 找出室內"是"室外"否"的案例
    indoor_yes_outdoor_no = df[(df['室內'] == '是') & (df['室外'] == '否')]
    print(f'\n室內"是"室外"否"的案例: {len(indoor_yes_outdoor_no)} 個')
    if len(indoor_yes_outdoor_no) > 0:
        for i, (idx, row) in enumerate(indoor_yes_outdoor_no.head(3).iterrows(), 1):
            print(f'  {i}. {row["避難收容處所名稱"]} -> is_indoor: {row["is_indoor"]}')
    
    # 找出室內"否"室外"是"的案例
    indoor_no_outdoor_yes = df[(df['室內'] == '否') & (df['室外'] == '是')]
    print(f'\n室內"否"室外"是"的案例: {len(indoor_no_outdoor_yes)} 個')
    if len(indoor_no_outdoor_yes) > 0:
        for i, (idx, row) in enumerate(indoor_no_outdoor_yes.head(3).iterrows(), 1):
            print(f'  {i}. {row["避難收容處所名稱"]} -> is_indoor: {row["is_indoor"]}')
    
    print('\n' + '=' * 50)
    print('分類邏輯總結:')
    print('1. 室內="是" -> is_indoor=True')
    print('2. 室外="是" -> is_indoor=False') 
    print('3. 室內室外都="是" 或 都="否" -> is_indoor=True')
    print('4. 其他情況 -> is_indoor=True')
    
    return df

if __name__ == "__main__":
    add_is_indoor_column()
