/**
 * 博主管理页面JavaScript
 * 实现博主的增删改查、搜索、筛选、分页等功能
 */

// 全局变量
let currentPage = 1;
let totalPages = 1;
let currentCategory = '';
let currentSearch = '';
let selectedInfluencers = new Set();

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
    const requiredElements = [
        '#influencerListContainer',
        '#alertContainer',
        '#searchInput',
        '#categoryFilter',
        '#selectAll'
    ];
    
    requiredElements.forEach(selector => {
        if ($(selector).length === 0) {
            console.error(`必要元素不存在: ${selector}`);
        }
    });
    
    // 设置初始状态
    $('#batchScrapeBtn, #batchToggleStatusBtn, #batchDeleteBtn').prop('disabled', true);
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 添加博主按钮 - 使用Bootstrap 5的data-bs-toggle自动处理
    // 不需要手动绑定点击事件
    
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
        const isChecked = $(this).is(':checked');
        $('.influencer-checkbox').prop('checked', isChecked);
        updateSelectedInfluencers();
    });
    
    // 批量操作按钮通过onclick属性处理
    
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
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
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
    
    const params = {
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
                const errorMsg = response && response.error ? response.error : '未知错误';
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
    const container = $('#influencerListContainer');
    
    if (influencers.length === 0) {
        container.html(`
            <div class="text-center py-5">
                <i class="fas fa-user-friends fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">暂无博主数据</h5>
                <p class="text-muted">点击上方"添加博主"按钮开始添加</p>
            </div>
        `);
        return;
    }
    
    let html = '<div class="row">';
    influencers.forEach(influencer => {
        const statusBadge = influencer.is_active ? 
            '<span class="badge bg-success">启用</span>' : 
            '<span class="badge bg-secondary">禁用</span>';
        
        const lastScraped = influencer.last_scraped ? 
            new Date(influencer.last_scraped).toLocaleString() : '从未抓取';
        
        html += `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input influencer-checkbox" 
                                   id="influencer_${influencer.id}" value="${influencer.id}">
                            <label class="form-check-label" for="influencer_${influencer.id}"></label>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                    type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-end">
                                <a class="dropdown-item" href="#" onclick="editInfluencer(${influencer.id})">
                                    <i class="fas fa-edit"></i> 编辑
                                </a>
                                <a class="dropdown-item" href="#" onclick="toggleInfluencerStatus(${influencer.id})">
                                    <i class="fas fa-toggle-${influencer.is_active ? 'off' : 'on'}"></i> ${influencer.is_active ? '禁用' : '启用'}
                                </a>
                                <a class="dropdown-item" href="#" onclick="scrapeInfluencer(${influencer.id})">
                                    <i class="fas fa-download"></i> 抓取
                                </a>
                                <a class="dropdown-item" href="${influencer.profile_url}" target="_blank">
                                    <i class="fas fa-external-link-alt"></i> 访问主页
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item text-danger" href="#" onclick="deleteInfluencer(${influencer.id})">
                                    <i class="fas fa-trash"></i> 删除
                                </a>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">${influencer.name}</h6>
                        <p class="card-text text-muted small">@${influencer.username}</p>
                        <p class="card-text">${influencer.description || '暂无描述'}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-primary">${influencer.category}</span>
                            ${statusBadge}
                        </div>
                    </div>
                    <div class="card-footer small text-muted">
                        <div class="d-flex justify-content-between">
                            <span>粉丝: ${(influencer.followers_count || 0).toLocaleString()}</span>
                            <span>最后抓取: ${lastScraped}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.html(html);
    
    // 绑定复选框事件
    $('.influencer-checkbox').change(updateSelectedInfluencers);
    
    // 初始化选中状态
    updateSelectedInfluencers();
}

/**
 * 更新分页
 */
function updatePagination(data) {
    totalPages = data.pages;
    currentPage = data.current_page;
    
    const pagination = $('#paginationList');
    const paginationContainer = $('#influencerPagination');
    
    if (totalPages <= 1) {
        paginationContainer.hide();
        return;
    }
    
    paginationContainer.show();
    
    let html = '';
    
    // 上一页
    if (currentPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage - 1})">上一页</a></li>`;
    }
    
    // 页码
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const active = i === currentPage ? 'active' : '';
        html += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="goToPage(${i})">${i}</a></li>`;
    }
    
    // 下一页
    if (currentPage < totalPages) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage + 1})">下一页</a></li>`;
    }
    
    pagination.html(html);
}

