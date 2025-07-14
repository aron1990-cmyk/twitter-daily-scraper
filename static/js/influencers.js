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
    initializePage();
    bindEvents();
    loadInfluencers();
    loadCategories();
    loadStats();
});

/**
 * 初始化页面
 */
function initializePage() {
    console.log('博主管理页面初始化');
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 添加博主按钮
    $('#addInfluencerBtn').click(function() {
        showAddInfluencerModal();
    });
    
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
    $('#selectAllCheckbox').change(function() {
        const isChecked = $(this).is(':checked');
        $('.influencer-checkbox').prop('checked', isChecked);
        updateSelectedInfluencers();
    });
    
    // 批量操作按钮
    $('#batchScrapeBtn').click(batchScrapeInfluencers);
    $('#batchToggleStatusBtn').click(batchToggleStatus);
    $('#batchDeleteBtn').click(batchDeleteInfluencers);
    
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
    
    $.get('/api/influencers', params)
        .done(function(response) {
            if (response.success) {
                displayInfluencers(response.data.influencers);
                updatePagination(response.data);
            } else {
                showAlert('加载博主列表失败: ' + response.error, 'danger');
            }
        })
        .fail(function() {
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
    const container = $('#influencersContainer');
    
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
    
    let html = '';
    influencers.forEach(influencer => {
        const statusBadge = influencer.is_active ? 
            '<span class="badge badge-success">启用</span>' : 
            '<span class="badge badge-secondary">禁用</span>';
        
        const lastScraped = influencer.last_scraped ? 
            new Date(influencer.last_scraped).toLocaleString() : '从未抓取';
        
        html += `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="custom-control custom-checkbox">
                            <input type="checkbox" class="custom-control-input influencer-checkbox" 
                                   id="influencer_${influencer.id}" value="${influencer.id}">
                            <label class="custom-control-label" for="influencer_${influencer.id}"></label>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                    type="button" data-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-right">
                                <a class="dropdown-item" href="#" onclick="editInfluencer(${influencer.id})">
                                    <i class="fas fa-edit"></i> 编辑
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
                            <span class="badge badge-primary">${influencer.category}</span>
                            ${statusBadge}
                        </div>
                    </div>
                    <div class="card-footer small text-muted">
                        <div class="d-flex justify-content-between">
                            <span>粉丝: ${influencer.followers_count.toLocaleString()}</span>
                            <span>最后抓取: ${lastScraped}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.html(html);
    
    // 绑定复选框事件
    $('.influencer-checkbox').change(updateSelectedInfluencers);
}

/**
 * 更新分页
 */
function updatePagination(data) {
    totalPages = data.pages;
    currentPage = data.current_page;
    
    const pagination = $('#pagination');
    
    if (totalPages <= 1) {
        pagination.hide();
        return;
    }
    
    pagination.show();
    
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
    $('#addInfluencerModal').modal('show');
}

/**
 * 提交添加博主
 */
function submitAddInfluencer() {
    const formData = {
        name: $('#addName').val().trim(),
        profile_url: $('#addProfileUrl').val().trim(),
        description: $('#addDescription').val().trim(),
        category: $('#addCategory').val(),
        followers_count: parseInt($('#addFollowersCount').val()) || 0
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
            $('#addInfluencerModal').modal('hide');
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
                $('#editName').val(influencer.name);
                $('#editDescription').val(influencer.description);
                $('#editCategory').val(influencer.category);
                $('#editFollowersCount').val(influencer.followers_count);
                $('#editIsActive').prop('checked', influencer.is_active);
                
                $('#editInfluencerModal').modal('show');
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
        name: $('#editName').val().trim(),
        description: $('#editDescription').val().trim(),
        category: $('#editCategory').val(),
        followers_count: parseInt($('#editFollowersCount').val()) || 0,
        is_active: $('#editIsActive').is(':checked')
    };
    
    $.ajax({
        url: `/api/influencers/${id}`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(formData)
    })
    .done(function(response) {
        if (response.success) {
            $('#editInfluencerModal').modal('hide');
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
 * 批量抓取博主
 */
function batchScrapeInfluencers() {
    if (selectedInfluencers.size === 0) {
        showAlert('请先选择要抓取的博主', 'warning');
        return;
    }
    
    showAlert('批量抓取功能开发中...', 'info');
}

/**
 * 批量切换状态
 */
function batchToggleStatus() {
    if (selectedInfluencers.size === 0) {
        showAlert('请先选择要操作的博主', 'warning');
        return;
    }
    
    showAlert('批量状态切换功能开发中...', 'info');
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
    
    showAlert('批量删除功能开发中...', 'info');
}

/**
 * 显示加载状态
 */
function showLoading(show) {
    if (show) {
        $('#loadingSpinner').show();
        $('#influencersContainer').hide();
    } else {
        $('#loadingSpinner').hide();
        $('#influencersContainer').show();
    }
}

/**
 * 显示警告信息
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `;
    
    $('#alertContainer').html(alertHtml);
    
    // 自动隐藏
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
}