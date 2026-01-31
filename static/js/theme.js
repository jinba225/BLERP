/**
 * 主题切换功能
 * 通过修改CSS变量实现动态主题色切换
 */

// 定义主题色配置
const themeConfig = {
    red: {
        500: '#ef4444',
        600: '#dc2626',
        100: '#fee2e2',
    },
    orange: {
        500: '#f97316',
        600: '#ea580c',
        100: '#ffedd5',
    },
    blue: {
        500: '#3b82f6',
        600: '#2563eb',
        100: '#dbeafe',
    }
};

// 初始化主题色
function initTheme() {
    const savedTheme = localStorage.getItem('jazzmin-theme') || 'blue';
    changeTheme(savedTheme);
}

// 切换主题色
function changeTheme(themeName) {
    const theme = themeConfig[themeName];
    if (!theme) {
        console.warn(`Theme "${themeName}" not found`);
        return;
    }

    const root = document.documentElement;

    // 遍历主题色变量，设置到根元素
    Object.keys(theme).forEach(key => {
        root.style.setProperty(`--theme-${key}`, theme[key]);
    });

    // 持久化到localStorage
    localStorage.setItem('jazzmin-theme', themeName);

    // 更新按钮状态
    updateThemeButtons(themeName);

    console.log(`Theme changed to: ${themeName}`);
}

// 更新主题按钮状态
function updateThemeButtons(activeTheme) {
    document.querySelectorAll('.theme-btn').forEach(btn => {
        const btnTheme = btn.dataset.theme;
        if (btnTheme === activeTheme) {
            btn.classList.add('ring-2', 'ring-offset-2', 'ring-gray-400');
            btn.style.transform = 'scale(1.1)';
        } else {
            btn.classList.remove('ring-2', 'ring-offset-2', 'ring-gray-400');
            btn.style.transform = 'scale(1)';
        }
    });
}

// 添加主题切换按钮到页面
function addThemeButtons() {
    // 检查是否已存在
    if (document.getElementById('theme-switcher')) {
        console.log('主题切换器已存在');
        return;
    }

    console.log('开始添加主题切换按钮...');

    // 创建按钮容器
    const buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'theme-switcher';
    buttonsContainer.style.cssText = `
        position: fixed !important;
        top: 1rem !important;
        right: 1rem !important;
        z-index: 99999 !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        background: white;
        padding: 0.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    `;

    // 添加3个主题按钮
    const themes = [
        { name: 'red', color: '#ef4444', title: '红色主题' },
        { name: 'orange', color: '#f97316', title: '橙色主题' },
        { name: 'blue', color: '#3b82f6', title: '蓝色主题' },
    ];

    themes.forEach(theme => {
        const btn = document.createElement('button');
        btn.className = 'theme-btn';
        btn.dataset.theme = theme.name;
        btn.style.cssText = `
            width: 2rem !important;
            height: 2rem !important;
            border-radius: 50% !important;
            border: 2px solid #e5e7eb !important;
            cursor: pointer;
            transition: all 0.2s;
            background-color: ${theme.color};
        `;
        btn.title = theme.title;
        buttonsContainer.appendChild(btn);
        btn.addEventListener('click', () => changeTheme(theme.name));
    });

    document.body.appendChild(buttonsContainer);
    console.log('主题切换按钮已添加');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM加载完成，初始化主题...');
        initTheme();
        addThemeButtons();
    });
} else {
    setTimeout(() => {
        console.log('页面已加载，初始化主题...');
        initTheme();
        addThemeButtons();
    }, 100);
}

console.log('主题切换脚本已加载');
