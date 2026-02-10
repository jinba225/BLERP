/**
 * 可搜索下拉框工具函数库
 * Searchable Select Utilities
 *
 * 提供防抖、高亮匹配等辅助功能
 */

window.SearchableUtils = (function() {
    'use strict';

    /**
     * 防抖函数 - 延迟执行函数，避免频繁调用
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @return {Function} 防抖后的函数
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
     * 节流函数 - 限制函数执行频率
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 时间间隔（毫秒）
     * @return {Function} 节流后的函数
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 高亮匹配文本
     * @param {string} text - 原始文本
     * @param {string} query - 搜索关键词
     * @param {string} highlightClass - 高亮CSS类名
     * @return {string} 带高亮标记的HTML
     */
    function highlightMatch(text, query, highlightClass = 'bg-yellow-200') {
        if (!query || !text) return text;

        const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
        return text.replace(regex, `<span class="${highlightClass}">$1</span>`);
    }

    /**
     * 转义正则表达式特殊字符
     * @param {string} string - 要转义的字符串
     * @return {string} 转义后的字符串
     */
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * 多字段搜索过滤
     * @param {Array} items - 要过滤的数据项数组
     * @param {string} query - 搜索关键词
     * @param {Array} searchFields - 要搜索的字段名数组
     * @return {Array} 过滤后的数组
     */
    function filterByFields(items, query, searchFields) {
        if (!query || !query.trim()) return items;

        const lowerQuery = query.toLowerCase().trim();
        return items.filter(item => {
            return searchFields.some(field => {
                const value = item[field];
                if (value === null || value === undefined) return false;
                return String(value).toLowerCase().includes(lowerQuery);
            });
        });
    }

    /**
     * 滚动元素到可视区域
     * @param {HTMLElement} element - 要滚动的元素
     * @param {boolean} smooth - 是否平滑滚动
     */
    function scrollIntoView(element, smooth = true) {
        if (!element) return;

        element.scrollIntoView({
            behavior: smooth ? 'smooth' : 'auto',
            block: 'nearest',
            inline: 'nearest'
        });
    }

    /**
     * 生成唯一ID
     * @return {string} 唯一ID
     */
    function generateId() {
        return 'ss-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 安全的JSON解析
     * @param {string} jsonString - JSON字符串
     * @param {*} defaultValue - 解析失败时的默认值
     * @return {*} 解析后的对象或默认值
     */
    function safeJSONParse(jsonString, defaultValue = null) {
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            console.warn('JSON解析失败:', e);
            return defaultValue;
        }
    }

    /**
     * 检查元素是否在视口中
     * @param {HTMLElement} element - 要检查的元素
     * @return {boolean} 是否在视口中
     */
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * 获取元素的显示文本
     * @param {Object} item - 数据项
     * @param {string} displayField - 显示字段名
     * @param {string} fallback - 回退字段
     * @return {string} 显示文本
     */
    function getDisplayText(item, displayField, fallback = 'name') {
        if (!item) return '';
        return item[displayField] || item[fallback] || '';
    }

    /**
     * 格式化显示文本（支持多字段组合）
     * @param {Object} item - 数据项
     * @param {string|Function} formatter - 格式化配置
     * @return {string} 格式化后的文本
     */
    function formatDisplay(item, formatter) {
        if (typeof formatter === 'function') {
            return formatter(item);
        }
        if (typeof formatter === 'string') {
            return item[formatter] || '';
        }
        // 默认返回 name 或 label
        return item.name || item.label || String(item.id || '');
    }

    /**
     * 虚拟滚动计算（仅渲染可见项）
     * @param {Array} items - 所有数据项
     * @param {Object} config - 配置 {itemHeight, containerHeight, scrollTop}
     * @return {Object} {startIndex, endIndex, visibleItems}
     */
    function virtualScroll(items, config) {
        const {
            itemHeight = 40,
            containerHeight = 300,
            scrollTop = 0
        } = config;

        const startIndex = Math.floor(scrollTop / itemHeight);
        const endIndex = Math.min(
            startIndex + Math.ceil(containerHeight / itemHeight) + 1,
            items.length
        );

        const visibleItems = items.slice(startIndex, endIndex);
        const totalHeight = items.length * itemHeight;
        const offsetY = startIndex * itemHeight;

        return {
            startIndex,
            endIndex,
            visibleItems,
            totalHeight,
            offsetY
        };
    }

    // 导出公共API
    return {
        debounce,
        throttle,
        highlightMatch,
        escapeRegExp,
        filterByFields,
        scrollIntoView,
        generateId,
        safeJSONParse,
        isInViewport,
        getDisplayText,
        formatDisplay,
        virtualScroll
    };
})();

// 在控制台暴露API（用于调试）
if (typeof window !== 'undefined') {
    window.SearchableUtilsDebug = window.SearchableUtils;
}
