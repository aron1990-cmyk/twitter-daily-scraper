/**
 * 前端资源管理器
 * 负责清理定时器、事件监听器和内存对象，防止资源泄露
 */

class ResourceManager {
    constructor() {
        this.timers = new Set();
        this.intervals = new Set();
        this.eventListeners = new Map();
        this.abortControllers = new Set();
        this.observers = new Set();
        this.isPageUnloading = false;
        
        // 绑定页面卸载事件
        this.bindUnloadEvents();
        
        console.log('🔧 资源管理器已初始化');
    }
    
    /**
     * 创建受管理的定时器
     */
    setTimeout(callback, delay, ...args) {
        const timerId = setTimeout(() => {
            this.timers.delete(timerId);
            if (!this.isPageUnloading) {
                callback.apply(null, args);
            }
        }, delay);
        
        this.timers.add(timerId);
        return timerId;
    }
    
    /**
     * 创建受管理的间隔定时器
     */
    setInterval(callback, interval, ...args) {
        const intervalId = setInterval(() => {
            if (!this.isPageUnloading) {
                callback.apply(null, args);
            }
        }, interval);
        
        this.intervals.add(intervalId);
        return intervalId;
    }
    
    /**
     * 清除定时器
     */
    clearTimeout(timerId) {
        clearTimeout(timerId);
        this.timers.delete(timerId);
    }
    
    /**
     * 清除间隔定时器
     */
    clearInterval(intervalId) {
        clearInterval(intervalId);
        this.intervals.delete(intervalId);
    }
    
    /**
     * 添加受管理的事件监听器
     */
    addEventListener(element, event, handler, options = {}) {
        const wrappedHandler = (e) => {
            if (!this.isPageUnloading) {
                handler(e);
            }
        };
        
        element.addEventListener(event, wrappedHandler, options);
        
        const key = `${element.constructor.name}_${event}`;
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        
        this.eventListeners.get(key).push({
            element,
            event,
            handler: wrappedHandler,
            options
        });
        
        return wrappedHandler;
    }
    
    /**
     * 移除事件监听器
     */
    removeEventListener(element, event, handler, options = {}) {
        element.removeEventListener(event, handler, options);
        
        const key = `${element.constructor.name}_${event}`;
        const listeners = this.eventListeners.get(key);
        if (listeners) {
            const index = listeners.findIndex(l => 
                l.element === element && 
                l.event === event && 
                l.handler === handler
            );
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    /**
     * 创建受管理的AbortController
     */
    createAbortController() {
        const controller = new AbortController();
        this.abortControllers.add(controller);
        
        // 监听abort事件，自动从集合中移除
        controller.signal.addEventListener('abort', () => {
            this.abortControllers.delete(controller);
        }, { once: true });
        
        return controller;
    }
    
    /**
     * 创建受管理的Observer（MutationObserver, IntersectionObserver等）
     */
    createObserver(ObserverClass, callback, options) {
        const observer = new ObserverClass(callback, options);
        this.observers.add(observer);
        return observer;
    }
    
    /**
     * 安全的fetch请求（带超时和取消功能）
     */
    async safeFetch(url, options = {}) {
        const controller = this.createAbortController();
        const timeout = options.timeout || 10000;
        
        // 设置超时
        const timeoutId = this.setTimeout(() => {
            controller.abort();
            console.log(`请求超时: ${url}`);
        }, timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            this.clearTimeout(timeoutId);
            return response;
            
        } catch (error) {
            this.clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                console.log(`请求被取消: ${url}`);
            } else {
                console.error(`请求失败: ${url}`, error);
            }
            throw error;
        }
    }
    
    /**
     * 绑定页面卸载事件
     */
    bindUnloadEvents() {
        // beforeunload事件
        window.addEventListener('beforeunload', () => {
            this.isPageUnloading = true;
            this.cleanup();
        });
        
        // pagehide事件（更可靠）
        window.addEventListener('pagehide', () => {
            this.isPageUnloading = true;
            this.cleanup();
        });
        
        // visibilitychange事件（页面隐藏时清理）
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.partialCleanup();
            }
        });
        
        // 页面错误时也进行清理
        window.addEventListener('error', () => {
            this.partialCleanup();
        });
    }
    
    /**
     * 部分清理（页面隐藏时）
     */
    partialCleanup() {
        try {
            // 取消所有进行中的请求
            this.abortControllers.forEach(controller => {
                if (!controller.signal.aborted) {
                    controller.abort();
                }
            });
            
            console.log('🧹 执行部分资源清理');
        } catch (error) {
            console.error('部分清理失败:', error);
        }
    }
    
    /**
     * 完全清理所有资源
     */
    cleanup() {
        try {
            console.log('🧹 开始清理所有资源...');
            
            // 清理定时器
            this.timers.forEach(timerId => {
                clearTimeout(timerId);
            });
            this.timers.clear();
            
            // 清理间隔定时器
            this.intervals.forEach(intervalId => {
                clearInterval(intervalId);
            });
            this.intervals.clear();
            
            // 清理事件监听器
            this.eventListeners.forEach(listeners => {
                listeners.forEach(({ element, event, handler, options }) => {
                    try {
                        element.removeEventListener(event, handler, options);
                    } catch (e) {
                        console.warn('移除事件监听器失败:', e);
                    }
                });
            });
            this.eventListeners.clear();
            
            // 取消所有AbortController
            this.abortControllers.forEach(controller => {
                if (!controller.signal.aborted) {
                    controller.abort();
                }
            });
            this.abortControllers.clear();
            
            // 断开所有Observer
            this.observers.forEach(observer => {
                try {
                    if (observer.disconnect) {
                        observer.disconnect();
                    }
                } catch (e) {
                    console.warn('断开Observer失败:', e);
                }
            });
            this.observers.clear();
            
            console.log('✅ 资源清理完成');
            
        } catch (error) {
            console.error('资源清理失败:', error);
        }
    }
    
    /**
     * 获取资源使用统计
     */
    getStats() {
        return {
            timers: this.timers.size,
            intervals: this.intervals.size,
            eventListeners: Array.from(this.eventListeners.values()).reduce((sum, arr) => sum + arr.length, 0),
            abortControllers: this.abortControllers.size,
            observers: this.observers.size,
            isPageUnloading: this.isPageUnloading
        };
    }
    
    /**
     * 检查内存使用情况
     */
    checkMemoryUsage() {
        if (performance.memory) {
            const memory = performance.memory;
            const usage = {
                used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024)
            };
            
            console.log('💾 内存使用情况:', usage);
            
            // 如果内存使用超过80%，触发垃圾回收提示
            if (usage.used / usage.limit > 0.8) {
                console.warn('⚠️ 内存使用率过高，建议刷新页面');
                this.partialCleanup();
            }
            
            return usage;
        }
        return null;
    }
}

// 创建全局资源管理器实例
window.resourceManager = new ResourceManager();

// 导出给其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResourceManager;
}

// 定期检查内存使用情况
window.resourceManager.setInterval(() => {
    window.resourceManager.checkMemoryUsage();
}, 60000); // 每分钟检查一次

console.log('🚀 前端资源管理器已加载');