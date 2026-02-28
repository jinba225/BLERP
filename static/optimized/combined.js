/* 优化后的JavaScript文件 - 合并并压缩所有JS资源 */

// 全局命名空间
const ERP = ERP || {};

// 资源懒加载功能
ERP.LazyLoad = {
    // 图片懒加载
    initImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        } else {
            // 降级方案
            images.forEach(img => {
                img.src = img.dataset.src;
                img.classList.remove('lazy');
            });
        }
    },
    
    // 脚本懒加载
    loadScript(src, callback) {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        
        if (callback) {
            script.onload = callback;
        }
        
        document.head.appendChild(script);
    },
    
    // 样式懒加载
    loadStyle(href, callback) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        
        if (callback) {
            link.onload = callback;
        }
        
        document.head.appendChild(link);
    }
};

// 前端缓存策略
ERP.Cache = {
    // 本地存储缓存
    set(key, value, expiration = 86400) {
        const item = {
            value: value,
            expiry: Date.now() + (expiration * 1000)
        };
        localStorage.setItem(key, JSON.stringify(item));
    },
    
    get(key) {
        const itemStr = localStorage.getItem(key);
        if (!itemStr) return null;
        
        const item = JSON.parse(itemStr);
        if (Date.now() > item.expiry) {
            localStorage.removeItem(key);
            return null;
        }
        
        return item.value;
    },
    
    remove(key) {
        localStorage.removeItem(key);
    },
    
    clear() {
        localStorage.clear();
    }
};

// 工具函数
ERP.Utils = {
    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 深拷贝
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    // 格式化日期
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },
    
    // 格式化数字
    formatNumber(num, decimals = 2) {
        return parseFloat(num).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    // 生成唯一ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// API请求封装
ERP.Api = {
    // 基础请求方法
    async request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // GET请求
    get(url, params = {}) {
        const queryString = Object.entries(params)
            .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
            .join('&');
        
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl);
    },
    
    // POST请求
    post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT请求
    put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE请求
    delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};

// 表单处理
ERP.Form = {
    // 表单验证
    validate(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('border-red-500');
                isValid = false;
            } else {
                input.classList.remove('border-red-500');
            }
        });
        
        return isValid;
    },
    
    // 获取表单数据
    getData(form) {
        const formData = new FormData(form);
        const data = {};
        
        formData.forEach((value, key) => {
            data[key] = value;
        });
        
        return data;
    },
    
    // 重置表单
    reset(form) {
        form.reset();
        form.querySelectorAll('input, select, textarea').forEach(input => {
            input.classList.remove('border-red-500');
        });
    }
};

// 模态框
ERP.Modal = {
    open(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    },
    
    close(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }
};

