// 场景选择页面

const ScenariosPage = {
    scenarios: [],
    selectedScenarioId: null,

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-container fade-in">
                <!-- 头部 -->
                <div class="flex items-center justify-between mb-4">
                    <h1 class="text-xl font-bold text-gray-800">选择练习场景</h1>
                    <button
                        class="text-primary-500 font-medium text-sm"
                        onclick="ScenariosPage.regenerateScenarios()"
                    >
                        🔄 刷新
                    </button>
                </div>

                <!-- 加载状态或场景列表 -->
                <div id="scenariosContent">
                    <div class="text-center py-8">
                        <div class="loading"></div>
                        <p class="text-gray-500 mt-4">正在生成场景...</p>
                    </div>
                </div>
            </div>

            <!-- 底部导航栏 -->
            ${this.renderTabBar('scenarios')}
        `;

        await this.loadScenarios();
    },

    renderTabBar(activeTab) {
        return `
            <div class="tab-bar safe-area-inset-bottom">
                <div class="tab-item ${activeTab === 'scenarios' ? 'active' : ''}" onclick="Router.navigate('/scenarios')">
                    <div class="tab-icon">📚</div>
                    <div>场景</div>
                </div>
                <div class="tab-item" onclick="Router.navigate('/profile')">
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

    async loadScenarios() {
        try {
            // 先尝试获取已有场景
            let scenarios = await API.listScenarios();

            // 如果没有场景，生成新的
            if (!scenarios || scenarios.length === 0) {
                this.showLoading('正在生成场景...');
                try {
                    scenarios = await API.generateScenarios(5);
                } finally {
                    this.hideLoading();
                }
            }

            this.scenarios = scenarios;
            this.renderScenariosList();
        } catch (error) {
            this.hideLoading();
            document.getElementById('scenariosContent').innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-4">😕</div>
                    <p class="text-gray-500 mb-4">${error.message}</p>
                    <button class="btn-primary" onclick="ScenariosPage.render()">重试</button>
                </div>
            `;
        }
    },

    renderScenariosList() {
        const container = document.getElementById('scenariosContent');

        if (this.scenarios.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500">暂无场景</p>
                </div>
            `;
            return;
        }

        // 找到已选择的场景
        const selected = this.scenarios.find(s => s.is_selected);
        if (selected) {
            this.selectedScenarioId = selected.id;
        }

        container.innerHTML = `
            <p class="text-gray-500 text-sm mb-4">
                为你生成了 ${this.scenarios.length} 个场景，选择一个开始练习
            </p>
            ${this.scenarios.map(scenario => `
                <div
                    class="scenario-card ${this.selectedScenarioId === scenario.id ? 'selected' : ''}"
                    onclick="ScenariosPage.selectScenario(${scenario.id})"
                >
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h3 class="font-medium text-gray-800">${this.escapeHtml(scenario.title)}</h3>
                            <p class="text-sm text-gray-500 mt-1">${this.escapeHtml(scenario.description || '')}</p>
                        </div>
                        ${this.selectedScenarioId === scenario.id ?
                            '<span class="text-primary-500 text-sm">已选择</span>' :
                            '<span class="text-gray-300">›</span>'
                        }
                    </div>
                </div>
            `).join('')}

            ${this.selectedScenarioId ? `
                <button
                    class="btn-primary mt-4"
                    onclick="Router.navigate('/practice')"
                >
                    开始练习
                </button>
            ` : ''}
        `;
    },

    async selectScenario(scenarioId) {
        try {
            await API.selectScenario(scenarioId);
            this.selectedScenarioId = scenarioId;
            this.renderScenariosList();

            // 保存当前场景 ID 到状态
            Storage.setPracticeState({ scenarioId, sentenceId: null, showAnswer: false });

            // 自动跳转到练习页面
            Router.navigate('/practice');
        } catch (error) {
            this.showToast(error.message);
        }
    },

    async regenerateScenarios() {
        if (!confirm('确定要刷新场景吗？当前场景将被替换。')) {
            return;
        }

        this.showLoading('正在生成新场景...');

        try {
            const scenarios = await API.generateScenarios(5);
            this.scenarios = scenarios;
            this.selectedScenarioId = null;
            Storage.clearPracticeState();
            this.renderScenariosList();
        } catch (error) {
            this.showToast(error.message);
            await this.loadScenarios();
        } finally {
            this.hideLoading();
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.querySelector('div').textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 2000);
    },

    showLoading(message) {
        const app = document.getElementById('app');
        const existingModal = app.querySelector('.loading-modal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.className = 'loading-modal fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 text-center">
                <div class="loading loading-lg mx-auto mb-4"></div>
                <p class="text-gray-600">${message}</p>
            </div>
        `;
        app.appendChild(modal);
    },

    hideLoading() {
        const app = document.getElementById('app');
        const modal = app.querySelector('.loading-modal');
        if (modal) modal.remove();
    }
};

window.ScenariosPage = ScenariosPage;
