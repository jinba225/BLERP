(function() {
    'use strict';

    /**
     * Logo 响应式显示控制器
     * 功能：根据 Logo 宽度自动显示/隐藏公司名称
     */
    
    function adjustBrandText() {
        const brandLink = document.querySelector('#jazzy-logo');
        const logo = brandLink?.querySelector('.brand-image');
        const brandText = brandLink?.querySelector('#brand-text');
        
        if (!logo || !brandText || !brandLink) {
            console.log('Logo 响应式控制器：未找到必要的元素');
            return;
        }
        
        // 等待图片加载完成
        if (!logo.complete || logo.naturalWidth === 0) {
            logo.onload = adjustBrandText;
            logo.onerror = function() {
                console.error('Logo 加载失败，无法检测宽度');
                // Logo 加载失败时，保持文字显示
                brandText.style.display = '';
            };
            return;
        }
        
        const logoWidth = logo.offsetWidth;
        const threshold = 80; // Logo 宽度阈值（像素）
        
        if (logoWidth > threshold) {
            brandText.style.display = 'none';
            brandLink.classList.add('logo-large');
            brandLink.style.justifyContent = 'center';
            logo.style.marginLeft = '0';
            logo.style.marginRight = '0';
            console.log(`Logo 宽度 ${logoWidth}px 超过阈值 ${threshold}px，隐藏品牌名称`);
        } else {
            brandText.style.display = '';
            brandLink.classList.remove('logo-large');
            brandLink.style.justifyContent = '';
            logo.style.marginLeft = '';
            logo.style.marginRight = '';
            console.log(`Logo 宽度 ${logoWidth}px，正常显示品牌名称`);
        }
    }
    
    // 页面加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', adjustBrandText);
    } else {
        adjustBrandText();
    }
    
    // 窗口大小改变时重新检测（防止 CSS 变化导致 Logo 尺寸改变）
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(adjustBrandText, 250); // 防抖 250ms
    });
    
    // 监听侧边栏折叠/展开事件
    const sidebarToggleBtn = document.querySelector('[data-widget="pushmenu"]');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            setTimeout(adjustBrandText, 300); // 等待折叠动画完成
        });
    }
    
})();
