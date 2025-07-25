#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复推文抓取数量不足问题

主要问题分析：
1. 推文解析失败率高 - 选择器不够全面，验证条件过于严格
2. 去重逻辑过于严格 - 基于内容前50字符去重可能误删不同推文
3. 滚动策略不够积极 - 连续3次无新推文就停止，但可能页面还在加载
4. 等待时间不足 - 页面加载需要更多时间
5. 推文元素识别不准确 - 可能包含广告、推荐等非推文元素

解决方案：
1. 增强推文解析器的容错性
2. 优化去重策略
3. 改进滚动策略
4. 增加调试信息
5. 添加推文质量检测
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_tweet_scraping_issues():
    """修复推文抓取数量不足的问题"""
    logger.info("开始修复推文抓取数量不足问题...")
    
    # 1. 修复推文解析逻辑
    fix_tweet_parsing_logic()
    
    # 2. 修复去重策略
    fix_deduplication_strategy()
    
    # 3. 修复滚动策略
    fix_scrolling_strategy()
    
    # 4. 添加推文质量检测
    add_tweet_quality_detection()
    
    logger.info("推文抓取修复完成！")

def fix_tweet_parsing_logic():
    """修复推文解析逻辑"""
    logger.info("修复推文解析逻辑...")
    
    parser_file = '/Users/aron/twitter-daily-scraper/twitter_parser.py'
    
    # 读取原文件
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 增强的推文解析函数
    enhanced_parse_function = '''
    async def parse_tweet_element_enhanced(self, element) -> Optional[Dict[str, Any]]:
        """增强的推文元素解析 - 解决数量不足问题"""
        try:
            # 首先检查是否为有效的推文元素
            if not await self.is_valid_tweet_element(element):
                return None
            
            # 提取基础信息
            tweet_data = {
                'username': await self.extract_username_enhanced(element),
                'content': await self.extract_content_enhanced(element),
                'link': await self.extract_tweet_link_enhanced(element),
                'publish_time': await self.extract_publish_time_enhanced(element),
                'likes': 0,
                'comments': 0,
                'retweets': 0,
                'media': {'images': [], 'videos': []}
            }
            
            # 提取互动数据
            engagement = await self.extract_engagement_enhanced(element)
            tweet_data.update(engagement)
            
            # 提取媒体内容
            media = await self.extract_media_content_enhanced(element)
            tweet_data['media'] = media
            
            # 改进的去重检查
            if await self.is_duplicate_tweet_enhanced(tweet_data):
                self.logger.debug(f"推文重复，跳过: {tweet_data.get('link', 'no_link')}")
                return None
            
            # 放宽验证条件 - 只要有基本信息就保留
            if self.is_valid_tweet_data_enhanced(tweet_data):
                return tweet_data
            
            return None
            
        except Exception as e:
            self.logger.debug(f"解析推文元素失败: {e}")
            return None
    
    async def is_valid_tweet_element(self, element) -> bool:
        """检查是否为有效的推文元素"""
        try:
            # 检查是否包含推文的基本结构
            has_user_info = await element.query_selector('[data-testid="User-Name"]') is not None
            has_content_area = await element.query_selector('[data-testid="tweetText"]') is not None
            has_time = await element.query_selector('time') is not None
            has_actions = await element.query_selector('[role="group"]') is not None
            
            # 排除广告和推荐内容
            element_text = await element.text_content()
            is_ad = any(keyword in element_text.lower() for keyword in ['promoted', '推广', 'ad', '广告'])
            
            # 至少要有用户信息或内容区域，且不是广告
            return (has_user_info or has_content_area or has_time or has_actions) and not is_ad
            
        except Exception:
            return True  # 出错时保守处理，认为是有效元素
    
    async def extract_username_enhanced(self, element) -> str:
        """增强的用户名提取"""
        try:
            # 扩展选择器列表
            selectors = [
                '[data-testid="User-Name"] [dir="ltr"]',
                '[data-testid="User-Name"] span',
                '[data-testid="User-Names"] [dir="ltr"]',
                '[data-testid="User-Names"] span',
                'a[href^="/"][role="link"] span',
                '[dir="ltr"] span',
                'div[dir="ltr"] span',
                'span[dir="ltr"]'
            ]
            
            for selector in selectors:
                try:
                    elements = await element.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.text_content()
                        if text and text.strip():
                            username = self.clean_username(text.strip())
                            if username and username != 'unknown':
                                return username
                except Exception:
                    continue
            
            # 从链接中提取
            try:
                link_elem = await element.query_selector('a[href^="/"][role="link"]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    if href:
                        match = re.match(r'^/([^/]+)', href)
                        if match:
                            return match.group(1)
            except Exception:
                pass
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def clean_username(self, text: str) -> str:
        """清理用户名"""
        if not text:
            return 'unknown'
        
        # 移除@符号
        text = re.sub(r'^@+', '', text)
        
        # 只保留第一个单词
        text = text.split()[0] if text.split() else text
        
        # 移除特殊字符，只保留字母数字和下划线
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        
        # 排除明显的数字（如点赞数等）
        if re.match(r'^\d+[KMB]?$', text):
            return 'unknown'
        
        return text if text else 'unknown'
    
    async def extract_content_enhanced(self, element) -> str:
        """增强的内容提取"""
        try:
            content_parts = []
            
            # 扩展内容选择器
            selectors = [
                '[data-testid="tweetText"]',
                '[data-testid="tweetText"] span',
                '[lang] span',
                'div[dir="auto"] span',
                'div[dir="ltr"] span',
                'div[dir="rtl"] span',
                'span[dir="auto"]',
                'span[dir="ltr"]',
                'span[dir="rtl"]',
                'div[lang] span'
            ]
            
            for selector in selectors:
                try:
                    elements = await element.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.text_content()
                        if text and text.strip():
                            clean_text = text.strip()
                            if clean_text not in content_parts and len(clean_text) > 2:
                                content_parts.append(clean_text)
                except Exception:
                    continue
            
            if content_parts:
                content = ' '.join(content_parts)
                return self.clean_tweet_content_enhanced(content)
            
            # 如果没有找到内容，尝试从整个元素提取
            try:
                full_text = await element.text_content()
                if full_text:
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    # 过滤掉用户名、时间等信息，保留主要内容
                    content_lines = []
                    for line in lines:
                        if (len(line) > 10 and 
                            not line.startswith('@') and 
                            not re.match(r'^\d+[hms]$', line) and
                            not re.match(r'^\d+[KMB]?$', line)):
                            content_lines.append(line)
                    
                    if content_lines:
                        return ' '.join(content_lines[:3])  # 取前3行
            except Exception:
                pass
            
            return 'No content available'
            
        except Exception:
            return 'No content available'
    
    def clean_tweet_content_enhanced(self, content: str) -> str:
        """增强的内容清理"""
        if not content:
            return ""
        
        # 基础清理
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 移除明显的重复模式
        content = re.sub(r'\b(\w+)\s+\1\b', r'\1', content)
        
        # 移除末尾的统计信息
        content = re.sub(r'\s*[·…]+\s*\d+[KMB]?\s*$', '', content)
        
        # 移除开头的重复用户名
        content = re.sub(r'^(@?\w+)\s+\1\s+', r'\1 ', content)
        
        return content.strip()
    
    async def extract_tweet_link_enhanced(self, element) -> str:
        """增强的链接提取"""
        try:
            # 多种链接选择器
            selectors = [
                'a[href*="/status/"]',
                'a[href*="/status/"][role="link"]',
                'time[datetime] a',
                'time a'
            ]
            
            for selector in selectors:
                try:
                    link_elem = await element.query_selector(selector)
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href and '/status/' in href:
                            if href.startswith('/'):
                                return f'https://x.com{href}'
                            return href
                except Exception:
                    continue
            
            return ''
            
        except Exception:
            return ''
    
    async def is_duplicate_tweet_enhanced(self, tweet_data: Dict[str, Any]) -> bool:
        """增强的去重检查"""
        try:
            # 优先使用链接去重
            link = tweet_data.get('link', '')
            if link:
                tweet_id = self.extract_tweet_id(link)
                if tweet_id:
                    if not hasattr(self, 'seen_tweet_ids_enhanced'):
                        self.seen_tweet_ids_enhanced = set()
                    
                    if tweet_id in self.seen_tweet_ids_enhanced:
                        return True
                    self.seen_tweet_ids_enhanced.add(tweet_id)
                    return False
            
            # 如果没有链接，使用内容去重（更宽松的策略）
            content = tweet_data.get('content', '')
            if content and len(content) > 20:
                # 使用内容的哈希值而不是前50字符
                import hashlib
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if not hasattr(self, 'seen_content_hashes'):
                    self.seen_content_hashes = set()
                
                if content_hash in self.seen_content_hashes:
                    return True
                self.seen_content_hashes.add(content_hash)
            
            return False
            
        except Exception:
            return False
    
    def is_valid_tweet_data_enhanced(self, tweet_data: Dict[str, Any]) -> bool:
        """增强的推文数据验证 - 更宽松的条件"""
        try:
            username = tweet_data.get('username', '')
            content = tweet_data.get('content', '')
            link = tweet_data.get('link', '')
            
            # 只要满足以下任一条件就认为有效：
            # 1. 有用户名且不是unknown
            # 2. 有内容且长度大于5
            # 3. 有有效链接
            # 4. 有媒体内容
            # 5. 有任何互动数据
            
            has_username = username and username != 'unknown'
            has_content = content and content != 'No content available' and len(content.strip()) > 5
            has_link = link and '/status/' in link
            has_media = (tweet_data.get('media', {}).get('images') or 
                        tweet_data.get('media', {}).get('videos'))
            has_engagement = (tweet_data.get('likes', 0) > 0 or 
                            tweet_data.get('comments', 0) > 0 or 
                            tweet_data.get('retweets', 0) > 0)
            
            return has_username or has_content or has_link or has_media or has_engagement
            
        except Exception:
            return False
'''
    
    # 在文件中添加增强的解析函数
    if 'parse_tweet_element_enhanced' not in content:
        # 找到合适的位置插入新函数
        insert_pos = content.find('async def parse_tweet_element_optimized')
        if insert_pos != -1:
            content = content[:insert_pos] + enhanced_parse_function + '\n\n    ' + content[insert_pos:]
        else:
            # 如果找不到，添加到类的末尾
            class_end = content.rfind('class TwitterParser')
            if class_end != -1:
                next_class = content.find('\nclass ', class_end + 1)
                if next_class != -1:
                    content = content[:next_class] + enhanced_parse_function + '\n' + content[next_class:]
                else:
                    content += enhanced_parse_function
    
    # 写回文件
    with open(parser_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("推文解析逻辑修复完成")

def fix_deduplication_strategy():
    """修复去重策略"""
    logger.info("修复去重策略...")
    
    parser_file = '/Users/aron/twitter-daily-scraper/twitter_parser.py'
    
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复原有的去重逻辑
    old_dedup_pattern = r'tweet_id = tweet_data\.get\(\'link\', \'\'\'\) or tweet_data\.get\(\'content\', \'\'\'\)\[:50\]'
    new_dedup_logic = '''# 改进的去重逻辑
            link = tweet_data.get('link', '')
            if link:
                tweet_id = self.extract_tweet_id(link)
                if tweet_id:
                    if tweet_id not in self.seen_tweet_ids:
                        self.seen_tweet_ids.add(tweet_id)
                        tweets_data.append(tweet_data)
                        new_tweets_parsed += 1
                        self.logger.debug(f"新抓取推文: @{tweet_data.get('username', 'unknown')}")
                    else:
                        self.logger.debug(f"推文重复(链接): {tweet_id}")
                else:
                    # 没有有效ID，使用内容哈希
                    content = tweet_data.get('content', '')
                    if content and len(content) > 10:
                        import hashlib
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        if content_hash not in getattr(self, 'seen_content_hashes', set()):
                            if not hasattr(self, 'seen_content_hashes'):
                                self.seen_content_hashes = set()
                            self.seen_content_hashes.add(content_hash)
                            tweets_data.append(tweet_data)
                            new_tweets_parsed += 1
                            self.logger.debug(f"新抓取推文(内容): @{tweet_data.get('username', 'unknown')}")
                        else:
                            self.logger.debug(f"推文重复(内容): {content[:30]}...")
            else:
                # 没有链接，直接添加（风险较低的重复）
                tweets_data.append(tweet_data)
                new_tweets_parsed += 1
                self.logger.debug(f"新抓取推文(无链接): @{tweet_data.get('username', 'unknown')}")'''
    
    # 替换去重逻辑
    if 'tweet_id not in self.seen_tweet_ids:' in content:
        # 找到并替换整个去重代码块
        pattern = r'tweet_id = tweet_data\.get\(\'link\', \'\'\'\) or tweet_data\.get\(\'content\', \'\'\'\)\[:50\]\s*if tweet_id not in self\.seen_tweet_ids:[^}]+?self\.logger\.debug\(f"新抓取推文: @\{tweet_data\.get\(\'username\', \'unknown\'\)\}"\)'
        
        import re
        content = re.sub(pattern, new_dedup_logic, content, flags=re.DOTALL)
    
    with open(parser_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("去重策略修复完成")

def fix_scrolling_strategy():
    """修复滚动策略"""
    logger.info("修复滚动策略...")
    
    parser_file = '/Users/aron/twitter-daily-scraper/twitter_parser.py'
    
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改滚动参数
    # 1. 增加最大滚动次数
    content = re.sub(r'max_scroll_attempts = 20', 'max_scroll_attempts = 30', content)
    
    # 2. 减少连续无新推文的阈值
    content = re.sub(r'if no_new_tweets_count >= 3:', 'if no_new_tweets_count >= 5:', content)
    
    # 3. 增加等待时间
    content = re.sub(r'await asyncio\.sleep\(1\)', 'await asyncio.sleep(2)', content)
    
    # 4. 增加滚动距离
    content = re.sub(r'window\.scrollBy\(0, 800\)', 'window.scrollBy(0, 1200)', content)
    
    with open(parser_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("滚动策略修复完成")

def add_tweet_quality_detection():
    """添加推文质量检测"""
    logger.info("添加推文质量检测...")
    
    parser_file = '/Users/aron/twitter-daily-scraper/twitter_parser.py'
    
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加推文质量检测函数
    quality_detection_code = '''
    def detect_tweet_quality(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测推文质量并添加质量标记"""
        try:
            quality_score = 0
            quality_issues = []
            
            # 检查用户名
            username = tweet_data.get('username', '')
            if username and username != 'unknown':
                quality_score += 20
            else:
                quality_issues.append('缺少用户名')
            
            # 检查内容
            content = tweet_data.get('content', '')
            if content and content != 'No content available':
                if len(content) > 10:
                    quality_score += 30
                elif len(content) > 5:
                    quality_score += 15
                    quality_issues.append('内容过短')
                else:
                    quality_issues.append('内容太短')
            else:
                quality_issues.append('缺少内容')
            
            # 检查链接
            link = tweet_data.get('link', '')
            if link and '/status/' in link:
                quality_score += 25
            else:
                quality_issues.append('缺少有效链接')
            
            # 检查时间
            if tweet_data.get('publish_time'):
                quality_score += 10
            else:
                quality_issues.append('缺少发布时间')
            
            # 检查互动数据
            has_engagement = (tweet_data.get('likes', 0) > 0 or 
                            tweet_data.get('comments', 0) > 0 or 
                            tweet_data.get('retweets', 0) > 0)
            if has_engagement:
                quality_score += 15
            else:
                quality_issues.append('缺少互动数据')
            
            # 添加质量信息
            tweet_data['quality_score'] = quality_score
            tweet_data['quality_issues'] = quality_issues
            tweet_data['quality_level'] = (
                'high' if quality_score >= 80 else
                'medium' if quality_score >= 50 else
                'low'
            )
            
            return tweet_data
            
        except Exception as e:
            self.logger.debug(f"质量检测失败: {e}")
            tweet_data['quality_score'] = 0
            tweet_data['quality_issues'] = ['质量检测失败']
            tweet_data['quality_level'] = 'unknown'
            return tweet_data
'''
    
    if 'detect_tweet_quality' not in content:
        # 在类的末尾添加质量检测函数
        insert_pos = content.rfind('    def ')
        if insert_pos != -1:
            # 找到下一个函数的结束位置
            next_def = content.find('\n    def ', insert_pos + 1)
            if next_def == -1:
                next_def = content.find('\nclass ', insert_pos)
            if next_def == -1:
                next_def = len(content)
            
            content = content[:next_def] + quality_detection_code + '\n' + content[next_def:]
        else:
            content += quality_detection_code
    
    with open(parser_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("推文质量检测添加完成")

def create_enhanced_scraping_test():
    """创建增强抓取测试脚本"""
    logger.info("创建增强抓取测试脚本...")
    
    test_script = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的推文抓取功能
"""

import asyncio
import logging
from twitter_parser import TwitterParser

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_scraping():
    """测试增强的推文抓取"""
    parser = None
    try:
        logger.info("开始测试增强推文抓取...")
        
        # 创建解析器
        parser = TwitterParser()
        await parser.init_browser()
        
        # 测试用户推文抓取
        test_username = "socialmedia2day"
        target_tweets = 50
        
        logger.info(f"测试抓取用户 @{test_username} 的 {target_tweets} 条推文")
        
        tweets = await parser.scrape_user_tweets(test_username, target_tweets)
        
        logger.info(f"抓取结果: 目标 {target_tweets} 条，实际获得 {len(tweets)} 条")
        
        if len(tweets) < target_tweets:
            shortage = target_tweets - len(tweets)
            logger.warning(f"仍然存在数量不足问题，缺少 {shortage} 条推文")
        else:
            logger.info("抓取数量达到目标！")
        
        # 分析推文质量
        if hasattr(parser, 'detect_tweet_quality'):
            quality_stats = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
            for tweet in tweets:
                tweet = parser.detect_tweet_quality(tweet)
                quality_level = tweet.get('quality_level', 'unknown')
                quality_stats[quality_level] += 1
            
            logger.info(f"推文质量分布: {quality_stats}")
        
        # 显示前5条推文的详细信息
        logger.info("前5条推文详情:")
        for i, tweet in enumerate(tweets[:5], 1):
            logger.info(f"推文 {i}:")
            logger.info(f"  用户: @{tweet.get('username', 'unknown')}")
            logger.info(f"  内容: {tweet.get('content', 'No content')[:100]}...")
            logger.info(f"  链接: {tweet.get('link', 'No link')}")
            logger.info(f"  互动: 👍{tweet.get('likes', 0)} 💬{tweet.get('comments', 0)} 🔄{tweet.get('retweets', 0)}")
            if 'quality_score' in tweet:
                logger.info(f"  质量: {tweet['quality_level']} ({tweet['quality_score']}/100)")
            logger.info("")
        
        return len(tweets)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 0
    finally:
        if parser:
            await parser.close()

if __name__ == "__main__":
    result = asyncio.run(test_enhanced_scraping())
    print(f"\n测试完成，共抓取 {result} 条推文")
'''
    
    with open('/Users/aron/twitter-daily-scraper/test_enhanced_scraping.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    logger.info("测试脚本创建完成")

if __name__ == "__main__":
    fix_tweet_scraping_issues()
    create_enhanced_scraping_test()
    
    print("\n=== 修复完成 ===")
    print("主要修复内容:")
    print("1. 增强推文解析器的容错性和选择器覆盖")
    print("2. 优化去重策略，减少误删")
    print("3. 改进滚动策略，增加抓取机会")
    print("4. 添加推文质量检测")
    print("5. 增加详细的调试日志")
    print("\n建议运行测试脚本验证修复效果:")
    print("python3 test_enhanced_scraping.py")