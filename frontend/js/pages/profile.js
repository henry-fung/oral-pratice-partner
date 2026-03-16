// 配置页面（角色和语言选择）

const ProfilePage = {
    selectedRole: null,
    customRoleName: '',
    selectedLanguage: 'en',
    selectedLevel: 'intermediate',

    async render() {
        const user = Storage.getUser();
        const app = document.getElementById('app');

        // 尝试获取现有配置
        let existingProfile = null;
        try {
            existingProfile = await API.getProfile();
            this.selectedRole = existingProfile.role;
            this.selectedLanguage = existingProfile.target_language;
            this.selectedLevel = existingProfile.proficiency_level;
        } catch (e) {
            // 没有配置，使用默认值
        }

        const roles = API.getAvailableRoles();
        const languages = API.getAvailableLanguages();
        const levels = [
            { id: 'beginner', name: '初级', description: '刚开始学习' },
            { id: 'intermediate', name: '中级', 'description': '有一定基础' },
            { id: 'advanced', name: '高级', description: '流利交流' }
        ];

        app.innerHTML = `
            <div class="page-container fade-in">
                <!-- 头部 -->
                <div class="flex items-center justify-between mb-6">
                    <h1 class="text-xl font-bold text-gray-800">设置学习目标</h1>
                    <span class="text-sm text-gray-500">${user?.username || '用户'}</span>
                </div>

                <p class="text-gray-600 mb-6">选择你的角色和想要练习的语言</p>

                <!-- 角色选择 -->
                <div class="mb-6">
                    <h2 class="text-lg font-medium text-gray-800 mb-3">选择你的角色</h2>
                    <div class="grid grid-cols-2 gap-3">
                        ${roles.map(role => `
                            <div
                                class="role-card ${this.selectedRole === role.id ? 'selected' : ''}"
                                onclick="ProfilePage.selectRole('${role.id}')"
                            >
                                <div class="text-3xl mb-2">${role.icon}</div>
                                <div class="font-medium text-gray-800">${role.name}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- 语言选择 -->
                <div class="mb-6">
                    <h2 class="text-lg font-medium text-gray-800 mb-3">选择目标语言</h2>
                    <div class="grid grid-cols-3 gap-3">
                        ${languages.map(lang => `
                            <div
                                class="language-btn ${this.selectedLanguage === lang.id ? 'selected' : ''}"
                                onclick="ProfilePage.selectLanguage('${lang.id}')"
                            >
                                <div class="text-2xl mb-1">${lang.flag}</div>
                                <div class="text-xs text-gray-600">${lang.name}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- 水平选择 -->
                <div class="mb-6">
                    <h2 class="text-lg font-medium text-gray-800 mb-3">当前水平</h2>
                    <div class="grid grid-cols-3 gap-3">
                        ${levels.map(level => `
                            <div
                                class="language-btn ${this.selectedLevel === level.id ? 'selected' : ''}"
                                onclick="ProfilePage.selectLevel('${level.id}')"
                            >
                                <div class="font-medium text-gray-800">${level.name}</div>
                                <div class="text-xs text-gray-500">${level.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- 提交按钮 -->
                <button
                    id="saveBtn"
                    class="btn-primary"
                    onclick="ProfilePage.saveProfile()"
                >
                    ${existingProfile ? '保存修改' : '开始练习'}
                </button>

                <!-- 退出登录 -->
                <button
                    class="btn-secondary mt-3"
                    onclick="ProfilePage.logout()"
                >
                    退出登录
                </button>
            </div>

            <!-- 底部导航栏 -->
            ${this.renderTabBar('profile')}
        `;
    },

    renderTabBar(activeTab) {
        return `
            <div class="tab-bar safe-area-inset-bottom">
                <div class="tab-item" onclick="Router.navigate('/scenarios')">
                    <div class="tab-icon">📚</div>
                    <div>场景</div>
                </div>
                <div class="tab-item ${activeTab === 'profile' ? 'active' : ''}" onclick="Router.navigate('/profile')">
                    <div class="tab-icon">⚙️</div>
                    <div>设置</div>
                </div>
                <div class="tab-item" onclick="Router.navigate('/vocabulary')">
                    <div class="tab-icon">📖</div>
                    <div>单词本</div>
                </div>
            </div>
        `;
    },

    selectRole(roleId) {
        if (roleId === 'custom') {
            const customName = prompt('请输入你的角色名称（例如：医生、律师、教师等）：');
            if (customName && customName.trim()) {
                this.customRoleName = customName.trim();
                this.selectedRole = roleId;
                this.render();
            }
        } else {
            this.selectedRole = roleId;
            this.customRoleName = '';
            this.render();
        }
    },

    selectLanguage(langId) {
        this.selectedLanguage = langId;
        this.render();
    },

    selectLevel(levelId) {
        this.selectedLevel = levelId;
        this.render();
    },

    async saveProfile() {
        if (!this.selectedRole) {
            this.showToast('请选择一个角色');
            return;
        }

        // 如果选择自定义角色，验证是否输入了名称
        if (this.selectedRole === 'custom' && !this.customRoleName.trim()) {
            this.showToast('请输入自定义角色名称');
            return;
        }

        const btn = document.getElementById('saveBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="loading"></span>';
        btn.disabled = true;

        try {
            // 尝试获取现有配置
            let existingProfile = null;
            try {
                existingProfile = await API.getProfile();
            } catch (e) {
                // 没有配置
            }

            const profileData = {
                role: this.selectedRole,
                target_language: this.selectedLanguage,
                proficiency_level: this.selectedLevel
            };

            // 如果是自定义角色，添加自定义名称
            if (this.selectedRole === 'custom') {
                profileData.custom_role_name = this.customRoleName;
            }

            if (existingProfile) {
                await API.updateProfile(profileData);
                this.showToast('保存成功');
            } else {
                await API.createProfile(profileData);
                this.showToast('配置成功');
            }

            // 跳转到场景页面
            setTimeout(() => {
                Router.navigate('/scenarios');
            }, 500);
        } catch (error) {
            this.showToast(error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    logout() {
        if (confirm('确定要退出登录吗？')) {
            API.logout();
            Router.navigate('/auth');
        }
    },

    showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.querySelector('div').textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 2000);
    }
};

window.ProfilePage = ProfilePage;
