// 认证页面（登录/注册）

const AuthPage = {
    isLoginMode: true,

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-container fade-in">
                <div style="height: 10vh;"></div>

                <!-- Logo 和标题 -->
                <div class="text-center mb-8">
                    <div class="text-6xl mb-4">🎯</div>
                    <h1 class="text-2xl font-bold text-gray-800">口语练习助手</h1>
                    <p class="text-gray-500 mt-2">Oral Practice Partner</p>
                </div>

                <!-- 表单 -->
                <div class="card">
                    <div class="flex mb-6">
                        <button
                            id="loginTab"
                            class="flex-1 py-3 text-center font-medium border-b-2 transition-colors"
                            style="${this.isLoginMode ? 'border-color: #6366F1; color: #6366F1;' : 'border-color: #2A2A2E; color: #71717A;'}"
                        >
                            登录
                        </button>
                        <button
                            id="registerTab"
                            class="flex-1 py-3 text-center font-medium border-b-2 transition-colors"
                            style="${!this.isLoginMode ? 'border-color: #6366F1; color: #6366F1;' : 'border-color: #2A2A2E; color: #71717A;'}"
                        >
                            注册
                        </button>
                    </div>

                    <form id="authForm" onsubmit="return false;">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-medium mb-2">用户名</label>
                            <input
                                type="text"
                                id="username"
                                class="input-field"
                                placeholder="请输入用户名"
                                required
                            />
                        </div>

                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-medium mb-2">密码</label>
                            <input
                                type="password"
                                id="password"
                                class="input-field"
                                placeholder="请输入密码"
                                required
                            />
                        </div>

                        <div id="emailField" class="mb-4 ${this.isLoginMode ? 'hidden' : ''}">
                            <label class="block text-gray-700 text-sm font-medium mb-2">邮箱（可选）</label>
                            <input
                                type="email"
                                id="email"
                                class="input-field"
                                placeholder="请输入邮箱"
                            />
                        </div>

                        <button type="submit" id="submitBtn" class="btn-primary mt-6">
                            ${this.isLoginMode ? '登 录' : '注 册'}
                        </button>
                    </form>

                    <p class="text-center text-gray-500 text-sm mt-4">
                        ${this.isLoginMode ? '还没有账号？' : '已有账号？'}
                        <button
                            id="toggleMode"
                            class="text-primary-500 font-medium"
                        >
                            ${this.isLoginMode ? '立即注册' : '去登录'}
                        </button>
                    </p>
                </div>
            </div>
        `;

        this.bindEvents();
    },

    bindEvents() {
        // 切换登录/注册
        document.getElementById('loginTab').onclick = () => {
            this.isLoginMode = true;
            this.render();
        };

        document.getElementById('registerTab').onclick = () => {
            this.isLoginMode = false;
            this.render();
        };

        document.getElementById('toggleMode').onclick = () => {
            this.isLoginMode = !this.isLoginMode;
            this.render();
        };

        // 提交表单
        document.getElementById('authForm').onsubmit = (e) => {
            e.preventDefault();
            this.handleSubmit();
        };
    },

    async handleSubmit() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const email = document.getElementById('email')?.value.trim() || null;

        if (!username || !password) {
            this.showToast('请填写用户名和密码');
            return;
        }

        if (password.length < 6) {
            this.showToast('密码长度至少为 6 位');
            return;
        }

        const btn = document.getElementById('submitBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="loading"></span>';
        btn.disabled = true;

        try {
            if (this.isLoginMode) {
                await API.login(username, password);
                this.showToast('登录成功');
            } else {
                await API.register(username, password, email);
                this.showToast('注册成功');
            }

            // 检查是否有配置，决定跳转页面
            try {
                const profile = await API.getProfile(true);
                Router.navigate('/scenarios');
            } catch (e) {
                // 没有配置，跳转到配置页面
                Router.navigate('/profile');
            }
        } catch (error) {
            this.showToast(error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    showToast(message) {
        const toast = document.getElementById('toast');
        toast.querySelector('div').textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 2000);
    }
};

window.AuthPage = AuthPage;
