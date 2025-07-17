import pytest
import json
import sqlite3
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_writer import ExcelWriter
from storage_manager import StorageManager
from models import Tweet

class TestDataExport:
    """数据保存模块测试类"""
    
    @pytest.fixture
    def sample_tweets_data(self):
        """加载示例推文数据"""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def sample_tweets_objects(self, sample_tweets_data):
        """转换为Tweet对象列表"""
        tweets = []
        for data in sample_tweets_data:
            tweet = Tweet(
                id=data['id'],
                username=data['username'],
                content=data['content'],
                timestamp=data['timestamp'],
                url=data['url'],
                likes=data['likes'],
                retweets=data['retweets'],
                replies=data['replies']
            )
            tweets.append(tweet)
        return tweets
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_excel_export_basic(self, sample_tweets_data, temp_dir):
        """测试基础Excel导出功能
        
        验证能够正确导出推文数据到Excel文件
        """
        excel_writer = ExcelWriter()
        output_file = temp_dir / "test_tweets.xlsx"
        
        # 执行导出
        excel_writer.write_tweets_to_excel(sample_tweets_data, str(output_file))
        
        # 验证文件存在
        assert output_file.exists()
        
        # 验证文件内容
        df = pd.read_excel(output_file)
        assert len(df) == len(sample_tweets_data)
        
        # 验证必需字段存在
        required_columns = ['username', 'content', 'timestamp', 'url', 'likes', 'retweets', 'replies']
        for col in required_columns:
            assert col in df.columns
    
    def test_excel_export_custom_fields(self, sample_tweets_data, temp_dir):
        """测试自定义字段Excel导出
        
        验证自定义字段模板能够正确应用到Excel导出
        """
        excel_writer = ExcelWriter()
        output_file = temp_dir / "test_custom_tweets.xlsx"
        
        # 定义自定义字段
        custom_fields = ['username', 'content', 'likes', 'url']
        
        # 执行导出
        excel_writer.write_tweets_to_excel(
            sample_tweets_data, 
            str(output_file),
            custom_fields=custom_fields
        )
        
        # 验证文件存在
        assert output_file.exists()
        
        # 验证只包含指定字段
        df = pd.read_excel(output_file)
        assert list(df.columns) == custom_fields
        assert len(df) == len(sample_tweets_data)
    
    def test_json_export_basic(self, sample_tweets_data, temp_dir):
        """测试基础JSON导出功能
        
        验证能够正确导出推文数据到JSON文件
        """
        output_file = temp_dir / "test_tweets.json"
        
        # 执行导出
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_tweets_data, f, ensure_ascii=False, indent=2)
        
        # 验证文件存在
        assert output_file.exists()
        
        # 验证文件内容
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == len(sample_tweets_data)
        assert loaded_data == sample_tweets_data
    
    def test_json_export_structure_validation(self, sample_tweets_data, temp_dir):
        """测试JSON导出结构验证
        
        验证导出的JSON文件结构完整性
        """
        output_file = temp_dir / "test_structure_tweets.json"
        
        # 执行导出
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_tweets_data, f, ensure_ascii=False, indent=2)
        
        # 验证JSON结构
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        required_fields = ['id', 'username', 'content', 'timestamp', 'url']
        for tweet in loaded_data:
            for field in required_fields:
                assert field in tweet, f"Missing field {field} in exported JSON"
    
    def test_sqlite_export_basic(self, sample_tweets_objects, temp_dir):
        """测试基础SQLite导出功能
        
        验证能够正确导出推文数据到SQLite数据库
        """
        db_file = temp_dir / "test_tweets.db"
        storage_manager = StorageManager(str(db_file))
        
        # 执行导出
        for tweet in sample_tweets_objects:
            storage_manager.save_tweet(tweet)
        
        # 验证数据库文件存在
        assert db_file.exists()
        
        # 验证数据库内容
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tweets")
        count = cursor.fetchone()[0]
        assert count == len(sample_tweets_objects)
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [row[1] for row in cursor.fetchall()]
        required_columns = ['id', 'username', 'content', 'timestamp', 'url']
        for col in required_columns:
            assert col in columns
        
        conn.close()
    
    def test_sqlite_export_data_integrity(self, sample_tweets_objects, temp_dir):
        """测试SQLite导出数据完整性
        
        验证导出到SQLite的数据完整性和准确性
        """
        db_file = temp_dir / "test_integrity_tweets.db"
        storage_manager = StorageManager(str(db_file))
        
        # 执行导出
        for tweet in sample_tweets_objects:
            storage_manager.save_tweet(tweet)
        
        # 验证数据完整性
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tweets ORDER BY id")
        rows = cursor.fetchall()
        
        assert len(rows) == len(sample_tweets_objects)
        
        # 验证具体数据
        for i, row in enumerate(rows):
            original_tweet = sample_tweets_objects[i]
            assert str(row[0]) == original_tweet.id  # id
            assert row[1] == original_tweet.username  # username
            assert row[2] == original_tweet.content   # content
        
        conn.close()
    
    @pytest.mark.parametrize("export_format,file_extension", [
        ("excel", ".xlsx"),
        ("json", ".json"),
        ("sqlite", ".db")
    ])
    def test_multiple_export_formats(self, sample_tweets_data, temp_dir, export_format, file_extension):
        """测试多种导出格式支持
        
        验证系统支持Excel、JSON、SQLite等多种导出格式
        """
        output_file = temp_dir / f"test_tweets{file_extension}"
        
        if export_format == "excel":
            excel_writer = ExcelWriter()
            excel_writer.write_tweets_to_excel(sample_tweets_data, str(output_file))
        elif export_format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sample_tweets_data, f, ensure_ascii=False, indent=2)
        elif export_format == "sqlite":
            # 创建简单的SQLite数据库
            conn = sqlite3.connect(str(output_file))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE tweets (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    content TEXT,
                    timestamp TEXT,
                    url TEXT,
                    likes INTEGER,
                    retweets INTEGER,
                    replies INTEGER
                )
            ''')
            
            for tweet in sample_tweets_data:
                cursor.execute('''
                    INSERT INTO tweets VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tweet['id'], tweet['username'], tweet['content'],
                    tweet['timestamp'], tweet['url'], tweet['likes'],
                    tweet['retweets'], tweet['replies']
                ))
            
            conn.commit()
            conn.close()
        
        # 验证文件存在
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_excel_export_large_dataset(self, temp_dir):
        """测试大数据集Excel导出
        
        验证Excel导出能够处理大量推文数据
        """
        # 生成大量测试数据
        large_dataset = []
        for i in range(1000):
            tweet = {
                'id': str(i),
                'username': f'user_{i % 10}',
                'content': f'This is test tweet number {i}',
                'timestamp': '2024-01-15 10:00:00',
                'url': f'https://twitter.com/user_{i % 10}/status/{i}',
                'likes': i * 10,
                'retweets': i * 2,
                'replies': i
            }
            large_dataset.append(tweet)
        
        excel_writer = ExcelWriter()
        output_file = temp_dir / "large_dataset.xlsx"
        
        # 执行导出
        excel_writer.write_tweets_to_excel(large_dataset, str(output_file))
        
        # 验证文件存在且大小合理
        assert output_file.exists()
        assert output_file.stat().st_size > 10000  # 至少10KB
        
        # 验证数据完整性
        df = pd.read_excel(output_file)
        assert len(df) == 1000
    
    def test_export_with_special_characters(self, temp_dir):
        """测试包含特殊字符的数据导出
        
        验证导出功能能够正确处理特殊字符和Unicode
        """
        special_tweets = [
            {
                'id': '1',
                'username': 'test_user',
                'content': 'Tweet with emoji 😀🚀 and special chars: @#$%^&*()',
                'timestamp': '2024-01-15 10:00:00',
                'url': 'https://twitter.com/test_user/status/1',
                'likes': 100,
                'retweets': 20,
                'replies': 5
            },
            {
                'id': '2',
                'username': '测试用户',
                'content': '包含中文的推文内容，测试Unicode支持',
                'timestamp': '2024-01-15 11:00:00',
                'url': 'https://twitter.com/测试用户/status/2',
                'likes': 50,
                'retweets': 10,
                'replies': 2
            }
        ]
        
        # 测试Excel导出
        excel_writer = ExcelWriter()
        excel_file = temp_dir / "special_chars.xlsx"
        excel_writer.write_tweets_to_excel(special_tweets, str(excel_file))
        
        assert excel_file.exists()
        df = pd.read_excel(excel_file)
        assert len(df) == 2
        assert '😀🚀' in df.iloc[0]['content']
        assert '中文' in df.iloc[1]['content']
        
        # 测试JSON导出
        json_file = temp_dir / "special_chars.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(special_tweets, f, ensure_ascii=False, indent=2)
        
        assert json_file.exists()
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert len(loaded_data) == 2
        assert '😀🚀' in loaded_data[0]['content']
    
    def test_export_empty_dataset(self, temp_dir):
        """测试空数据集导出
        
        验证当没有推文数据时的导出处理
        """
        empty_data = []
        
        # 测试Excel导出
        excel_writer = ExcelWriter()
        excel_file = temp_dir / "empty.xlsx"
        excel_writer.write_tweets_to_excel(empty_data, str(excel_file))
        
        assert excel_file.exists()
        df = pd.read_excel(excel_file)
        assert len(df) == 0
        
        # 测试JSON导出
        json_file = temp_dir / "empty.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f)
        
        assert json_file.exists()
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert len(loaded_data) == 0
    
    def test_export_file_permissions(self, sample_tweets_data, temp_dir):
        """测试导出文件权限处理
        
        验证在文件权限受限时的错误处理
        """
        excel_writer = ExcelWriter()
        
        # 尝试写入到不存在的目录
        invalid_path = temp_dir / "nonexistent" / "test.xlsx"
        
        with pytest.raises(Exception):
            excel_writer.write_tweets_to_excel(sample_tweets_data, str(invalid_path))
    
    def test_custom_field_template_validation(self, sample_tweets_data, temp_dir):
        """测试自定义字段模板验证
        
        验证自定义字段模板的有效性检查
        """
        excel_writer = ExcelWriter()
        output_file = temp_dir / "custom_template.xlsx"
        
        # 测试有效的自定义字段
        valid_fields = ['username', 'content', 'likes']
        excel_writer.write_tweets_to_excel(
            sample_tweets_data, 
            str(output_file),
            custom_fields=valid_fields
        )
        
        df = pd.read_excel(output_file)
        assert list(df.columns) == valid_fields
        
        # 测试包含无效字段的模板
        invalid_fields = ['username', 'nonexistent_field', 'content']
        output_file2 = temp_dir / "invalid_template.xlsx"
        
        # 应该忽略无效字段或抛出警告
        excel_writer.write_tweets_to_excel(
            sample_tweets_data, 
            str(output_file2),
            custom_fields=invalid_fields
        )
        
        df2 = pd.read_excel(output_file2)
        # 验证只包含有效字段
        valid_columns = [col for col in invalid_fields if col in sample_tweets_data[0].keys()]
        assert all(col in df2.columns for col in valid_columns)
    
    @pytest.mark.parametrize("batch_size", [10, 50, 100])
    def test_batch_export_performance(self, temp_dir, batch_size):
        """测试批量导出性能
        
        验证不同批量大小的导出性能
        """
        # 生成测试数据
        test_data = []
        for i in range(batch_size):
            tweet = {
                'id': str(i),
                'username': f'user_{i}',
                'content': f'Batch test tweet {i}',
                'timestamp': '2024-01-15 10:00:00',
                'url': f'https://twitter.com/user_{i}/status/{i}',
                'likes': i,
                'retweets': i // 2,
                'replies': i // 5
            }
            test_data.append(tweet)
        
        excel_writer = ExcelWriter()
        output_file = temp_dir / f"batch_{batch_size}.xlsx"
        
        # 执行批量导出
        excel_writer.write_tweets_to_excel(test_data, str(output_file))
        
        # 验证结果
        assert output_file.exists()
        df = pd.read_excel(output_file)
        assert len(df) == batch_size

if __name__ == "__main__":
    pytest.main(["-v", __file__])