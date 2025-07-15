// 通用主题切换系统
class ThemeManager {
    constructor() {
        this.body = document.body;
        this.savedTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // 设置初始主题
        this.body.setAttribute('data-theme', this.savedTheme);
        
        // 创建主题切换按钮
        this.createThemeToggle();
        
        // 更新图标
        this.updateThemeIcon(this.savedTheme);
    }

    createThemeToggle() {
        // 检查是否已存在主题切换按钮
        if (document.getElementById('themeToggle')) {
            this.bindEvents();
            return;
        }

        // 创建主题切换按钮
        const themeToggle = document.createElement('button');
        themeToggle.id = 'themeToggle';
        themeToggle.className = 'theme-toggle';
        themeToggle.title = '切换主题';
        
        const themeIcon = document.createElement('i');
        themeIcon.id = 'themeIcon';
        themeIcon.className = 'theme-icon fas fa-sun';
        
        themeToggle.appendChild(themeIcon);
        document.body.appendChild(themeToggle);
        
        this.bindEvents();
    }

    bindEvents() {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    toggleTheme() {
        const currentTheme = this.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        this.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('themeIcon');
        const themeToggle = document.getElementById('themeToggle');
        
        if (themeIcon && themeToggle) {
            if (theme === 'light') {
                themeIcon.className = 'theme-icon fas fa-sun';
                themeToggle.title = '切换到夜晚模式';
            } else {
                themeIcon.className = 'theme-icon fas fa-moon';
                themeToggle.title = '切换到白天模式';
            }
        }
    }

    getCurrentTheme() {
        return this.body.getAttribute('data-theme');
    }

    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            this.updateThemeIcon(theme);
        }
    }
}

// 页面加载时初始化主题管理器
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
});

// 导出给其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
} 