/**
 * 页面自动刷新模块
 *
 * 功能：
 * - 自动定时刷新
 * - 手动刷新按钮
 * - 页面可见性检测
 * - 用户活动检测
 * - 状态保持（滚动位置、URL参数）
 * - Toast通知系统
 */

// ============================================================================
// 刷新管理器类
// ============================================================================
class PageRefreshManager {
    constructor(config = {}) {
        this.config = {
            enabled: config.enabled ?? true,
            interval: (config.interval ?? 30) * 1000,  // 转换为毫秒
            mode: config.mode ?? 'auto',
            preserveState: config.preserveState ?? true,
            showNotifications: config.showNotifications ?? false,
            smartFeatures: config.smartFeatures ?? {},
        };

        this.state = {
            isRefreshing: false,
            lastRefreshTime: null,
            refreshCount: 0,
            isVisible: true,
            isUserActive: true,
            timerId: null,
        };

        this.init();
    }

    // 初始化
    init() {
        if (!this.config.enabled) {
            console.log('[PageRefresh] 自动刷新已禁用');
            return;
        }

        // 设置页面可见性检测
        if (this.config.smartFeatures.visibility_detection) {
            this.setupVisibilityDetection();
        }

        // 设置用户活动检测
        if (this.config.smartFeatures.user_activity_detection) {
            this.setupUserActivityDetection();
        }

        // 启动自动刷新
        if (this.config.mode === 'auto' || this.config.mode === 'smart') {
            this.startAutoRefresh();
        }

        console.log('[PageRefresh] 初始化完成', {
            interval: this.config.interval / 1000,
            mode: this.config.mode,
        });
    }

    // 启动自动刷新
    startAutoRefresh() {
        if (this.state.timerId) {
            clearInterval(this.state.timerId);
        }

        this.state.timerId = setInterval(() => {
            // 智能模式下检查页面可见性和用户活动
            if (this.config.mode === 'smart') {
                if (!this.state.isVisible || !this.state.isUserActive) {
                    console.log('[PageRefresh] 跳过刷新：页面不可见或用户无活动');
                    return;
                }
            }

            this.refresh(false);
        }, this.config.interval);
    }

    // 停止自动刷新
    stopAutoRefresh() {
        if (this.state.timerId) {
            clearInterval(this.state.timerId);
            this.state.timerId = null;
        }
    }

    // 手动刷新
    refresh(showNotification = false) {
        if (this.state.isRefreshing) {
            console.log('[PageRefresh] 正在刷新中，跳过');
            return;
        }

        this.state.isRefreshing = true;
        this.state.lastRefreshTime = new Date();

        // 保存状态
        let scrollPosition = 0;
        if (this.config.preserveState) {
            scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            sessionStorage.setItem('pageRefresh_scrollPosition', scrollPosition);
        }

        // 构建URL（保留查询参数并添加时间戳和缓存破坏参数）
        const urlParams = new URLSearchParams(window.location.search);

        // 移除旧的缓存破坏参数（如果存在）
        urlParams.delete('t');
        urlParams.delete('_cache');

        const currentUrl = window.location.pathname + '?' + urlParams.toString();
        const refreshUrl = currentUrl + '&_cache=' + Date.now();

        console.log('[PageRefresh] 开始刷新', refreshUrl);

        // 直接导航到新URL（而不是fetch + reload）
        // 这样可以确保浏览器获取最新数据
        if (showNotification || this.config.showNotifications) {
            this.showToast('正在刷新...', 'info');
        }

        // 使用replace避免在历史记录中创建多个条目
        window.location.replace(refreshUrl);
    }

    // 设置页面可见性检测
    setupVisibilityDetection() {
        document.addEventListener('visibilitychange', () => {
            this.state.isVisible = !document.hidden;

            if (!this.state.isVisible) {
                console.log('[PageRefresh] 页面隐藏，暂停刷新');
            } else {
                console.log('[PageRefresh] 页面可见，恢复刷新');
            }
        });
    }

    // 设置用户活动检测
    setupUserActivityDetection() {
        let activityTimer;

        const resetActivityTimer = () => {
            this.state.isUserActive = true;
            clearTimeout(activityTimer);

            // 5分钟无操作视为非活动状态
            activityTimer = setTimeout(() => {
                this.state.isUserActive = false;
                console.log('[PageRefresh] 用户无活动，暂停自动刷新');
            }, 5 * 60 * 1000);
        };

        // 监听用户活动事件
        window.addEventListener('mousemove', resetActivityTimer, { passive: true });
        window.addEventListener('keypress', resetActivityTimer, { passive: true });
        window.addEventListener('click', resetActivityTimer, { passive: true });
        window.addEventListener('scroll', resetActivityTimer, { passive: true });

        // 初始化
        resetActivityTimer();
    }

    // Toast通知
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 动画进入
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });

        // 3秒后移除
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 清理资源
    destroy() {
        this.stopAutoRefresh();
        console.log('[PageRefresh] 已清理资源');
    }
}

// 导出到全局（供Alpine.js使用）
window.PageRefreshManager = PageRefreshManager;
