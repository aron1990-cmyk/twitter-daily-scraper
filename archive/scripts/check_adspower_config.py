#!/usr/bin/env python3
from web_app import app, db, SystemConfig

with app.app_context():
    configs = SystemConfig.query.all()
    config_dict = {cfg.key: cfg.value for cfg in configs}
    
    print("AdsPower相关配置:")
    adspower_configs = {k: v for k, v in config_dict.items() if 'adspower' in k.lower()}
    
    if adspower_configs:
        for k, v in adspower_configs.items():
            print(f"  {k}: {v}")
    else:
        print("  未找到AdsPower配置")
    
    print("\n所有配置:")
    for k, v in config_dict.items():
        print(f"  {k}: {v}")