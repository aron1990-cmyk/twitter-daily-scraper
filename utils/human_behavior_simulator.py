# -*- coding: utf-8 -*-
"""
人工行为模拟器
模拟真实用户的浏览行为，包括滚动、点击、鼠标移动等操作
"""

import asyncio
import random
import logging
import math
import time
from typing import Optional, List, Dict, Any, Tuple
from playwright.async_api import Page

class HumanBehaviorSimulator:
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 增强的人工行为参数配置
        self.scroll_speeds = [600, 800, 1000, 1200, 1500]  # 更自然的滚动速度
        self.pause_times = [0.1, 0.2, 0.3, 0.5, 0.8]  # 更自然的停顿时间
        self.reading_times = [0.5, 1.0, 1.5, 2.0, 3.0]  # 更真实的阅读时间
        
        # 鼠标移动轨迹参数
        self.mouse_speed_range = (50, 150)  # 鼠标移动速度范围(像素/秒)
        self.curve_intensity = 0.3  # 曲线强度
        
        # 页面状态跟踪
        self.last_scroll_time = 0
        self.scroll_momentum = 0
        self.page_load_start_time = time.time()
        
        # 行为模式配置
        self.interaction_probability = {
            'hover': 0.15,  # 悬停概率
            'click_safe_area': 0.05,  # 点击安全区域概率
            'scroll_back': 0.08,  # 向上滚动概率
            'pause_reading': 0.25,  # 阅读停顿概率
        }
        
    async def random_pause(self, min_time: float = 0.1, max_time: float = 0.8):
        """智能随机停顿，基于页面状态和用户行为模式"""
        # 基础停顿时间
        base_pause = random.uniform(min_time, max_time)
        
        # 根据页面加载状态调整
        page_age = time.time() - self.page_load_start_time
        if page_age < 3:  # 页面刚加载，需要更多时间
            base_pause *= 1.5
        
        # 根据滚动频率调整
        time_since_last_scroll = time.time() - self.last_scroll_time
        if time_since_last_scroll < 1:  # 频繁滚动，增加停顿
            base_pause *= 1.3
        
        # 添加微小的随机波动，模拟人类不规律性
        jitter = random.uniform(-0.1, 0.1)
        final_pause = max(0.05, base_pause + jitter)
        
        await asyncio.sleep(final_pause)
        
    async def simulate_mouse_movement(self, target_x: int = None, target_y: int = None):
        """模拟真实的鼠标移动轨迹"""
        try:
            # 获取页面尺寸和当前鼠标位置
            viewport = await self.page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            
            # 确定目标位置
            if target_x is None or target_y is None:
                target_x = random.randint(100, viewport['width'] - 100)
                target_y = random.randint(100, viewport['height'] - 100)
            
            # 生成贝塞尔曲线路径
            path_points = self._generate_mouse_path(target_x, target_y, viewport)
            
            # 沿路径移动鼠标
            for point in path_points:
                await self.page.mouse.move(point[0], point[1])
                await asyncio.sleep(random.uniform(0.01, 0.03))  # 微小延迟
            
            # 到达目标后的微小停顿
            await self.random_pause(0.05, 0.2)
            
        except Exception as e:
            self.logger.debug(f"鼠标移动模拟失败: {e}")
    
    def _generate_mouse_path(self, target_x: int, target_y: int, viewport: dict) -> List[Tuple[int, int]]:
        """生成自然的鼠标移动路径"""
        # 假设当前位置在屏幕中心
        start_x = viewport['width'] // 2
        start_y = viewport['height'] // 2
        
        # 计算距离和步数
        distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
        steps = max(10, int(distance / 20))  # 每20像素一个步骤
        
        path_points = []
        
        for i in range(steps + 1):
            t = i / steps
            
            # 贝塞尔曲线插值
            control_x = start_x + (target_x - start_x) * 0.5 + random.randint(-50, 50)
            control_y = start_y + (target_y - start_y) * 0.5 + random.randint(-30, 30)
            
            # 二次贝塞尔曲线
            x = int((1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * target_x)
            y = int((1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * target_y)
            
            # 添加微小的随机抖动
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)
            
            path_points.append((x, y))
        
        return path_points
    
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
            
            # 模拟极短阅读时间
            reading_time = random.choice(self.reading_times)
            await asyncio.sleep(reading_time)
            
        except Exception as e:
            self.logger.debug(f"阅读行为模拟失败: {e}")
    
    async def human_like_scroll(self, direction: str = 'down', distance: int = None):
        """模拟真实的人类滚动行为"""
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            # 智能选择滚动距离
            if distance is None:
                # 根据滚动动量调整距离
                base_distance = random.choice(self.scroll_speeds)
                if self.scroll_momentum > 0:
                    # 有动量时，距离稍大
                    distance = int(base_distance * random.uniform(1.1, 1.4))
                else:
                    # 初始滚动，距离较小
                    distance = int(base_distance * random.uniform(0.7, 1.0))
            
            # 根据方向调整距离
            if direction == 'up':
                distance = -distance
                self.scroll_momentum = max(0, self.scroll_momentum - 1)  # 减少动量
            else:
                self.scroll_momentum = min(5, self.scroll_momentum + 1)  # 增加动量
            
            # 模拟真实的滚动模式
            await self._execute_natural_scroll(distance)
            
            # 更新滚动时间
            self.last_scroll_time = time.time()
            
            # 滚动后的智能停顿
            await self._post_scroll_behavior()
            
        except Exception as e:
            self.logger.error(f"滚动模拟失败: {e}")
    
    async def _execute_natural_scroll(self, total_distance: int):
        """执行自然的滚动动作"""
        # 模拟真实用户的滚动模式：快速滚动 + 微调
        scroll_patterns = [
            'smooth_continuous',  # 平滑连续滚动
            'burst_scroll',       # 突发式滚动
            'stepped_scroll'      # 阶梯式滚动
        ]
        
        pattern = random.choice(scroll_patterns)
        
        if pattern == 'smooth_continuous':
            # 平滑连续滚动
            steps = random.randint(8, 15)
            for i in range(steps):
                step_distance = total_distance // steps
                # 添加速度变化
                if i < steps // 3:
                    step_distance = int(step_distance * 0.8)  # 开始慢
                elif i > 2 * steps // 3:
                    step_distance = int(step_distance * 0.9)  # 结束慢
                
                await self.page.evaluate(f'window.scrollBy(0, {step_distance})')
                await asyncio.sleep(random.uniform(0.02, 0.05))
        
        elif pattern == 'burst_scroll':
            # 突发式滚动
            bursts = random.randint(2, 4)
            for i in range(bursts):
                burst_distance = total_distance // bursts
                await self.page.evaluate(f'window.scrollBy(0, {burst_distance})')
                if i < bursts - 1:  # 最后一次不停顿
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        
        else:  # stepped_scroll
            # 阶梯式滚动
            steps = random.randint(3, 6)
            for i in range(steps):
                step_distance = total_distance // steps
                await self.page.evaluate(f'window.scrollBy(0, {step_distance})')
                await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def _post_scroll_behavior(self):
        """滚动后的行为模拟"""
        # 随机决定滚动后的行为
        behavior_chance = random.random()
        
        if behavior_chance < self.interaction_probability['pause_reading']:
            # 停顿阅读
            await self.random_pause(0.5, 2.0)
        elif behavior_chance < self.interaction_probability['pause_reading'] + 0.1:
            # 微调滚动
            micro_scroll = random.randint(50, 150)
            if random.random() < 0.5:
                micro_scroll = -micro_scroll
            await self.page.evaluate(f'window.scrollBy(0, {micro_scroll})')
            await self.random_pause(0.2, 0.5)
        else:
            # 正常短暂停顿
            await self.random_pause(0.1, 0.4)
    
    async def simulate_tweet_interaction(self, tweet_element):
        """模拟与推文的真实交互行为"""
        try:
            interaction_chance = random.random()
            
            if interaction_chance < self.interaction_probability['hover']:
                # 悬停在推文上，模拟阅读
                await tweet_element.hover()
                await self.simulate_reading_behavior(tweet_element)
                
                # 可能的进一步交互
                further_action = random.random()
                if further_action < 0.3:
                    # 移动鼠标到推文内的不同位置
                    box = await tweet_element.bounding_box()
                    if box:
                        # 随机移动到推文内的位置
                        inner_x = int(box['x'] + random.uniform(0.2, 0.8) * box['width'])
                        inner_y = int(box['y'] + random.uniform(0.3, 0.7) * box['height'])
                        await self.simulate_mouse_movement(inner_x, inner_y)
                        await self.random_pause(0.3, 0.8)
                
            elif interaction_chance < self.interaction_probability['hover'] + 0.05:
                # 快速扫视（快速悬停后离开）
                await tweet_element.hover()
                await self.random_pause(0.1, 0.3)
                # 移动鼠标离开
                box = await tweet_element.bounding_box()
                if box:
                    away_x = int(box['x'] + box['width'] + random.randint(20, 100))
                    away_y = int(box['y'] + random.randint(-50, 50))
                    await self.simulate_mouse_movement(away_x, away_y)
            
        except Exception as e:
            self.logger.debug(f"推文交互模拟失败: {e}")
    
    async def simulate_page_exploration(self):
        """模拟真实的页面探索行为"""
        try:
            # 确保页面焦点
            await self.ensure_page_focus()
            
            # 更丰富的探索行为
            exploration_actions = [
                self._explore_scroll_pattern,
                self._explore_mouse_scanning,
                self._explore_reading_pause,
                self._explore_content_focus,
            ]
            
            # 执行2-4个探索动作
            num_actions = random.randint(2, 4)
            selected_actions = random.sample(exploration_actions, min(num_actions, len(exploration_actions)))
            
            for action in selected_actions:
                await action()
                await self.random_pause(0.2, 0.6)
                
        except Exception as e:
            self.logger.error(f"页面探索模拟失败: {e}")
    
    async def _explore_scroll_pattern(self):
        """探索性滚动模式"""
        # 随机选择滚动模式
        patterns = ['gentle_browse', 'quick_scan', 'focused_read']
        pattern = random.choice(patterns)
        
        if pattern == 'gentle_browse':
            # 温和浏览：小幅滚动 + 停顿
            for _ in range(random.randint(2, 4)):
                await self.human_like_scroll('down', random.randint(300, 600))
                await self.random_pause(0.8, 1.5)
        
        elif pattern == 'quick_scan':
            # 快速扫描：大幅滚动
            await self.human_like_scroll('down', random.randint(800, 1200))
            await self.random_pause(0.3, 0.6)
            # 可能回滚查看
            if random.random() < self.interaction_probability['scroll_back']:
                await self.human_like_scroll('up', random.randint(200, 400))
                await self.random_pause(0.5, 1.0)
        
        else:  # focused_read
            # 专注阅读：小幅滚动 + 长停顿
            await self.human_like_scroll('down', random.randint(200, 400))
            await self.random_pause(1.5, 3.0)
    
    async def _explore_mouse_scanning(self):
        """鼠标扫描行为"""
        viewport = await self.page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
        
        # 模拟视线扫描路径
        scan_points = [
            (viewport['width'] * 0.2, viewport['height'] * 0.3),
            (viewport['width'] * 0.8, viewport['height'] * 0.4),
            (viewport['width'] * 0.5, viewport['height'] * 0.6),
            (viewport['width'] * 0.3, viewport['height'] * 0.8),
        ]
        
        for point in scan_points:
            await self.simulate_mouse_movement(int(point[0]), int(point[1]))
            await self.random_pause(0.2, 0.5)
    
    async def _explore_reading_pause(self):
        """阅读停顿行为"""
        # 模拟在某个位置停下来仔细阅读
        await self.random_pause(1.0, 2.5)
        
        # 可能的微小鼠标移动，模拟阅读时的注意力转移
        for _ in range(random.randint(1, 3)):
            viewport = await self.page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            x = random.randint(int(viewport['width'] * 0.3), int(viewport['width'] * 0.7))
            y = random.randint(int(viewport['height'] * 0.4), int(viewport['height'] * 0.6))
            await self.simulate_mouse_movement(x, y)
            await self.random_pause(0.3, 0.8)
    
    async def _explore_content_focus(self):
        """内容聚焦行为"""
        try:
            # 寻找推文元素进行聚焦
            tweet_elements = await self.page.query_selector_all('[data-testid="tweet"]')
            if tweet_elements:
                # 随机选择一个推文进行聚焦
                target_tweet = random.choice(tweet_elements[:5])  # 只考虑前5个可见推文
                await self.simulate_tweet_interaction(target_tweet)
        except Exception as e:
            self.logger.debug(f"内容聚焦失败: {e}")
    
    async def ensure_page_focus(self):
        """
        确保页面获得焦点，处理页面被切换出去的情况
        """
        try:
            # 检查页面是否可见
            is_visible = await self.page.evaluate('!document.hidden')
            if not is_visible:
                self.logger.info("检测到页面失去焦点，尝试恢复...")
                
                # 尝试将页面带到前台
                await self.page.bring_to_front()
                await asyncio.sleep(1)
                
                # 使用更安全的方式恢复焦点，避免误点击链接
                try:
                    # 方法1：直接聚焦到页面
                    await self.page.evaluate('window.focus()')
                    await asyncio.sleep(0.3)
                    
                    # 方法2：如果还是没有焦点，尝试点击一个安全的区域（页面边缘）
                    is_visible = await self.page.evaluate('!document.hidden')
                    if not is_visible:
                        # 点击页面左上角的安全区域，避免点击到链接
                        await self.page.mouse.click(10, 10)
                        await asyncio.sleep(0.3)
                except Exception as focus_error:
                    self.logger.debug(f"焦点恢复操作失败: {focus_error}")
                
                # 再次检查
                is_visible = await self.page.evaluate('!document.hidden')
                if is_visible:
                    self.logger.info("页面焦点已恢复")
                else:
                    self.logger.warning("页面仍然失去焦点，但继续执行")
                    
        except Exception as e:
            self.logger.warning(f"页面焦点检查失败: {e}，继续执行")
    
    async def smart_scroll_and_collect(self, max_tweets: int = 10, target_selector: str = '[data-testid="tweet"]'):
        """智能滚动并收集推文，模拟真实用户行为"""
        collected_tweets = []
        scroll_attempts = 0
        max_scroll_attempts = max_tweets * 2  # 最大滚动次数
        
        try:
            self.logger.info(f"开始智能滚动收集，目标: {max_tweets} 条推文")
            
            while len(collected_tweets) < max_tweets and scroll_attempts < max_scroll_attempts:
                # 确保页面焦点
                await self.ensure_page_focus()
                
                # 获取当前可见的推文
                current_tweets = await self.page.query_selector_all(target_selector)
                
                # 处理新发现的推文
                for i, tweet in enumerate(current_tweets):
                    if len(collected_tweets) >= max_tweets:
                        break
                        
                    # 检查推文是否已经处理过（简单的去重）
                    try:
                        tweet_text = await tweet.inner_text() if tweet else ""
                        if tweet_text and not any(tweet_text in str(existing) for existing in collected_tweets):
                            # 极简模拟：跳过大部分交互，直接收集
                            if random.random() < 0.1:  # 仅10%概率进行交互
                                await self.simulate_tweet_interaction(tweet)
                            
                            # 收集推文数据（这里只是示例，实际解析在其他地方）
                            collected_tweets.append({
                                'element': tweet,
                                'text_preview': tweet_text[:100],
                                'index': len(collected_tweets)
                            })
                            
                            self.logger.info(f"发现第 {len(collected_tweets)} 条推文")
                    except Exception as e:
                        self.logger.debug(f"推文处理失败: {e}")
                
                # 如果还需要更多推文，继续滚动
                if len(collected_tweets) < max_tweets:
                    # 滚动前再次确保页面焦点
                    await self.ensure_page_focus()
                    await self.human_like_scroll('down')
                    scroll_attempts += 1
                    
                    # 极少向上滚动，减少不必要操作
                    if random.random() < 0.02:  # 仅2%概率
                        await self.ensure_page_focus()
                        await self.human_like_scroll('up', random.randint(100, 200))
                        await self.random_pause(0.1, 0.3)
                        await self.human_like_scroll('down', random.randint(200, 300))
            
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
                
                # 在页面停留一段时间（极速模式）
                stay_time = random.randint(1, 3)  # 1-3秒
                await asyncio.sleep(stay_time)
                
                # 跳过返回上一页操作（极速模式）
                pass
            
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