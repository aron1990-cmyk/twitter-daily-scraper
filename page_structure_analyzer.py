# -*- coding: utf-8 -*-
"""
智能页面结构识别与自动化采集系统
类似八爪鱼采集器的功能，能够自动识别页面结构并进行数据采集
"""

import asyncio
import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from playwright.async_api import Page, ElementHandle
import re

class PageStructureAnalyzer:
    """页面结构分析器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.structure_cache = {}
        self.selectors_cache = {}
        
    async def analyze_page_structure(self) -> Dict[str, Any]:
        """分析页面结构，识别关键元素"""
        try:
            self.logger.info("开始分析页面结构...")
            
            # 获取页面基本信息
            page_info = await self._get_page_info()
            
            # 识别内容容器
            content_containers = await self._identify_content_containers()
            
            # 识别列表项元素
            list_items = await self._identify_list_items()
            
            # 识别分页/加载更多元素
            pagination_elements = await self._identify_pagination_elements()
            
            # 识别数据字段
            data_fields = await self._identify_data_fields(list_items)
            
            structure = {
                'page_info': page_info,
                'content_containers': content_containers,
                'list_items': list_items,
                'pagination': pagination_elements,
                'data_fields': data_fields,
                'analysis_time': datetime.now().isoformat()
            }
            
            self.structure_cache = structure
            self.logger.info(f"页面结构分析完成，发现 {len(list_items)} 个列表项")
            
            return structure
            
        except Exception as e:
            self.logger.error(f"页面结构分析失败: {e}")
            return {}
    
    async def _get_page_info(self) -> Dict[str, Any]:
        """获取页面基本信息"""
        try:
            title = await self.page.title()
            url = self.page.url
            
            # 检测页面类型
            page_type = 'unknown'
            if 'x.com' in url or 'twitter.com' in url:
                if '/search' in url:
                    page_type = 'twitter_search'
                elif re.search(r'/[^/]+$', url):
                    page_type = 'twitter_profile'
                else:
                    page_type = 'twitter_home'
            
            return {
                'title': title,
                'url': url,
                'page_type': page_type,
                'domain': url.split('/')[2] if '/' in url else ''
            }
            
        except Exception as e:
            self.logger.error(f"获取页面信息失败: {e}")
            return {}
    
    async def _identify_content_containers(self) -> List[Dict[str, Any]]:
        """识别内容容器"""
        try:
            containers = []
            
            # Twitter特定的容器选择器
            twitter_selectors = [
                '[data-testid="primaryColumn"]',
                '[aria-label="Timeline: Your Home Timeline"]',
                '[aria-label*="Timeline"]',
                'main[role="main"]',
                'section[role="region"]'
            ]
            
            # 通用容器选择器
            generic_selectors = [
                'main',
                '.main-content',
                '#main-content',
                '.content',
                '.container',
                '[role="main"]'
            ]
            
            all_selectors = twitter_selectors + generic_selectors
            
            for selector in all_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            box = await element.bounding_box()
                            if box and box['width'] > 200 and box['height'] > 200:
                                containers.append({
                                    'selector': selector,
                                    'element': element,
                                    'bounds': box
                                })
                                break
                except Exception:
                    continue
            
            return containers
            
        except Exception as e:
            self.logger.error(f"识别内容容器失败: {e}")
            return []
    
    async def _identify_list_items(self) -> List[Dict[str, Any]]:
        """识别列表项元素"""
        try:
            list_items = []
            
            # Twitter特定的推文选择器
            twitter_selectors = [
                '[data-testid="tweet"]',
                '[data-testid="tweetText"]',
                'article[role="article"]',
                'div[data-testid="tweet"]'
            ]
            
            # 通用列表项选择器
            generic_selectors = [
                '.post',
                '.item',
                '.entry',
                '.card',
                'article',
                'li',
                '.list-item'
            ]
            
            all_selectors = twitter_selectors + generic_selectors
            
            for selector in all_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if len(elements) >= 3:  # 至少要有3个相似元素才认为是列表
                        for i, element in enumerate(elements[:10]):  # 只分析前10个
                            if await element.is_visible():
                                box = await element.bounding_box()
                                if box and box['height'] > 50:  # 高度至少50px
                                    list_items.append({
                                        'selector': selector,
                                        'element': element,
                                        'index': i,
                                        'bounds': box
                                    })
                        if list_items:
                            break
                except Exception:
                    continue
            
            return list_items
            
        except Exception as e:
            self.logger.error(f"识别列表项失败: {e}")
            return []
    
    async def _identify_pagination_elements(self) -> Dict[str, Any]:
        """识别分页/加载更多元素"""
        try:
            pagination = {
                'type': 'infinite_scroll',  # Twitter使用无限滚动
                'load_trigger': 'scroll',
                'indicators': []
            }
            
            # 查找加载指示器
            loading_selectors = [
                '[aria-label*="Loading"]',
                '.loading',
                '.spinner',
                '[data-testid="spinner"]',
                'div[role="progressbar"]'
            ]
            
            for selector in loading_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        pagination['indicators'].append({
                            'type': 'loading',
                            'selector': selector,
                            'count': len(elements)
                        })
                except Exception:
                    continue
            
            return pagination
            
        except Exception as e:
            self.logger.error(f"识别分页元素失败: {e}")
            return {'type': 'unknown'}
    
    async def _identify_data_fields(self, list_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """识别数据字段"""
        try:
            if not list_items:
                return {}
            
            # 分析第一个列表项的结构
            first_item = list_items[0]['element']
            
            fields = {
                'text_content': [],
                'links': [],
                'images': [],
                'metadata': [],
                'interactions': []
            }
            
            # Twitter特定字段选择器
            twitter_field_map = {
                'text_content': [
                    '[data-testid="tweetText"]',
                    'div[lang] span',
                    'div[dir="auto"] span'
                ],
                'links': [
                    'a[href*="/status/"]',
                    'a[href^="/"]',
                    'a[href^="http"]'
                ],
                'metadata': [
                    'time',
                    '[data-testid="User-Name"]',
                    '[data-testid="User-Names"]'
                ],
                'interactions': [
                    '[data-testid="like"]',
                    '[data-testid="reply"]',
                    '[data-testid="retweet"]'
                ],
                'images': [
                    'img',
                    '[data-testid="tweetPhoto"]'
                ]
            }
            
            # 检查每个字段类型
            for field_type, selectors in twitter_field_map.items():
                for selector in selectors:
                    try:
                        elements = await first_item.query_selector_all(selector)
                        if elements:
                            fields[field_type].append(selector)
                    except Exception:
                        continue
            
            return fields
            
        except Exception as e:
            self.logger.error(f"识别数据字段失败: {e}")
            return {}
    
    async def generate_extraction_config(self) -> Dict[str, Any]:
        """生成数据提取配置"""
        try:
            if not self.structure_cache:
                await self.analyze_page_structure()
            
            config = {
                'page_type': self.structure_cache.get('page_info', {}).get('page_type', 'unknown'),
                'extraction_rules': {
                    'list_selector': '',
                    'fields': {},
                    'pagination': {}
                },
                'scroll_config': {
                    'method': 'infinite_scroll',
                    'trigger_distance': 1000,
                    'max_scrolls': 50,
                    'scroll_delay': 2000
                }
            }
            
            # 设置列表选择器
            list_items = self.structure_cache.get('list_items', [])
            if list_items:
                config['extraction_rules']['list_selector'] = list_items[0]['selector']
            
            # 设置字段提取规则
            data_fields = self.structure_cache.get('data_fields', {})
            for field_type, selectors in data_fields.items():
                if selectors:
                    config['extraction_rules']['fields'][field_type] = {
                        'selectors': selectors,
                        'primary_selector': selectors[0] if selectors else ''
                    }
            
            # 设置分页配置
            pagination = self.structure_cache.get('pagination', {})
            config['extraction_rules']['pagination'] = pagination
            
            return config
            
        except Exception as e:
            self.logger.error(f"生成提取配置失败: {e}")
            return {}

class IntelligentScraper:
    """智能采集器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.analyzer = PageStructureAnalyzer(page)
        self.logger = logging.getLogger(__name__)
        self.extraction_config = {}
        
    async def intelligent_scrape(self, url: str, analysis: Dict, config: Dict) -> List[Dict]:
        """
        基于分析结果进行智能采集
        
        Args:
            url: 目标URL
            analysis: 页面结构分析结果
            config: 采集配置
            
        Returns:
            采集到的数据列表
        """
        try:
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            collected_data = []
            max_items = config.get('max_items', 50)
            scroll_delay = config.get('scroll_delay', 2)
            max_scrolls = config.get('max_scrolls', 50)
            
            list_items = analysis.get('list_items', [])
            data_fields = analysis.get('data_fields', {})
            
            if not list_items:
                print("[WARNING] 未找到列表项选择器")
                return collected_data
            
            # 使用第一个列表项选择器
            item_selector = list_items[0]['selector']
            print(f"[INFO] 使用选择器: {item_selector}")
            
            scroll_count = 0
            last_count = 0
            no_new_items_count = 0
            
            while len(collected_data) < max_items and scroll_count < max_scrolls:
                # 等待内容加载
                try:
                    await self.page.wait_for_selector(item_selector, timeout=5000)
                except:
                    print(f"[WARNING] 等待选择器 {item_selector} 超时")
                
                # 获取当前页面的所有项目
                items = await self.page.query_selector_all(item_selector)
                print(f"[INFO] 找到 {len(items)} 个项目")
                
                # 提取新项目的数据
                for i, item in enumerate(items[last_count:], last_count):
                    if len(collected_data) >= max_items:
                        break
                    
                    item_data = await self._extract_item_data(item, data_fields, i)
                    if item_data:
                        collected_data.append(item_data)
                        print(f"[INFO] 采集第 {len(collected_data)} 项: {item_data.get('content', '')[:50]}...")
                
                current_count = len(items)
                
                # 检查是否有新内容
                if current_count == last_count:
                    no_new_items_count += 1
                    if no_new_items_count >= 3:  # 连续3次没有新内容，停止采集
                        print("[INFO] 连续多次滚动无新内容，停止采集")
                        break
                else:
                    no_new_items_count = 0
                    last_count = current_count
                
                # 智能滚动
                await self._smart_scroll()
                await asyncio.sleep(scroll_delay)
                scroll_count += 1
                
                print(f"[INFO] 滚动 {scroll_count}/{max_scrolls}, 已采集 {len(collected_data)} 项")
            
            print(f"[INFO] 智能采集完成，共采集 {len(collected_data)} 项数据")
            return collected_data
            
        except Exception as e:
            print(f"[ERROR] 智能采集失败: {e}")
            return collected_data
        
    async def initialize(self):
        """初始化采集器"""
        try:
            self.logger.info("初始化智能采集器...")
            
            # 分析页面结构
            await self.analyzer.analyze_page_structure()
            
            # 生成提取配置
            self.extraction_config = await self.analyzer.generate_extraction_config()
            
            self.logger.info("智能采集器初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化智能采集器失败: {e}")
            raise
    
    async def smart_scroll_and_collect(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """智能滚动并采集数据"""
        try:
            if not self.extraction_config:
                await self.initialize()
            
            collected_data = []
            scroll_config = self.extraction_config.get('scroll_config', {})
            extraction_rules = self.extraction_config.get('extraction_rules', {})
            
            list_selector = extraction_rules.get('list_selector', '')
            if not list_selector:
                raise Exception("未找到有效的列表选择器")
            
            self.logger.info(f"开始智能采集，目标: {max_items} 条数据")
            
            scroll_count = 0
            max_scrolls = scroll_config.get('max_scrolls', 50)
            scroll_delay = scroll_config.get('scroll_delay', 2000) / 1000  # 转换为秒
            
            last_count = 0
            no_new_data_count = 0
            
            while len(collected_data) < max_items and scroll_count < max_scrolls:
                # 获取当前页面的所有列表项
                current_items = await self.page.query_selector_all(list_selector)
                
                # 提取新数据
                for i, item in enumerate(current_items):
                    if len(collected_data) >= max_items:
                        break
                    
                    # 检查是否已经处理过这个元素
                    item_data = await self._extract_item_data(item, i)
                    if item_data and not self._is_duplicate(item_data, collected_data):
                        collected_data.append(item_data)
                        self.logger.info(f"采集到第 {len(collected_data)} 条数据")
                
                # 检查是否有新数据
                if len(collected_data) == last_count:
                    no_new_data_count += 1
                    if no_new_data_count >= 3:  # 连续3次没有新数据就停止
                        self.logger.info("连续多次滚动未发现新数据，停止采集")
                        break
                else:
                    no_new_data_count = 0
                    last_count = len(collected_data)
                
                # 如果还需要更多数据，继续滚动
                if len(collected_data) < max_items:
                    await self._smart_scroll()
                    scroll_count += 1
                    await asyncio.sleep(scroll_delay)
            
            self.logger.info(f"智能采集完成，共采集 {len(collected_data)} 条数据，滚动 {scroll_count} 次")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"智能采集失败: {e}")
            return []
    
    async def _extract_item_data(self, item_element, data_fields: Dict, index: int) -> Dict:
        """
        从单个项目元素中提取数据
        
        Args:
            item_element: 项目DOM元素
            data_fields: 数据字段配置
            index: 项目索引
            
        Returns:
            提取的数据字典
        """
        try:
            item_data = {
                'index': index,
                'content': '',
                'metadata': {},
                'interactions': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # 提取文本内容
            text_selectors = data_fields.get('text_content', [])
            for selector in text_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and text.strip():
                            item_data['content'] = text.strip()
                            break
                except:
                    continue
            
            # 提取链接
            link_selectors = data_fields.get('links', [])
            for selector in link_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        href = await element.get_attribute('href')
                        if href:
                            item_data['metadata']['link'] = href
                            break
                except:
                    continue
            
            # 提取用户名（如果是Twitter）
            username_selectors = [
                '[data-testid="User-Name"] span',
                '.username',
                '[data-testid="User-Names"] span',
                'a[href*="/"] span'
            ]
            for selector in username_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        username = await element.inner_text()
                        if username and username.strip():
                            item_data['metadata']['username'] = username.strip()
                            break
                except:
                    continue
            
            # 提取时间信息
            time_selectors = [
                'time',
                '[datetime]',
                '.time',
                '[data-testid="Time"]'
            ]
            for selector in time_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        time_text = await element.inner_text()
                        datetime_attr = await element.get_attribute('datetime')
                        if datetime_attr:
                            item_data['metadata']['publish_time'] = datetime_attr
                        elif time_text:
                            item_data['metadata']['publish_time'] = time_text.strip()
                        break
                except:
                    continue
            
            # 提取交互数据（点赞、评论、转发）
            interaction_selectors = {
                'likes': ['[data-testid="like"]', '.like-count', '[aria-label*="like"]'],
                'comments': ['[data-testid="reply"]', '.comment-count', '[aria-label*="repl"]'],
                'retweets': ['[data-testid="retweet"]', '.retweet-count', '[aria-label*="retweet"]']
            }
            
            for interaction_type, selectors in interaction_selectors.items():
                for selector in selectors:
                    try:
                        element = await item_element.query_selector(selector)
                        if element:
                            # 尝试从aria-label获取数字
                            aria_label = await element.get_attribute('aria-label')
                            if aria_label:
                                import re
                                numbers = re.findall(r'\d+', aria_label)
                                if numbers:
                                    item_data['interactions'][interaction_type] = int(numbers[0])
                                    break
                            
                            # 尝试从文本内容获取数字
                            text = await element.inner_text()
                            if text:
                                numbers = re.findall(r'\d+', text)
                                if numbers:
                                    item_data['interactions'][interaction_type] = int(numbers[0])
                                    break
                    except:
                        continue
            
            # 只返回有内容的项目
            if item_data['content']:
                return item_data
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] 提取项目数据失败: {e}")
            return None
    
    async def _extract_text_content(self, element: ElementHandle, selectors: List[str]) -> str:
        """提取文本内容"""
        for selector in selectors:
            try:
                text_element = await element.query_selector(selector)
                if text_element:
                    text = await text_element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        return ''
    
    async def _extract_links(self, element: ElementHandle, selectors: List[str]) -> List[str]:
        """提取链接"""
        links = []
        for selector in selectors:
            try:
                link_elements = await element.query_selector_all(selector)
                for link_element in link_elements:
                    href = await link_element.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            href = f"https://x.com{href}"
                        links.append(href)
            except Exception:
                continue
        return list(set(links))  # 去重
    
    async def _extract_metadata(self, element: ElementHandle, selectors: List[str]) -> Dict[str, str]:
        """提取元数据"""
        metadata = {}
        
        # 提取用户名
        username_selectors = ['[data-testid="User-Name"] a', '[data-testid="User-Names"] a']
        for selector in username_selectors:
            try:
                user_element = await element.query_selector(selector)
                if user_element:
                    href = await user_element.get_attribute('href')
                    if href and '/' in href:
                        metadata['username'] = href.split('/')[-1]
                        break
            except Exception:
                continue
        
        # 提取时间
        for selector in selectors:
            if 'time' in selector:
                try:
                    time_element = await element.query_selector(selector)
                    if time_element:
                        datetime_attr = await time_element.get_attribute('datetime')
                        if datetime_attr:
                            metadata['publish_time'] = datetime_attr
                            break
                except Exception:
                    continue
        
        return metadata
    
    async def _extract_interactions(self, element: ElementHandle, selectors: List[str]) -> Dict[str, int]:
        """提取交互数据"""
        interactions = {'likes': 0, 'comments': 0, 'retweets': 0}
        
        interaction_map = {
            'like': 'likes',
            'reply': 'comments',
            'retweet': 'retweets'
        }
        
        for selector in selectors:
            for interaction_type, key in interaction_map.items():
                if interaction_type in selector:
                    try:
                        interaction_element = await element.query_selector(selector)
                        if interaction_element:
                            aria_label = await interaction_element.get_attribute('aria-label') or ''
                            number = self._extract_number_from_text(aria_label)
                            interactions[key] = number
                    except Exception:
                        continue
        
        return interactions
    
    async def _extract_images(self, element: ElementHandle, selectors: List[str]) -> List[str]:
        """提取图片"""
        images = []
        for selector in selectors:
            try:
                img_elements = await element.query_selector_all(selector)
                for img_element in img_elements:
                    src = await img_element.get_attribute('src')
                    if src:
                        images.append(src)
            except Exception:
                continue
        return images
    
    def _extract_number_from_text(self, text: str) -> int:
        """从文本中提取数字"""
        if not text:
            return 0
        
        text = text.replace(',', '').replace(' ', '').lower()
        match = re.search(r'([0-9.]+)([km]?)', text)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        if unit == 'k':
            return int(number * 1000)
        elif unit == 'm':
            return int(number * 1000000)
        else:
            return int(number)
    
    def _is_duplicate(self, new_data: Dict[str, Any], existing_data: List[Dict[str, Any]]) -> bool:
        """检查是否重复数据"""
        new_content = new_data.get('content', '')
        new_links = new_data.get('links', [])
        
        for existing in existing_data:
            existing_content = existing.get('content', '')
            existing_links = existing.get('links', [])
            
            # 如果内容相同或链接相同，认为是重复
            if new_content and new_content == existing_content:
                return True
            if new_links and existing_links and any(link in existing_links for link in new_links):
                return True
        
        return False
    
    async def _smart_scroll(self):
        """
        智能滚动，模拟人类行为
        """
        try:
            # 随机滚动距离
            scroll_distance = random.randint(300, 800)
            
            # 执行滚动
            await self.page.evaluate(f"""
                window.scrollBy(0, {scroll_distance});
            """)
            
            # 随机停顿
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 有时候向上滚动一点，模拟真实阅读行为
            if random.random() < 0.1:  # 10%的概率
                back_scroll = random.randint(50, 150)
                await self.page.evaluate(f"""
                    window.scrollBy(0, -{back_scroll});
                """)
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
        except Exception as e:
            print(f"[ERROR] 智能滚动失败: {e}")

# 使用示例
if __name__ == "__main__":
    async def demo():
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # 导航到Twitter
                await page.goto('https://x.com')
                await page.wait_for_load_state('networkidle')
                
                # 创建智能采集器
                scraper = IntelligentScraper(page)
                await scraper.initialize()
                
                # 开始采集
                data = await scraper.smart_scroll_and_collect(max_items=20)
                
                print(f"采集到 {len(data)} 条数据")
                for i, item in enumerate(data[:5]):
                    print(f"\n第 {i+1} 条:")
                    print(f"内容: {item.get('content', '')[:100]}...")
                    print(f"用户: {item.get('metadata', {}).get('username', 'unknown')}")
                    print(f"链接: {item.get('links', [])}")
                
            finally:
                await browser.close()
    
    asyncio.run(demo())