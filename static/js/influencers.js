/**
 * 博主管理页面JavaScript
 * 实现博主的增删改查、搜索、筛选、分页等功能
 * 兼容ES5语法
 */

// 全局变量
var currentPage = 1;
var totalPages = 1;
var currentCategory = '';
var currentSearch = '';
var selectedInfluencers = new Set();

// 页面加载完成后初始化
$(document).ready(function() {
    try {
        initializePage();
        bindEvents();
        loadInfluencers();
        loadCategories();
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
    console.log('博主管理页面初始化');
    
    // 检查必要的元素是否存在
    var requiredElements = [
        '#influencerListContainer',
        '#alertContainer',
        '#searchInput',
        '#categoryFilter',
        '#selectAll'
    ];
    
    for (var i = 0; i < requiredElements.length; i++) {
        var selector = requiredElements[i];
        if ($(selector).length === 0) {
            console.error('必要元素不存在: ' + selector);
        }
    }
    
    // 设置初始状态
    $('#batchScrapeBtn, #batchToggleStatusBtn, #batchDeleteBtn').prop('disabled', true);
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 搜索框
    $('#searchInput').on('input', debounce(function() {
        currentSearch = $(this).val().trim();
        currentPage = 1;
        loadInfluencers();
    }, 500));
    
    // 分类筛选
    $('#categoryFilter').change(function() {
        currentCategory = $(this).val();
        currentPage = 1;
        loadInfluencers();
    });
    
    // 全选/取消全选
    $('#selectAll').change(function() {
        var isChecked = $(this).is(':checked');
        $('.influencer-checkbox').prop('checked', isChecked);
        updateSelectedInfluencers();
    });
    
    // 添加博主表单提交
    $('#addInfluencerForm').submit(function(e) {
        e.preventDefault();
        submitAddInfluencer();
    });
    
    // 编辑博主表单提交
    $('#editInfluencerForm').submit(function(e) {
        e.preventDefault();
        submitEditInfluencer();
    });
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    var timeout;
    return function executedFunction() {
        var args = Array.prototype.slice.call(arguments);
        var later = function() {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 加载博主列表
 */
function loadInfluencers() {
    console.log('开始加载博主列表...');
    showLoading(true);
    
    var params = {
        page: currentPage,
        per_page: 20
    };
    
    if (currentCategory) {
        params.category = currentCategory;
    }
    
    if (currentSearch) {
        params.search = currentSearch;
    }
    
    console.log('请求参数:', params);
    
    $.ajax({
        url: '/api/influencers',
        method: 'GET',
        data: params,
        dataType: 'json'
    })
        .done(function(response) {
            console.log('API响应:', response);
            console.log('response.success的值:', response.success, '类型:', typeof response.success);
            if (response && response.success === true) {
                displayInfluencers(response.data.influencers);
                updatePagination(response.data);
                console.log('博主列表加载成功，共', response.data.influencers.length, '条记录');
            } else {
                console.error('API返回错误:', response);
                var errorMsg = response && response.error ? response.error : '未知错误';
                showAlert('加载博主列表失败: ' + errorMsg, 'danger');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('请求失败:', status, error, xhr.responseText);
            showAlert('网络错误，请稍后重试', 'danger');
        })
        .always(function() {
            showLoading(false);
        });
}

/**
 * 显示博主列表
 */
function displayInfluencers(influencers) {
    var container = $('#influencerListContainer');
    
    if (influencers.length === 0) {
        container.html(
            '<div class="text-center py-5">' +
                '<i class="fas fa-user-friends fa-3x text-muted mb-3"></i>' +
                '<h5 class="text-muted">暂无博主数据</h5>' +
                '<p class="text-muted">点击上方"添加博主"按钮开始添加</p>' +
            '</div>'
        );
        return;
    }
    
    var html = '<div class="row">';
    for (var i = 0; i < influencers.length; i++) {
        var influencer = influencers[i];
        var statusBadge = influencer.is_active ? 
            '<span class="badge bg-success">启用</span>' : 
            '<span class="badge bg-secondary">禁用</span>';
        
        var lastScraped = influencer.last_scraped ? 
            new Date(influencer.last_scraped).toLocaleString() : '从未抓取';
        
        html += '<div class="col-md-6 col-lg-4 mb-4">' +
                '<div class="card h-100">' +
                '<div class="card-header d-flex justify-content-between align-items-center">' +
                '<div class="form-check">' +
                '<input type="checkbox" class="form-check-input influencer-checkbox" ' +
                'id="influencer_' + influencer.id + '" value="' + influencer.id + '">' +
                '<label class="form-check-label" for="influencer_' + influencer.id + '"></label>' +
                '</div>' +
                '<div class="dropdown">' +
                '<button class="btn btn-sm btn-outline-secondary dropdown-toggle" ' +
                'type="button" data-bs-toggle="dropdown">' +
                '<i class="fas fa-ellipsis-v"></i>' +
                '</button>' +
                '<div class="dropdown-menu dropdown-menu-end">' +
                '<a class="dropdown-item" href="#" onclick="editInfluencer(' + influencer.id + ')">' +
                '<i class="fas fa-edit me-2"></i>编辑' +
                '</a>' +
                '<a class="dropdown-item" href="#" onclick="toggleInfluencerStatus(' + influencer.id + ')">' +
                '<i class="fas fa-toggle-on me-2"></i>切换状态' +
                '</a>' +
                '<div class="dropdown-divider"></div>' +
                '<a class="dropdown-item text-danger" href="#" onclick="deleteInfluencer(' + influencer.id + ')">' +
                '<i class="fas fa-trash me-2"></i>删除' +
                '</a>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '<div class="card-body">' +
                '<div class="d-flex align-items-center mb-3">' +
                '<div class="me-3">' +
                '<img src="' + (influencer.avatar_url || '/static/default-avatar.png') + '" ' +
                'class="rounded-circle" width="50" height="50" alt="头像">' +
                '</div>' +
                '<div class="flex-grow-1">' +
                '<h6 class="mb-1">' + (influencer.display_name || influencer.username || '未知') + '</h6>' +
                '<p class="text-muted mb-1">@' + (influencer.username || '未知') + '</p>' +
                statusBadge +
                '</div>' +
                '</div>' +
                '<div class="mb-2">' +
                '<small class="text-muted">分类：</small>' +
                '<span class="badge bg-primary">' + (influencer.category || '未分类') + '</span>' +
                '</div>' +
                '<div class="mb-2">' +
                '<small class="text-muted">粉丝数：</small>' +
                '<span>' + (influencer.followers_count || 0) + '</span>' +
                '</div>' +
                '<div class="mb-2">' +
                '<small class="text-muted">最后抓取：</small>' +
                '<span>' + lastScraped + '</span>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '</div>';
    }
    html += '</div>';
    
    container.html(html);
    
    // 重新绑定复选框事件
    $('.influencer-checkbox').change(function() {
        updateSelectedInfluencers();
    });
}

// 其他函数保持简化版本
function updateSelectedInfluencers() {
    selectedInfluencers.clear();
    $('.influencer-checkbox:checked').each(function() {
        selectedInfluencers.add(parseInt($(this).val()));
    });
    
    var hasSelected = selectedInfluencers.size > 0;
    $('#batchScrapeBtn, #batchToggleStatusBtn, #batchDeleteBtn').prop('disabled', !hasSelected);
    
    $('#selectAll').prop('checked', $('.influencer-checkbox').length > 0 && 
                                   $('.influencer-checkbox:checked').length === $('.influencer-checkbox').length);
}

function showLoading(show) {
    if (show) {
        $('#influencerListContainer').html('<div class="text-center py-5"><div class="spinner-border"></div><p class="mt-2 text-muted">加载中...</p></div>');
    }
}

function showAlert(message, type) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                    '</div>';
    $('#alertContainer').html(alertHtml);
}

// 简化的其他函数
function loadCategories() {
    console.log('开始加载分类数据...');
    
    $.ajax({
        url: '/api/influencers/categories',
        method: 'GET',
        dataType: 'json'
    })
        .done(function(response) {
            console.log('分类数据响应:', response);
            if (response && response.success === true) {
                // 可以在这里处理分类数据，比如更新筛选下拉框
                console.log('分类数据加载成功');
            } else {
                console.error('分类数据API返回错误:', response);
            }
        })
        .fail(function(xhr, status, error) {
            console.error('分类数据请求失败:', status, error);
        });
}

function loadStats() {
    console.log('开始加载统计数据...');
    
    $.ajax({
        url: '/api/influencers/stats',
        method: 'GET',
        dataType: 'json'
    })
        .done(function(response) {
            console.log('统计数据响应:', response);
            if (response && response.success === true) {
                var data = response.data;
                // 任务中使用的博主数量
                $('#totalInfluencers').text(data.total_influencers || 0);
                // 管理表中的博主数量
                $('#managedInfluencers').text(data.managed_influencers || 0);
                // 管理表中启用的博主数量
                $('#activeInfluencers').text(data.active_influencers || 0);
                // 分类数量
                $('#totalCategories').text(data.total_categories || 0);
                // 今日任务涉及的博主数量
                $('#scrapedToday').text(data.scraped_today || 0);
                console.log('统计数据更新成功');
                console.log('- 任务博主数:', data.total_influencers);
                console.log('- 管理博主数:', data.managed_influencers);
                console.log('- 启用博主数:', data.active_influencers);
                console.log('- 今日任务博主数:', data.scraped_today);
            } else {
                console.error('统计数据API返回错误:', response);
                showAlert('加载统计数据失败', 'warning');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('统计数据请求失败:', status, error);
            showAlert('网络错误，统计数据加载失败', 'warning');
        });
}

function updatePagination(data) {
    var pagination = data.pagination;
    if (!pagination) {
        $('#influencerPagination').hide();
        return;
    }
    
    totalPages = pagination.pages;
    currentPage = pagination.page;
    
    if (totalPages <= 1) {
        $('#influencerPagination').hide();
        return;
    }
    
    var paginationHtml = '';
    
    // 上一页
    if (currentPage > 1) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="#" onclick="loadPage(' + (currentPage - 1) + ')">上一页</a></li>';
    } else {
        paginationHtml += '<li class="page-item disabled"><span class="page-link">上一页</span></li>';
    }
    
    // 页码
    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, currentPage + 2);
    
    for (var i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHtml += '<li class="page-item active"><span class="page-link">' + i + '</span></li>';
        } else {
            paginationHtml += '<li class="page-item"><a class="page-link" href="#" onclick="loadPage(' + i + ')">' + i + '</a></li>';
        }
    }
    
    // 下一页
    if (currentPage < totalPages) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="#" onclick="loadPage(' + (currentPage + 1) + ')">下一页</a></li>';
    } else {
        paginationHtml += '<li class="page-item disabled"><span class="page-link">下一页</span></li>';
    }
    
    $('#paginationList').html(paginationHtml);
    $('#influencerPagination').show();
}

function loadPage(page) {
    currentPage = page;
    loadInfluencers();
}

function submitAddInfluencer() {
    var url = $('#addInfluencerUrl').val().trim();
    var name = $('#addInfluencerName').val().trim();
    var category = $('#addInfluencerCategory').val();
    var description = $('#addInfluencerDescription').val().trim();
    var isActive = $('#addInfluencerActive').is(':checked');
    
    if (!url || !name) {
        showAlert('请填写博主URL和名称', 'danger');
        return;
    }
    
    var data = {
        profile_url: url,
        name: name,
        category: category,
        description: description,
        is_active: isActive
    };
    
    $.ajax({
        url: '/api/influencers',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success === true) {
                showAlert('博主添加成功！', 'success');
                $('#addInfluencerModal').modal('hide');
                $('#addInfluencerForm')[0].reset();
                loadInfluencers();
                loadStats();
            } else {
                var errorMsg = response && response.error ? response.error : '添加失败';
                showAlert('添加博主失败: ' + errorMsg, 'danger');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('添加博主请求失败:', status, error);
            showAlert('网络错误，请稍后重试', 'danger');
        });
}

function addInfluencer() {
    submitAddInfluencer();
}

function editInfluencer(id) {
    console.log('编辑博主:', id);
    
    $.ajax({
        url: '/api/influencers/' + id,
        method: 'GET',
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success === true) {
                var influencer = response.data;
                $('#editInfluencerId').val(influencer.id);
                $('#editInfluencerUrl').val(influencer.profile_url);
                $('#editInfluencerName').val(influencer.name);
                $('#editInfluencerCategory').val(influencer.category);
                $('#editInfluencerDescription').val(influencer.description || '');
                $('#editInfluencerActive').prop('checked', influencer.is_active);
                $('#editInfluencerModal').modal('show');
            } else {
                showAlert('获取博主信息失败', 'danger');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('获取博主信息失败:', status, error);
            showAlert('网络错误，请稍后重试', 'danger');
        });
}

function submitEditInfluencer() {
    var id = $('#editInfluencerId').val();
    var url = $('#editInfluencerUrl').val().trim();
    var name = $('#editInfluencerName').val().trim();
    var category = $('#editInfluencerCategory').val();
    var description = $('#editInfluencerDescription').val().trim();
    var isActive = $('#editInfluencerActive').is(':checked');
    
    if (!url || !name) {
        showAlert('请填写博主URL和名称', 'danger');
        return;
    }
    
    var data = {
        profile_url: url,
        name: name,
        category: category,
        description: description,
        is_active: isActive
    };
    
    $.ajax({
        url: '/api/influencers/' + id,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(data),
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success === true) {
                showAlert('博主更新成功！', 'success');
                $('#editInfluencerModal').modal('hide');
                loadInfluencers();
                loadStats();
            } else {
                var errorMsg = response && response.error ? response.error : '更新失败';
                showAlert('更新博主失败: ' + errorMsg, 'danger');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('更新博主请求失败:', status, error);
            showAlert('网络错误，请稍后重试', 'danger');
        });
}

function deleteInfluencer(id) {
    if (!confirm('确定要删除这个博主吗？此操作不可撤销。')) {
        return;
    }
    
    console.log('删除博主:', id);
    
    $.ajax({
        url: '/api/influencers/' + id,
        method: 'DELETE',
        dataType: 'json'
    })
        .done(function(response) {
            if (response && response.success === true) {
                showAlert('博主删除成功！', 'success');
                loadInfluencers();
                loadStats();
            } else {
                var errorMsg = response && response.error ? response.error : '删除失败';
                showAlert('删除博主失败: ' + errorMsg, 'danger');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('删除博主请求失败:', status, error);
            showAlert('网络错误，请稍后重试', 'danger');
        });
}

function toggleInfluencerStatus(id) {
    // 简化实现
}

function batchScrapeInfluencers() {
    showAlert('批量抓取功能开发中...', 'info');
}

function batchToggleStatus() {
    showAlert('批量状态切换功能开发中...', 'info');
}

function batchDeleteInfluencers() {
    showAlert('批量删除功能开发中...', 'info');
}

function batchOperation(action) {
    var selectedIds = [];
    $('.influencer-checkbox:checked').each(function() {
        selectedIds.push($(this).val());
    });
    
    if (selectedIds.length === 0) {
        showAlert('请选择要操作的博主', 'warning');
        return;
    }
    
    var actionText = '';
    var confirmText = '';
    
    switch(action) {
        case 'enable':
            actionText = '启用';
            confirmText = '确定要启用选中的 ' + selectedIds.length + ' 个博主吗？';
            break;
        case 'disable':
            actionText = '禁用';
            confirmText = '确定要禁用选中的 ' + selectedIds.length + ' 个博主吗？';
            break;
        case 'delete':
            actionText = '删除';
            confirmText = '确定要删除选中的 ' + selectedIds.length + ' 个博主吗？此操作不可撤销。';
            break;
        default:
            showAlert('未知操作', 'danger');
            return;
    }
    
    if (!confirm(confirmText)) {
        return;
    }
    
    var requests = [];
    
    selectedIds.forEach(function(id) {
        var request;
        if (action === 'delete') {
            request = $.ajax({
                url: '/api/influencers/' + id,
                method: 'DELETE',
                dataType: 'json'
            });
        } else {
            var isActive = action === 'enable';
            request = $.ajax({
                url: '/api/influencers/' + id,
                method: 'PUT',
                contentType: 'application/json',
                data: JSON.stringify({ is_active: isActive }),
                dataType: 'json'
            });
        }
        requests.push(request);
    });
    
    Promise.all(requests)
        .then(function(responses) {
            var successCount = 0;
            responses.forEach(function(response) {
                if (response && response.success === true) {
                    successCount++;
                }
            });
            
            if (successCount === selectedIds.length) {
                showAlert('批量' + actionText + '成功！', 'success');
            } else {
                showAlert('批量' + actionText + '部分成功，成功: ' + successCount + '/' + selectedIds.length, 'warning');
            }
            
            loadInfluencers();
            loadStats();
            $('#selectAll').prop('checked', false);
        })
        .catch(function(error) {
            console.error('批量操作失败:', error);
            showAlert('批量' + actionText + '失败，请稍后重试', 'danger');
        });
}