/**
 * 跳转到指定页面
 */
function goToPage(page) {
    currentPage = page;
    loadInfluencers();
}

/**
 * 加载分类列表
 */
function loadCategories() {
    $.get('/api/influencers/categories')
        .done(function(response) {
            if (response.success) {
                const select = $('#categoryFilter');
                select.empty().append('<option value="">全部分类</option>');
                
                response.data.forEach(category => {
                    select.append(`<option value="${category.name}">${category.name} (${category.count})</option>`);
                });
            }
        });
}

/**
 * 加载统计数据
 */
function loadStats() {
    $.get('/api/influencers')
        .done(function(response) {
            if (response.success) {
                const total = response.data.total;
                $('#totalInfluencers').text(total);
            }
        });
    
    // 加载其他统计数据
    $.get('/api/influencers?is_active=true')
        .done(function(response) {
            if (response.success) {
                $('#activeInfluencers').text(response.data.total);
            }
        });
}

/**
 * 更新选中的博主
 */
function updateSelectedInfluencers() {
    selectedInfluencers.clear();
    $('.influencer-checkbox:checked').each(function() {
        selectedInfluencers.add(parseInt($(this).val()));
    });
    
    // 更新批量操作按钮状态
    const hasSelected = selectedInfluencers.size > 0;
    $('#batchScrapeBtn, #batchToggleStatusBtn, #batchDeleteBtn').prop('disabled', !hasSelected);
    
    // 更新选中计数
    $('#selectedCount').text(selectedInfluencers.size);
}

/**
 * 显示添加博主模态框
 */
function showAddInfluencerModal() {
    $('#addInfluencerForm')[0].reset();
    // Bootstrap 5 模态框API
    const modal = new bootstrap.Modal(document.getElementById('addInfluencerModal'));
    modal.show();
}

/**
 * 提交添加博主
 */
function submitAddInfluencer() {
    const formData = {
        name: $('#addInfluencerName').val().trim(),
        profile_url: $('#addInfluencerUrl').val().trim(),
        description: $('#addInfluencerDescription').val().trim(),
        category: $('#addInfluencerCategory').val(),
        is_active: $('#addInfluencerActive').is(':checked')
    };
    
    if (!formData.name || !formData.profile_url) {
        showAlert('请填写博主名称和主页URL', 'warning');
        return;
    }
    
    $.ajax({
        url: '/api/influencers',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData)
    })
    .done(function(response) {
        if (response.success) {
            // Bootstrap 5 模态框API
            const modal = bootstrap.Modal.getInstance(document.getElementById('addInfluencerModal'));
            modal.hide();
            showAlert('博主添加成功', 'success');
            loadInfluencers();
            loadStats();
        } else {
            showAlert('添加失败: ' + response.error, 'danger');
        }
    })
    .fail(function() {
        showAlert('网络错误，请稍后重试', 'danger');
    });
}

/**
 * 编辑博主
 */
function editInfluencer(id) {
    // 获取博主信息
    $.get(`/api/influencers/${id}`)
        .done(function(response) {
            if (response.success) {
                const influencer = response.data;
                
                // 填充编辑表单
                $('#editInfluencerId').val(influencer.id);
                $('#editInfluencerName').val(influencer.name);
                $('#editInfluencerDescription').val(influencer.description);
                $('#editInfluencerCategory').val(influencer.category);
                $('#editInfluencerActive').prop('checked', influencer.is_active);
                
                // Bootstrap 5 模态框API
                const modal = new bootstrap.Modal(document.getElementById('editInfluencerModal'));
                modal.show();
            } else {
                showAlert('获取博主信息失败: ' + response.error, 'danger');
            }
        })
        .fail(function() {
            showAlert('网络错误，请稍后重试', 'danger');
        });
}

/**
 * 提交编辑博主
 */
