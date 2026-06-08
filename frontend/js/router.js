// 简单的前端路由

const Router = {
    routes: {},
    currentRoute: null,

    // 注册路由
    register(path, handler) {
        this.routes[path] = handler;
    },

    // 导航到指定路由
    async navigate(path) {
        this.currentRoute = path;
        window.location.hash = path;

        // 执行路由处理
        if (this.routes[path]) {
            await this.routes[path]();
        } else {
            // 默认重定向到首页
            this.navigate('/auth');
        }
    },

    // 获取当前路径
    getPath() {
        return window.location.hash.slice(1) || '/auth';
    },

    // 初始化路由
    init() {
        // 监听 hash 变化（仅处理浏览器前进/后退，navigate() 已直接调用处理器）
        window.addEventListener('hashchange', () => {
            const path = this.getPath();
            // 如果是 navigate() 触发的，currentRoute 已匹配，跳过避免双重渲染
            if (path === this.currentRoute) return;
            if (this.routes[path]) {
                this.currentRoute = path;
                this.routes[path]();
            }
        });

        // 初始化时检查登录状态
        const token = Storage.getToken();
        const path = this.getPath();

        if (token) {
            // 已登录，检查是否有配置
            if (path === '/auth' || path === '') {
                this.navigate('/profile');
            } else {
                this.navigate(path);
            }
        } else {
            // 未登录，只能访问 auth 页面
            if (path !== '/auth') {
                this.navigate('/auth');
            } else {
                this.navigate(path);
            }
        }
    }
};

window.Router = Router;
