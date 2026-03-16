// localStorage 封装 - 用于存储 token 和用户信息

const Storage = {
    // 认证相关
    getToken() {
        return localStorage.getItem('access_token');
    },

    setToken(token) {
        localStorage.setItem('access_token', token);
    },

    removeToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('current_user');
    },

    // 用户信息
    getUser() {
        const user = localStorage.getItem('current_user');
        return user ? JSON.parse(user) : null;
    },

    setUser(user) {
        localStorage.setItem('current_user', JSON.stringify(user));
    },

    // 练习状态
    getPracticeState() {
        const state = localStorage.getItem('practice_state');
        return state ? JSON.parse(state) : null;
    },

    setPracticeState(state) {
        localStorage.setItem('practice_state', JSON.stringify(state));
    },

    clearPracticeState() {
        localStorage.removeItem('practice_state');
    },

    // 通用方法
    get(key) {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    },

    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },

    remove(key) {
        localStorage.removeItem(key);
    },

    clear() {
        localStorage.clear();
    }
};

window.Storage = Storage;
