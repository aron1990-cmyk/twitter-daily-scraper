import pandas as pd

# 读取Excel文件
df = pd.read_excel('/Users/aron/twitter-daily-scraper/data/twitter_daily_20250717.xlsx')

print('文件总行数:', len(df))
print('列名:', list(df.columns))

# 检查是否包含neilpatel
neilpatel_mask = df['账号'].str.contains('neilpatel', na=False)
print('是否包含neilpatel:', neilpatel_mask.any())

neilpatel_data = df[neilpatel_mask]
print('neilpatel相关推文数:', len(neilpatel_data))

if len(neilpatel_data) > 0:
    print('\nneilpatel推文示例:')
    for idx, row in neilpatel_data.head().iterrows():
        print(f"账号: {row['账号']}")
        print(f"内容: {row['推文内容'][:100]}...")
        print(f"时间: {row['发布时间']}")
        print('-' * 50)
else:
    print('\n未找到neilpatel的推文数据')
    print('\n所有账号列表:')
    unique_accounts = df['账号'].unique()
    for account in unique_accounts[:20]:  # 显示前20个账号
        print(f"  {account}")
    if len(unique_accounts) > 20:
        print(f"  ... 还有 {len(unique_accounts) - 20} 个账号")