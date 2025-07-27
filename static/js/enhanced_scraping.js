/**
 * 增强推文抓取页面JavaScript
 * 实现推文抓取的交互逻辑
 * 兼容ES5语法
 */

// 全局变量
var progressInterval = null;
var isProgressRunning = false;

// 页面加载完成后初始化
$(document).ready(function() {
    try {
        initializePage();
        bindEvents();
        loadStats();
    } catch (error) {
        console.error('页面初始化错误:', error);
        showAlert('页面初始化失败，请刷新页面重试', 'danger');
    }
});

/**
 * 初始化页面
 */
function initializePage() {
    console.log('增强推文抓取页面初始化');
    
    // 检查必要的元素是否存在
    var requiredElements = [
        '#enhancedScrapeForm',
        '#alertContainer',
        '#progressContainer',
        '#dataPreview'
    ];
    
    for (var i = 0; i < requiredElements.length; i++) {
        var selector = requiredElements[i];
        if ($(selector).length === 0) {
            console.error('必要元素不存在: ' + selector);
        }
    }
    
    // 隐藏进度容器
    $('#progressContainer').hide();
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 表单提交
    $('#enhancedScrapeForm').submit(function(e) {
        e.preventDefault();
        startEnhancedScraping();
    });
    
    // 停止按钮
    $('#stopScrapeBtn').click(function() {
        stopProgressMonitoring();
        showAlert('抓取已停止', 'warning');
    });
}

/**
 * 启动增强抓取
 */
function startEnhancedScraping() {
    console.log('启动增强抓取');
    
    // 获取表单数据
    var formData = {
        keywords: $('#keywords').val().trim(),
        max_tweets: parseInt($('#maxTweets').val()) || 100,
        min_likes: parseInt($('#minLikes').val()) || 0,
        min_retweets: parseInt($('#minRetweets').val()) || 0,
        min_comments: parseInt($('#minComments').val()) || 0,
        date_from: $('#dateFrom').val(),
        date_to: $('#dateTo').val(),
        language: $('#language').val() || 'zh',
        include_replies: $('#includeReplies').is(':checked'),
        include_retweets: $('#includeRetweets').is(':checked')
    };
    
    // 验证必填字段
    if (!formData.keywords) {
        showAlert('请输入搜索关键词', 'warning');
        return;
    }
    
    // 禁用开始按钮
    var $startBtn = $('#startScrapeBtn');
    $startBtn.prop('disabled', true);
    $startBtn.html('<i class="fas fa-spinner fa-spin"></i> 启动中...');
    
    // 发送抓取请求
    $.ajax({
        url: '/api/enhanced-scrape',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData)
    })
        .done(function(response) {
            if (response && response.success) {
                showAlert('抓取任务已启动', 'success');
                showProgressContainer();
                startProgressMonitoring();
            } else {
                var errorMsg = response && response.error ? response.error : '启动失败';
                showAlert('启动抓取失败: ' + errorMsg, 'danger');
                resetStartButton();
            }
        })
        .fail(function(xhr, status, error) {
            console.error('请求失败:', status, error);
            showAlert('网络错误，请稍后重试', 'danger');
            resetStartButton();
        });
}

/**
 * 显示进度容器
 */
function showProgressContainer() {
    $('#progressContainer').show();
    $('#dataPreview').show();
}

/**
 * 启动进度监控
 */
function startProgressMonitoring() {
    if (isProgressRunning) {
        return;
    }
    
    isProgressRunning = true;
    updateProgress();
    
    // 每2秒更新一次进度
    progressInterval = setInterval(function() {
        updateProgress();
    }, 2000);
}

/**
 * 更新进度
 */
function updateProgress() {
    $.ajax({
        url: '/api/scrape-progress',
        method: 'GET',
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success) {
                updateProgressDisplay(response.data);
                updateDataPreview(response.data);
                
                // 如果抓取完成，停止监控
                if (response.data.status === 'completed' || response.data.status === 'failed') {
                    stopProgressMonitoring();
                    resetStartButton();
                    
                    if (response.data.status === 'completed') {
                        showAlert('抓取完成！', 'success');
                    } else {
                        showAlert('抓取失败', 'danger');
                    }
                }
            }
        })
        .fail(function() {
            console.error('获取进度失败');
        });
}

/**
 * 更新进度显示
 */
