"""
主题颜色配置
定义三种主题的颜色方案，与前台保持一致
"""

THEME_COLORS = {
    'blue': {
        'primary': '#3b82f6',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#3b82f6',
        'sidebar_bg': '#1e293b',
        'sidebar_header_bg': '#0f172a',
        'sidebar_link_active_bg': '#3b82f6',
        'sidebar_link_active_color': '#ffffff',
        'sidebar_link_color': '#94a3b8',
        'header_bg': '#ffffff',
        'header_text': '#1e293b',
    },
    'yellow': {
        'primary': '#eab308',
        'success': '#22c55e',
        'warning': '#ca8a04',
        'danger': '#ef4444',
        'info': '#eab308',
        'sidebar_bg': '#422006',
        'sidebar_header_bg': '#713f12',
        'sidebar_link_active_bg': '#eab308',
        'sidebar_link_active_color': '#ffffff',
        'sidebar_link_color': '#fde047',
        'header_bg': '#fefce8',
        'header_text': '#422006',
    },
    'red': {
        'primary': '#dc2626',
        'success': '#22c55e',
        'warning': '#f97316',
        'danger': '#b91c1c',
        'info': '#dc2626',
        'sidebar_bg': '#450a0a',
        'sidebar_header_bg': '#7f1d1d',
        'sidebar_link_active_bg': '#dc2626',
        'sidebar_link_active_color': '#ffffff',
        'sidebar_link_color': '#f87171',
        'header_bg': '#fef2f2',
        'header_text': '#450a0a',
    },
}

DEFAULT_THEME = 'blue'

VALID_THEMES = list(THEME_COLORS.keys())
