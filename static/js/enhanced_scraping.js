// 增强推文抓取页面交互逻辑

let currentTaskId = null;
let progressInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    bindEvents();
    loadStatistics();
});

function initializePage() {
    console.log('增强推文抓取页面初始化');
}

function bindEvents() {
    // 绑定表单提交事件
    document.getElementById('enhancedScrapingForm').addEventListener('submit', handleFormSubmit);
}

function handleFormSubmit(event) {
    event.preventDefault();
    
    if (currentTaskId) {
        showAlert('当前有任务正在运行，请等待完成后再启动新任务', 'warning');
        return;
    }
    
    startEnhancedScraping();
}

function startEnhancedScraping() {
    // 获取表单数据
    const targetAccounts = document.getElementById('targetAccounts').value
        .split('\n')
        .map(account => account.trim())
        .filter(account => account.length > 0);
    
    const targetKeywords = document.getElementById('targetKeywords').value
        .split('\n')
        .map(keyword => keyword.trim())
        .filter(keyword => keyword.length > 0);
    
    const maxTweets = parseInt(document.getElementById('maxTweets').value) || 20;
    const enableDetails = document.getElementById('enableDetails').checked;
    const taskName = document.getElementById('taskName').value.trim();
    
    // 验证输入
    if (targetAccounts.length === 0 && targetKeywords.length === 0) {
        showAlert('请至少输入一个目标账号或关键词', 'danger');
        return;
    }
    
    // 准备请求数据
    const requestData = {
        target_accounts: targetAccounts,
        target_keywords: targetKeywords,
        max_tweets: maxTweets,
        enable_details: enableDetails,
        task_name: taskName
    };
    
    // 显示加载状态
    const startButton = document.getElementById('startButton');
    startButton.disabled = true;
    startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 启动中...';
    
    // 发送请求
    fetch('/api/start-enhanced-scraping', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentTaskId = data.task_id;
            showAlert(data.message, 'success');
            showProgressContainer();
            startProgressMonitoring();
        } else {
            showAlert('启动失败: ' + data.error, 'danger');
            resetStartButton();
        }
    })
    .catch(error => {
        console.error('启动增强抓取失败:', error);
        showAlert('启动失败: ' + error.message, 'danger');
        resetStartButton();
    });
}

function showProgressContainer() {
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('dataPreview').style.display = 'block';
}

function startProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(() => {
        if (currentTaskId) {
            updateProgress();
        }
    }, 10000); // 每10秒更新一次（减少服务器负载）
    
    // 立即更新一次
    updateProgress();
}