// 通知系统
ERP.Notification = {
    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-0 opacity-100`;
        
        switch (type) {
            case 'success':
                notification.classList.add('bg-green-500', 'text-white');
                break;
            case 'error':
                notification.classList.add('bg-red-500', 'text-white');
                break;
            case 'warning':
                notification.classList.add('bg-yellow-500', 'text-white');
                break;
            default:
                notification.classList.add('bg-blue-500', 'text-white');
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, duration);
    }
};

// 表格处理
ERP.Table = {
    // 排序
    sort(table, columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // 切换排序方向
        const currentSort = table.dataset.sort || 'asc';
        const newSort = currentSort === 'asc' ? 'desc' : 'asc';
        table.dataset.sort = newSort;
        
        // 排序行
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            if (!isNaN(aValue) && !isNaN(bValue)) {
                return newSort === 'asc' ? parseFloat(aValue) - parseFloat(bValue) : parseFloat(bValue) - parseFloat(aValue);
            }
            
            return newSort === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
        });
        
        // 重新插入行
        rows.forEach(row => tbody.appendChild(row));
    },
    
    // 搜索
    search(table, searchTerm) {
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
};

// 初始化函数
ERP.init = function() {
    // 初始化图片懒加载
    ERP.LazyLoad.initImages();
    
    // 初始化事件监听器
    this.initEventListeners();
    
    // 初始化表单验证
    this.initFormValidation();
    
    console.log('ERP system initialized');
};

// 初始化事件监听器
ERP.initEventListeners = function() {
    // 模态框关闭按钮
    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-close');
            ERP.Modal.close(modalId);
        });
    });
    
    // 模态框打开按钮
    document.querySelectorAll('[data-modal-open]').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-open');
            ERP.Modal.open(modalId);
        });
    });
    
    // 表格排序
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = Array.from(this.parentElement.children).indexOf(this);
            ERP.Table.sort(table, columnIndex);
        });
    });
    
    // 表格搜索
    document.querySelectorAll('[data-table-search]').forEach(input => {
        input.addEventListener('input', ERP.Utils.debounce(function() {
            const tableId = this.getAttribute('data-table-search');
            const table = document.getElementById(tableId);
            ERP.Table.search(table, this.value);
        }, 300));
    });
    
    // 表单提交
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!ERP.Form.validate(this)) {
                e.preventDefault();
                ERP.Notification.show('请填写所有必填字段', 'error');
            }
        });
    });
};

// 初始化表单验证
ERP.initFormValidation = function() {
    document.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
        input.addEventListener('blur', function() {
            if (!this.value.trim()) {
                this.classList.add('border-red-500');
            } else {
                this.classList.remove('border-red-500');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('border-red-500');
            }
        });
    });
};

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ERP.init.bind(ERP));
} else {
    ERP.init();
}

// 导出全局变量
if (typeof window !== 'undefined') {
    window.ERP = ERP;
}

// 性能监控
if ('performance' in window) {
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`页面加载时间: ${loadTime.toFixed(2)}ms`);
        
        // 发送性能数据到服务器
        if (navigator.sendBeacon) {
            const performanceData = {
                loadTime: loadTime,
                navigationType: performance.navigation.type,
                timestamp: new Date().toISOString()
            };
            
            navigator.sendBeacon('/api/performance', JSON.stringify(performanceData));
        }
    });
}

// 错误监控
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    
    // 发送错误数据到服务器
    if (navigator.sendBeacon) {
        const errorData = {
            message: e.error.message,
            stack: e.error.stack,
            filename: e.filename,
            lineno: e.lineno,
            colno: e.colno,
            timestamp: new Date().toISOString()
        };
        
        navigator.sendBeacon('/api/error', JSON.stringify(errorData));
    }
});

// 未捕获的Promise错误
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled Promise rejection:', e.reason);
    
    // 发送错误数据到服务器
    if (navigator.sendBeacon) {
        const errorData = {
            message: e.reason.message || String(e.reason),
            stack: e.reason.stack,
            timestamp: new Date().toISOString()
        };
        
        navigator.sendBeacon('/api/error', JSON.stringify(errorData));
    }
});

// 滚动优化
window.addEventListener('scroll', ERP.Utils.throttle(function() {
    // 滚动相关的逻辑
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // 处理导航栏样式变化
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (scrollTop > 100) {
            navbar.classList.add('bg-white', 'shadow-md');
        } else {
            navbar.classList.remove('bg-white', 'shadow-md');
        }
    }
}, 16));

// 响应式处理
window.addEventListener('resize', ERP.Utils.debounce(function() {
    // 响应式相关的逻辑
    const windowWidth = window.innerWidth;
    
    // 处理侧边栏
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        if (windowWidth < 768) {
            sidebar.classList.add('hidden');
        } else {
            sidebar.classList.remove('hidden');
        }
    }
}, 250));

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // ESC键关闭模态框
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal:not(.hidden)').forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.classList.remove('overflow-hidden');
    }
    
    // Ctrl/Cmd + K 打开搜索
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('[data-table-search]');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// 复制到剪贴板功能
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                ERP.Notification.show('已复制到剪贴板', 'success');
            })
            .catch(err => {
                console.error('复制失败:', err);
                ERP.Notification.show('复制失败', 'error');
            });
    } else {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        ERP.Notification.show('已复制到剪贴板', 'success');
    }
}

// 导出复制函数
if (typeof window !== 'undefined') {
    window.copyToClipboard = copyToClipboard;
}

// 加载Alpine.js
if (typeof Alpine === 'undefined') {
    console.error('Alpine.js not loaded');
} else {
    console.log('Alpine.js loaded successfully');
}