function updateProgressDisplay(data) {
    var progress = data.progress || 0;
    var status = data.status || 'unknown';
    var message = data.message || '处理中...';
    
    // 更新进度条
    $('#progressBar').css('width', progress + '%');
    $('#progressBar').attr('aria-valuenow', progress);
    $('#progressText').text(Math.round(progress) + '%');
    
    // 更新状态
    $('#statusText').text(message);
    
    // 更新统计
    if (data.stats) {
        $('#totalTweets').text(data.stats.total || 0);
        $('#processedTweets').text(data.stats.processed || 0);
        $('#savedTweets').text(data.stats.saved || 0);
    }
}

/**
 * 更新数据预览
 */
function updateDataPreview(data) {
    if (!data.preview || data.preview.length === 0) {
        $('#dataPreview').html('<p class="text-muted">暂无预览数据</p>');
        return;
    }
    
    var html = '<h6>最新抓取的推文预览：</h6>';
    for (var i = 0; i < Math.min(data.preview.length, 3); i++) {
        var tweet = data.preview[i];
        html += createTweetPreview(tweet);
    }
    
    $('#dataPreview').html(html);
}

/**
 * 创建推文预览元素
 */
function createTweetPreview(tweet) {
    var mediaIcon = getMediaIcon(tweet.media_type);
    var createdAt = tweet.created_at ? new Date(tweet.created_at).toLocaleString() : '未知时间';
    
    return '<div class="card mb-2">' +
           '<div class="card-body p-3">' +
           '<div class="d-flex align-items-start">' +
           '<div class="me-3">' +
           '<img src="' + (tweet.user_avatar || '/static/default-avatar.png') + '" ' +
           'class="rounded-circle" width="40" height="40" alt="头像">' +
           '</div>' +
           '<div class="flex-grow-1">' +
           '<div class="d-flex justify-content-between align-items-start mb-2">' +
           '<div>' +
           '<strong>' + (tweet.user_name || '未知用户') + '</strong>' +
           '<span class="text-muted ms-2">@' + (tweet.username || 'unknown') + '</span>' +
           '</div>' +
           '<small class="text-muted">' + createdAt + '</small>' +
           '</div>' +
           '<p class="mb-2">' + (tweet.content || '无内容') + '</p>' +
           '<div class="d-flex justify-content-between text-muted small">' +
           '<span><i class="fas fa-heart"></i> ' + (tweet.likes_count || 0) + '</span>' +
           '<span><i class="fas fa-retweet"></i> ' + (tweet.retweets_count || 0) + '</span>' +
           '<span><i class="fas fa-comment"></i> ' + (tweet.comments_count || 0) + '</span>' +
           mediaIcon +
           '</div>' +
           '</div>' +
           '</div>' +
           '</div>' +
           '</div>';
}

/**
 * 获取媒体图标
 */
function getMediaIcon(mediaType) {
    if (!mediaType || mediaType === 'none') {
        return '';
    }
    
    var iconClass = '';
    switch (mediaType) {
        case 'photo':
            iconClass = 'fa-image';
            break;
        case 'video':
            iconClass = 'fa-video';
            break;
        case 'gif':
            iconClass = 'fa-file-image';
            break;
        default:
            iconClass = 'fa-paperclip';
    }
    
    return '<span><i class="fas ' + iconClass + '"></i></span>';
}

/**
 * 停止进度监控
 */
function stopProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    isProgressRunning = false;
}

/**
 * 重置开始按钮
 */
function resetStartButton() {
    var $startBtn = $('#startScrapeBtn');
    $startBtn.prop('disabled', false);
    $startBtn.html('<i class="fas fa-play"></i> 开始抓取');
}

/**
 * 加载统计数据
 */
function loadStats() {
    $.ajax({
        url: '/api/stats',
        method: 'GET',
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success) {
                $('#totalTweetsCount').text(response.data.total_tweets || 0);
                $('#todayTweetsCount').text(response.data.today_tweets || 0);
                $('#activeInfluencersCount').text(response.data.active_influencers || 0);
            }
        })
        .fail(function() {
            console.error('加载统计数据失败');
        });
}

/**
 * 显示警告框
 */
function showAlert(message, type) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                    '</div>';
    $('#alertContainer').html(alertHtml);
    
    // 5秒后自动隐藏
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
}