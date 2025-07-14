# -*- coding: utf-8 -*-
"""
人工行为模拟器
模拟真实用户的浏览行为，包括滚动、点击、鼠标移动等操作
"""

import asyncio
import random
import logging
from typing import Optional, List, Dict, Any
from playwright.async_api import Page

class HumanBehaviorSimulator:
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 人工行为参数配置
        self.scroll_speeds = [200, 300, 400, 500, 600]  # 不同的滚动速度
        self.pause_times = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # 随机停顿时间
        self.reading_times = [2, 3, 4, 5, 6, 8, 10]  # 模拟阅读时间
        
    async def random_pause(self, min_time: float = 0.5, max_time: float = 3.0):
        """随机停顿，模拟人类思考时间"""
        pause_time = random.uniform(min_time, max_time)
        await asyncio.sleep(pause_time)
        
    async def simulate_mouse_movement(self):
        """模拟鼠标随机移动"""
        try:
            # 获取页面尺寸
            viewport = await self.page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            
            # 随机移动鼠标
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            await self.page.mouse.move(x, y)
            await self.random_pause(0.1, 0.3)
            
        except Exception as e:
            self.logger.debug(f"鼠标移动模拟失败: {e}")
    
    async def simulate_reading_behavior(self, element=None):
        """模拟阅读行为"""
        try:
            # 如果有指定元素，将鼠标移动到元素上
            if element:
                box = await element.bounding_box()
                if box:
                    # 移动到元素中心附近的随机位置
                    x = box['x'] + random.randint(10, int(box['width'] - 10))
                    y = box['y'] + random.randint(10, int(box['height'] - 10))
                    await self.page.mouse.move(x, y)
            
            # 模拟阅读时间
            reading_time = random.choice(self.reading_times)
            await asyncio.sleep(reading_time)
            
        except Exception as e:
            self.logger.debug(f"阅读行为模拟失败: {e}")
    
    async def human_like_scroll(self, direction: str = 'down', distance: int = None):
        """模拟人类滚动行为"""
        try:
            # 随机选择滚动距离
            if distance is None:
                distance = random.choice(self.scroll_speeds)
            
            # 根据方向调整距离
            if direction == 'up':
                distance = -distance
            
            # 模拟不均匀的滚动（分几次完成）
            scroll_steps = random.randint(2, 4)
            step_distance = distance // scroll_steps
            
            for i in range(scroll_steps):
                await self.page.evaluate(f'window.scrollBy(0, {step_distance})')
                await self.random_pause(0.1, 0.3)
            
            # 滚动后的停顿
            await self.random_pause(0.5, 2.0)
            
        except Exception as e:
            self.logger.error(f"滚动模拟失败: {e}")
    
    async def simulate_tweet_interaction(self, tweet_element):
        """模拟与推文的交互"""
        try:
            # 移动鼠标到推文上
            await self.simulate_reading_behavior(tweet_element)
            
            # 随机决定是否进行交互
            interaction_chance = random.random()
            
            if interaction_chance < 0.1:  # 10%概率点击推文
                await tweet_element.click()
                await self.random_pause(1, 3)
                # 返回上一页
                await self.page.go_back()
                await self.random_pause(1, 2)
                
            elif interaction_chance < 0.2:  # 10%概率悬停在推文上
                await tweet_element.hover()
                await self.random_pause(1, 2)
            
        except Exception as e:
            self.logger.debug(f"推文交互模拟失败: {e}")
    
    async def simulate_page_exploration(self):
        """模拟页面探索行为"""
        try:
            # 随机滚动到页面不同位置
            actions = [
                lambda: self.human_like_scroll('down', random.randint(200, 800)),
                lambda: self.human_like_scroll('up', random.randint(100, 400)),
                lambda: self.simulate_mouse_movement(),
                lambda: self.random_pause(1, 3)
            ]
            
            # 执行3-6个随机动作
            num_actions = random.randint(3, 6)
            for _ in range(num_actions):
                action = random.choice(actions)
                await action()
                
        except Exception as e:
            self.logger.error(f"页面探索模拟失败: {e}")
    
    async def smart_scroll_and_collect(self, max_tweets: int = 10, target_selector: str = '[data-testid="tweet"]'):
        """智能滚动并收集推文，模拟真实用户行为"""
        collected_tweets = []
        scroll_attempts = 0
        max_scroll_attempts = max_tweets * 2  # 最大滚动次数
        
        try:
            self.logger.info(f"开始智能滚动收集，目标: {max_tweets} 条推文")
            
            while len(collected_tweets) < max_tweets and scroll_attempts < max_scroll_attempts:
                # 获取当前可见的推文
                current_tweets = await self.page.query_selector_all(target_selector)
                
                # 处理新发现的推文
                for i, tweet in enumerate(current_tweets):
                    if len(collected_tweets) >= max_tweets:
                        break
                        
                    # 检查推文是否已经处理过（简单的去重）
                    tweet_text = await tweet.inner_text() if tweet else ""
                    if tweet_text and not any(tweet_text in str(existing) for existing in collected_tweets):
                        # 模拟查看推文
                        await self.simulate_tweet_interaction(tweet)
                        
                        # 收集推文数据（这里只是示例，实际解析在其他地方）
                        collected_tweets.append({
                            'element': tweet,
                            'text_preview': tweet_text[:100],
                            'index': len(collected_tweets)
                        })
                        
                        self.logger.info(f"发现第 {len(collected_tweets)} 条推文")
                
                # 如果还需要更多推文，继续滚动
                if len(collected_tweets) < max_tweets:
                    await self.human_like_scroll('down')
                    scroll_attempts += 1
                    
                    # 偶尔向上滚动，模拟重新查看
                    if random.random() < 0.1:
                        await self.human_like_scroll('up', random.randint(100, 300))
                        await self.random_pause(1, 2)
                        await self.human_like_scroll('down', random.randint(200, 400))
            
            self.logger.info(f"智能滚动完成，收集到 {len(collected_tweets)} 条推文，滚动次数: {scroll_attempts}")
            return collected_tweets
            
        except Exception as e:
            self.logger.error(f"智能滚动收集失败: {e}")
            return collected_tweets
    
    async def simulate_user_session(self, duration_minutes: int = 5):
        """模拟完整的用户会话"""
        try:
            self.logger.info(f"开始模拟 {duration_minutes} 分钟的用户会话")
            
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + (duration_minutes * 60)
            
            while asyncio.get_event_loop().time() < end_time:
                # 随机选择行为
                behaviors = [
                    self.simulate_page_exploration,
                    lambda: self.human_like_scroll('down'),
                    lambda: self.human_like_scroll('up'),
                    self.simulate_mouse_movement,
                    lambda: self.random_pause(2, 5)
                ]
                
                behavior = random.choice(behaviors)
                await behavior()
                
                # 检查是否应该结束
                if random.random() < 0.05:  # 5%概率提前结束
                    break
            
            self.logger.info("用户会话模拟完成")
            
        except Exception as e:
            self.logger.error(f"用户会话模拟失败: {e}")
    
    async def simulate_natural_browsing(self, pages_to_visit: List[str]):
        """模拟自然的浏览行为，访问多个页面"""
        try:
            for i, url in enumerate(pages_to_visit):
                self.logger.info(f"访问第 {i+1} 个页面: {url}")
                
                # 导航到页面
                await self.page.goto(url, timeout=60000)
                await self.random_pause(2, 4)
                
                # 模拟页面浏览
                await self.simulate_page_exploration()
                
                # 在页面停留一段时间
                stay_time = random.randint(30, 120)  # 30-120秒
                await asyncio.sleep(stay_time)
                
                # 偶尔返回上一页
                if i > 0 and random.random() < 0.2:
                    await self.page.go_back()
                    await self.random_pause(1, 3)
                    await self.page.go_forward()
                    await self.random_pause(1, 2)
            
        except Exception as e:
            self.logger.error(f"自然浏览模拟失败: {e}")

# 使用示例
if __name__ == "__main__":
    async def demo():
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            simulator = HumanBehaviorSimulator(page)
            
            # 访问Twitter
            await page.goto('https://x.com')
            
            # 模拟用户行为
            await simulator.simulate_user_session(2)  # 2分钟会话
            
            await browser.close()
    
    asyncio.run(demo())