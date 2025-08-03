# -*- coding: utf-8 -*-
"""
数据库查询优化器
专门处理SQL查询的性能优化，包括索引管理、查询分析等
"""

import time
import logging
from functools import wraps
from typing import Dict, List, Any, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.slow_queries = []
        self.query_stats = {}
        self.slow_query_threshold = 0.5  # 慢查询阈值（秒）
        
    def setup_query_monitoring(self):
        """设置查询监控"""
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            # 记录慢查询
            if total_time > self.slow_query_threshold:
                self.slow_queries.append({
                    'query': statement[:200] + '...' if len(statement) > 200 else statement,
                    'duration': round(total_time, 3),
                    'timestamp': time.time(),
                    'parameters': str(parameters)[:100] if parameters else None
                })
                
                # 只保留最近100条慢查询
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
                    
                logger.warning(f'Slow query detected: {total_time:.3f}s - {statement[:100]}')
            
            # 更新查询统计
            query_type = statement.strip().split()[0].upper()
            if query_type not in self.query_stats:
                self.query_stats[query_type] = {'count': 0, 'total_time': 0, 'avg_time': 0}
            
            self.query_stats[query_type]['count'] += 1
            self.query_stats[query_type]['total_time'] += total_time
            self.query_stats[query_type]['avg_time'] = (
                self.query_stats[query_type]['total_time'] / 
                self.query_stats[query_type]['count']
            )
    
    def create_indexes(self):
        """创建性能优化索引"""
        try:
            with self.db.engine.connect() as conn:
                # 为TwitterInfluencer表创建索引
                indexes = [
                    # 状态索引 - 用于筛选活跃/非活跃博主
                    "CREATE INDEX IF NOT EXISTS idx_influencer_is_active ON twitter_influencer(is_active)",
                    
                    # 分类索引 - 用于按分类筛选
                    "CREATE INDEX IF NOT EXISTS idx_influencer_category ON twitter_influencer(category)",
                    
                    # 创建时间索引 - 用于排序和时间范围查询
                    "CREATE INDEX IF NOT EXISTS idx_influencer_created_at ON twitter_influencer(created_at)",
                    
                    # 更新时间索引 - 用于获取最近更新的博主
                    "CREATE INDEX IF NOT EXISTS idx_influencer_updated_at ON twitter_influencer(updated_at)",
                    
                    # 用户名索引 - 用于搜索和去重
                    "CREATE INDEX IF NOT EXISTS idx_influencer_username ON twitter_influencer(username)",
                    
                    # 复合索引：状态+分类 - 用于常见的组合查询
                    "CREATE INDEX IF NOT EXISTS idx_influencer_active_category ON twitter_influencer(is_active, category)",
                    
                    # 为ScrapingTask表创建索引
                    "CREATE INDEX IF NOT EXISTS idx_task_status ON scraping_task(status)",
                    "CREATE INDEX IF NOT EXISTS idx_task_created_at ON scraping_task(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_task_updated_at ON scraping_task(updated_at)",
                    
                    # 为ScrapingResult表创建索引（如果存在）
                    "CREATE INDEX IF NOT EXISTS idx_result_task_id ON scraping_result(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_result_created_at ON scraping_result(created_at)",
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        logger.info(f'Created index: {index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unknown"}')
                    except Exception as e:
                        logger.warning(f'Index creation failed or already exists: {e}')
                
                conn.commit()
                logger.info('Database indexes optimization completed')
                
        except Exception as e:
            logger.error(f'Failed to create indexes: {e}')
    
    def analyze_tables(self):
        """分析表统计信息"""
        try:
            with self.db.engine.connect() as conn:
                # SQLite的ANALYZE命令
                conn.execute(text('ANALYZE'))
                conn.commit()
                logger.info('Database tables analyzed')
        except Exception as e:
            logger.error(f'Failed to analyze tables: {e}')
    
    def get_table_stats(self) -> Dict[str, Any]:
        """获取表统计信息"""
        stats = {}
        try:
            with self.db.engine.connect() as conn:
                # 获取表行数
                tables = ['twitter_influencer', 'scraping_task', 'scraping_result']
                
                for table in tables:
                    try:
                        result = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                        stats[table] = {'row_count': result[0] if result else 0}
                    except Exception as e:
                        logger.warning(f'Failed to get stats for {table}: {e}')
                        stats[table] = {'row_count': 0}
                
        except Exception as e:
            logger.error(f'Failed to get table stats: {e}')
            
        return stats
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        return sorted(self.slow_queries, key=lambda x: x['duration'], reverse=True)[:limit]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return self.query_stats.copy()
    
    def optimize_connection_pool(self):
        """优化连接池配置"""
        try:
            # 配置连接池参数
            pool_config = {
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600,  # 1小时回收连接
                'pool_pre_ping': True,  # 连接前ping检查
            }
            
            # 应用连接池配置
            engine = self.db.engine
            for key, value in pool_config.items():
                if hasattr(engine.pool, key):
                    setattr(engine.pool, key, value)
                    
            logger.info('Connection pool optimized')
            
        except Exception as e:
            logger.error(f'Failed to optimize connection pool: {e}')
    
    def vacuum_database(self):
        """清理数据库碎片"""
        try:
            with self.db.engine.connect() as conn:
                conn.execute(text('VACUUM'))
                conn.commit()
                logger.info('Database vacuumed successfully')
        except Exception as e:
            logger.error(f'Failed to vacuum database: {e}')

def query_timer(func):
    """查询计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        if duration > 0.1:  # 记录超过100ms的查询
            logger.info(f'Query {func.__name__} took {duration:.3f}s')
            
        return result
    return wrapper

def batch_query(model_class, ids: List[int], batch_size: int = 100):
    """批量查询优化"""
    results = []
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_results = model_class.query.filter(model_class.id.in_(batch_ids)).all()
        results.extend(batch_results)
    return results

class Pagination:
    """模拟Flask-SQLAlchemy的Pagination对象"""
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = (total + per_page - 1) // per_page
        self.has_prev = page > 1
        self.has_next = page * per_page < total
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """生成分页页码迭代器"""
        last = self.pages
        for num in range(1, last + 1):
            if num <= left_edge or \
               (self.page - left_current - 1 < num < self.page + right_current) or \
               num > last - right_edge:
                yield num
            elif num == left_edge + 1 or num == last - right_edge:
                yield None

def paginated_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """分页查询优化"""
    # 限制每页最大数量
    per_page = min(per_page, max_per_page)
    
    # 使用offset和limit进行分页
    offset = (page - 1) * per_page
    
    # 获取总数（使用子查询优化）
    total = query.count()
    
    # 获取当前页数据
    items = query.offset(offset).limit(per_page).all()
    
    return Pagination(items, total, page, per_page)

# 全局数据库优化器实例
db_optimizer = None

def init_db_optimizer(db: SQLAlchemy):
    """初始化数据库优化器"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(db)
    db_optimizer.setup_query_monitoring()
    db_optimizer.create_indexes()
    db_optimizer.analyze_tables()
    db_optimizer.optimize_connection_pool()
    logger.info('Database optimizer initialized')
    
    return db_optimizer