function submitEditInfluencer() {
    const id = $('#editInfluencerId').val();
    const formData = {
        name: $('#editInfluencerName').val().trim(),
        description: $('#editInfluencerDescription').val().trim(),
        category: $('#editInfluencerCategory').val(),
        is_active: $('#editInfluencerActive').is(':checked')
    };
    
    $.ajax({
        url: `/api/influencers/${id}`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(formData)
    })
    .done(function(response) {
        if (response.success) {
            // Bootstrap 5 模态框API
            const modal = bootstrap.Modal.getInstance(document.getElementById('editInfluencerModal'));
            modal.hide();
            showAlert('博主信息更新成功', 'success');
            loadInfluencers();
        } else {
            showAlert('更新失败: ' + response.error, 'danger');
        }
    })
    .fail(function() {
        showAlert('网络错误，请稍后重试', 'danger');
    });
}

/**
 * 删除博主
 */
function deleteInfluencer(id) {
    if (!confirm('确定要删除这个博主吗？此操作不可恢复。')) {
        return;
    }
    
    $.ajax({
        url: `/api/influencers/${id}`,
        method: 'DELETE'
    })
    .done(function(response) {
        if (response.success) {
            showAlert('博主删除成功', 'success');
            loadInfluencers();
            loadStats();
        } else {
            showAlert('删除失败: ' + response.error, 'danger');
        }
    })
    .fail(function() {
        showAlert('网络错误，请稍后重试', 'danger');
    });
}

/**
 * 抓取单个博主
 */
function scrapeInfluencer(id) {
    showAlert('抓取功能开发中...', 'info');
}

/**
 * 切换博主状态
 */
function toggleInfluencerStatus(id) {
    $.ajax({
        url: `/api/influencers/${id}/toggle-status`,
        method: 'PATCH'
    })
    .done(function(response) {
        if (response.success) {
            showAlert(response.message, 'success');
            loadInfluencers(); // 重新加载列表以更新状态显示
            loadStats(); // 更新统计数据
        } else {
            showAlert('状态切换失败: ' + response.error, 'danger');
        }
    })
    .fail(function() {
        showAlert('网络错误，请稍后重试', 'danger');
    });
}

/**
 * 批量抓取博主
 */
function batchScrapeInfluencers() {
    console.log('batchScrapeInfluencers 函数被调用');
    
    const $selectedCheckboxes = $('.influencer-checkbox:checked');
    console.log('选中的复选框数量:', $selectedCheckboxes.length);
    
    if ($selectedCheckboxes.length === 0) {
        showAlert('请先选择要抓取的博主', 'warning');
        return;
    }
    
    const influencerIds = $selectedCheckboxes.map(function() {
        return parseInt($(this).val());
    }).get();
    console.log('博主IDs:', influencerIds);
    
    // 显示确认对话框
    if (!confirm(`确定要批量抓取选中的 ${influencerIds.length} 个博主的推文吗？`)) {
        return;
    }
    
    // 显示加载状态
    const $batchScrapeBtn = $('#batchScrapeBtn');
    if ($batchScrapeBtn.length === 0) {
        showAlert('找不到批量抓取按钮', 'danger');
        console.error('批量抓取按钮元素未找到');
        return;
    }
    const originalText = $batchScrapeBtn.html();
    $batchScrapeBtn.html('<i class="fas fa-spinner fa-spin"></i> 启动中...');
    $batchScrapeBtn.prop('disabled', true);
    
    // 发送批量抓取请求
    $.ajax({
        url: '/api/influencers/batch-scrape',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            influencer_ids: influencerIds,
            max_tweets: 50,
            min_likes: 0,
            min_retweets: 0,
            min_comments: 0
        })
    })
    .done(function(response) {
        if (response.success) {
            showAlert(response.message, 'success');
            // 清除选择
            $('#selectAll').prop('checked', false);
            $('.influencer-checkbox').prop('checked', false);
            updateSelectedInfluencers();
        } else {
            showAlert(response.error || '批量抓取启动失败', 'danger');
        }
    })
    .fail(function() {
        showAlert('批量抓取启动失败，请重试', 'danger');
    })
    .always(function() {
        // 恢复按钮状态
        $batchScrapeBtn.html(originalText);
        $batchScrapeBtn.prop('disabled', false);
    });
}

/**
 * 批量切换状态
 */