function updateProgress() {
    if (!currentTaskId) return;
    
    fetch(`/api/enhanced-scraping-progress/${currentTaskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const taskData = data.data;
                updateProgressDisplay(taskData);
                
                if (taskData.status === 'completed' || taskData.status === 'failed') {
                    stopProgressMonitoring();
                    resetStartButton();
                    
                    if (taskData.status === 'completed') {
                        showAlert(`抓取完成！共收集 ${taskData.collected_count} 条推文，其中 ${taskData.details_scraped} 条进行了详情抓取`, 'success');
                        loadStatistics(); // 重新加载统计数据
                    } else {
                        showAlert('抓取失败: ' + taskData.error, 'danger');
                    }
                }
            }
        })
        .catch(error => {
            console.error('获取进度失败:', error);
        });
}

function updateProgressDisplay(taskData) {
    // 更新数字显示
    document.getElementById('collectedCount').textContent = taskData.collected_count || 0;
    document.getElementById('detailsScraped').textContent = taskData.details_scraped || 0;
    document.getElementById('targetCount').textContent = taskData.target_count || 0;
    
    // 计算进度百分比
    const progress = taskData.target_count > 0 ? 
        Math.round((taskData.collected_count / taskData.target_count) * 100) : 0;
    document.getElementById('progressPercent').textContent = progress + '%';
    
    // 更新进度条
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = progress + '%';
    progressBar.setAttribute('aria-valuenow', progress);
    
    // 更新状态徽章
    const statusBadge = document.getElementById('statusBadge');
    const statusMap = {
        'running': { text: '运行中', class: 'bg-primary' },
        'completed': { text: '已完成', class: 'bg-success' },
        'failed': { text: '失败', class: 'bg-danger' }
    };
    
    const status = statusMap[taskData.status] || statusMap['running'];
    statusBadge.textContent = status.text;
    statusBadge.className = `badge ${status.class} ms-2`;
    
    // 显示错误信息
    const errorMessage = document.getElementById('errorMessage');
    if (taskData.error) {
        errorMessage.textContent = taskData.error;
        errorMessage.style.display = 'block';
    } else {
        errorMessage.style.display = 'none';
    }
    
    // 更新最新数据预览
    if (taskData.latest_data && taskData.latest_data.length > 0) {
        updateDataPreview(taskData.latest_data);
    }
}

function updateDataPreview(tweets) {
    const container = document.getElementById('latestTweets');
    container.innerHTML = '';
    
    tweets.forEach(tweet => {
        const tweetElement = createTweetPreview(tweet);
        container.appendChild(tweetElement);
    });
}

function createTweetPreview(tweet) {
    const div = document.createElement('div');
    div.className = 'tweet-preview';
    
    // 构建推文HTML
    let html = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
                <strong>@${tweet.username || '未知用户'}</strong>
                ${tweet.has_detailed_content ? '<span class="enhancement-badge">增强</span>' : ''}
            </div>
            <small class="text-muted">${tweet.source || ''}</small>
        </div>
        <div class="mb-2">
            ${tweet.full_content || tweet.content || '无内容'}
        </div>
    `;
    
    // 添加多媒体内容
    if (tweet.media && tweet.media.length > 0) {
        html += '<div class="mb-2">';
        tweet.media.forEach(media => {
            html += `<span class="media-item">
                <i class="fas fa-${getMediaIcon(media.type)}"></i> ${media.type}
            </span>`;
        });
        html += '</div>';
    }
    
    // 添加线程指示
    if (tweet.thread && tweet.thread.length > 0) {
        html += `<div class="thread-indicator">
            <i class="fas fa-list"></i> 包含 ${tweet.thread.length} 条线程推文
        </div>`;
    }
    
    // 添加引用推文
    if (tweet.quoted_tweet) {
        html += `<div class="quoted-tweet">
            <small><i class="fas fa-quote-left"></i> 引用推文:</small><br>
            <strong>@${tweet.quoted_tweet.username}</strong>: ${tweet.quoted_tweet.content}
        </div>`;
    }
    
    // 添加统计信息
    html += `
        <div class="d-flex justify-content-between text-muted small">
            <div>
                <i class="fas fa-heart"></i> ${tweet.likes || 0}
                <i class="fas fa-comment ms-2"></i> ${tweet.comments || 0}
                <i class="fas fa-retweet ms-2"></i> ${tweet.retweets || 0}
                ${tweet.account_type ? `<span class="account-type ${tweet.account_type} ms-2" title="账号类型">${tweet.account_type}</span>` : ''}
            </div>
            <div>${tweet.publish_time || ''}</div>
        </div>
    `;
    
    div.innerHTML = html;
    return div;
}

function getMediaIcon(mediaType) {
    const iconMap = {
        'image': 'image',
        'video': 'video',
        'gif': 'film'
    };
    return iconMap[mediaType] || 'file';
}

function stopProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    currentTaskId = null;
}

function resetStartButton() {
    const startButton = document.getElementById('startButton');
    startButton.disabled = false;
    startButton.innerHTML = '<i class="fas fa-play"></i> 开始抓取';
}

function loadStatistics() {
    // 加载统计数据
    fetch('/api/tasks')
        .then(response => response.json())
        .then(tasks => {
            document.getElementById('totalTasks').textContent = tasks.length;
            
            // 计算总推文数
            const totalTweets = tasks.reduce((sum, task) => sum + (task.result_count || 0), 0);
            document.getElementById('totalTweets').textContent = totalTweets;
        })
        .catch(error => {
            console.error('加载统计数据失败:', error);
        });
}

function showAlert(message, type = 'info') {
    // 创建警告框
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到页面顶部
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    stopProgressMonitoring();
});