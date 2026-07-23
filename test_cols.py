import pandas as pd
df = pd.DataFrame({'년도':[2024],'회차':[1230],'추첨일':['2024-07-01'],'1':[1],'2':[2],'3':[3],'4':[4],'5':[5],'6':[6],'보너스':[7]})
dfs = [df]
df_parsed = None
required_cols = ['회차','번호1','번호2','번호3','번호4','번호5','번호6','보너스']

for d in dfs:
    df_extracted = None
    col_vals = [str(x).strip() for x in d.columns]
    if '회차' in col_vals and '보너스' in col_vals:
        df_extracted = d.copy()
    else:
        for idx in range(min(5, len(d))):
            row_vals = [str(x).strip() for x in d.iloc[idx].values]
            if '회차' in row_vals and '보너스' in row_vals:
                d.columns = d.iloc[idx]
                df_extracted = d.iloc[idx+1:].copy()
                break
    
    if df_extracted is not None:
        col_map = {}
        for col in df_extracted.columns:
            c = str(col).strip()
            if c=='회차': col_map[col]='회차'
            elif c=='1': col_map[col]='번호1'
            elif c=='2': col_map[col]='번호2'
            elif c=='3': col_map[col]='번호3'
            elif c=='4': col_map[col]='번호4'
            elif c=='5': col_map[col]='번호5'
            elif c=='6': col_map[col]='번호6'
            elif c=='보너스': col_map[col]='보너스'
        df_extracted = df_extracted.rename(columns=col_map)
        if all(c in df_extracted.columns for c in required_cols):
            df_parsed = df_extracted[required_cols]
            break

print("Extraction Successful:")
print(df_parsed)