function batchToggleStatus() {
    if (selectedInfluencers.size === 0) {
        showAlert('请先选择要操作的博主', 'warning');
        return;
    }
    
    if (!confirm(`确定要切换选中的 ${selectedInfluencers.size} 个博主的状态吗？`)) {
        return;
    }
    
    const $batchToggleBtn = $('#batchToggleStatusBtn');
    const originalText = $batchToggleBtn.html();
    $batchToggleBtn.html('<i class="fas fa-spinner fa-spin"></i> 处理中...');
    $batchToggleBtn.prop('disabled', true);
    
    let completed = 0;
    let errors = 0;
    const total = selectedInfluencers.size;
    
    // 逐个切换状态
    selectedInfluencers.forEach(id => {
        $.ajax({
            url: `/api/influencers/${id}/toggle-status`,
            method: 'PATCH'
        })
        .done(function(response) {
            completed++;
            if (!response.success) {
                errors++;
            }
        })
        .fail(function() {
            completed++;
            errors++;
        })
        .always(function() {
            // 检查是否全部完成
            if (completed === total) {
                // 恢复按钮状态
                $batchToggleBtn.html(originalText);
                $batchToggleBtn.prop('disabled', false);
                
                // 显示结果
                if (errors === 0) {
                    showAlert(`成功切换了 ${total} 个博主的状态`, 'success');
                } else {
                    showAlert(`完成批量切换，成功 ${total - errors} 个，失败 ${errors} 个`, 'warning');
                }
                
                // 清除选择并重新加载
                $('#selectAll').prop('checked', false);
                $('.influencer-checkbox').prop('checked', false);
                updateSelectedInfluencers();
                loadInfluencers();
                loadStats();
            }
        });
    });
}

/**
 * 批量删除博主
 */
function batchDeleteInfluencers() {
    if (selectedInfluencers.size === 0) {
        showAlert('请先选择要删除的博主', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${selectedInfluencers.size} 个博主吗？此操作不可恢复。`)) {
        return;
    }
    
    const $batchDeleteBtn = $('#batchDeleteBtn');
    const originalText = $batchDeleteBtn.html();
    $batchDeleteBtn.html('<i class="fas fa-spinner fa-spin"></i> 删除中...');
    $batchDeleteBtn.prop('disabled', true);
    
    let completed = 0;
    let errors = 0;
    const total = selectedInfluencers.size;
    
    // 逐个删除博主
    selectedInfluencers.forEach(id => {
        $.ajax({
            url: `/api/influencers/${id}`,
            method: 'DELETE'
        })
        .done(function(response) {
            completed++;
            if (!response.success) {
                errors++;
            }
        })
        .fail(function() {
            completed++;
            errors++;
        })
        .always(function() {
            // 检查是否全部完成
            if (completed === total) {
                // 恢复按钮状态
                $batchDeleteBtn.html(originalText);
                $batchDeleteBtn.prop('disabled', false);
                
                // 显示结果
                if (errors === 0) {
                    showAlert(`成功删除了 ${total} 个博主`, 'success');
                } else {
                    showAlert(`完成批量删除，成功 ${total - errors} 个，失败 ${errors} 个`, 'warning');
                }
                
                // 清除选择并重新加载
                $('#selectAll').prop('checked', false);
                $('.influencer-checkbox').prop('checked', false);
                updateSelectedInfluencers();
                loadInfluencers();
                loadStats();
            }
        });
    });
}

/**
 * HTML模板中调用的函数
 */
function addInfluencer() {
    submitAddInfluencer();
}

function updateInfluencer() {
    submitEditInfluencer();
}

function searchInfluencers() {
    currentSearch = $('#searchInput').val().trim();
    currentPage = 1;
    loadInfluencers();
}

function batchScrape() {
    console.log('batchScrape 函数被调用');
    batchScrapeInfluencers();
}

function batchDelete() {
    batchDeleteInfluencers();
}

/**
 * 显示加载状态
 */
function showLoading(show) {
    const container = $('#influencerListContainer');
    if (show) {
        container.html(`
            <div class="text-center py-4">
                <div class="loading"></div>
                <p class="mt-2 text-muted">加载中...</p>
            </div>
        `);
    }
    // 加载完成后会调用displayInfluencers来替换内容
}

/**
 * 显示警告信息
 */
function showAlert(message, type = 'info') {
    // 确保alertContainer存在
    const alertContainer = $('#alertContainer');
    if (alertContainer.length === 0) {
        console.error('alertContainer not found');
        return;
    }
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.html(alertHtml);
    
    // 自动隐藏
    setTimeout(() => {
        const alertElement = alertContainer.find('.alert')[0];
        if (alertElement) {
            const alert = new bootstrap.Alert(alertElement);
            alert.close();
        }
    }, 5000);
}