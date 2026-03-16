// 主应用入口

// 注册所有路由
Router.register('/auth', () => {
    AuthPage.render();
});

Router.register('/profile', () => {
    ProfilePage.render();
});

Router.register('/scenarios', () => {
    ScenariosPage.render();
});

Router.register('/practice', () => {
    PracticePage.render();
});

Router.register('/vocabulary', () => {
    VocabularyPage.render();
});

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('口语练习助手启动中...');

    // 初始化路由
    Router.init();
});

// 全局错误处理
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('全局错误:', msg, error);
    return false;
};
