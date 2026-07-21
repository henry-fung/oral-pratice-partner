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
                    <div class="flex items-center gap-3">
                        <button
                            class="text-primary-500 font-medium text-sm"
                            onclick="ScenariosPage.showCustomScenarioModal()"
                        >
                            ＋ 新增
                        </button>
                        <button
                            class="text-primary-500 font-medium text-sm"
                            onclick="ScenariosPage.regenerateScenarios()"
                        >
                            🔄 刷新
                        </button>
                    </div>
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
                        <div class="flex items-center gap-2">
                            ${scenario.is_practiced ? '<span class="text-green-500 text-xs">✓ 已练习</span>' : ''}
                            ${this.selectedScenarioId === scenario.id ?
                                '<span class="text-primary-500 text-sm">已选择</span>' :
                                '<span class="text-gray-300">›</span>'
                            }
                        </div>
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

    showCustomScenarioModal() {
        document.getElementById('customScenarioModal')?.remove();
        const modal = document.createElement('div');
        modal.id = 'customScenarioModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-end justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-t-2xl w-full max-w-lg p-6 pb-8 max-h-full overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">新增自定义场景</h3>
                    <button class="text-gray-400 text-2xl leading-none" onclick="ScenariosPage.closeCustomScenarioModal()">×</button>
                </div>
                <label class="block text-sm text-gray-600 mb-2">你想练习什么场景？</label>
                <textarea id="customScenarioInput" rows="4" class="input-field mb-4" placeholder="例如：在海外酒店因房间噪音要求换房"></textarea>
                <label class="block text-sm text-gray-600 mb-2">可见范围</label>
                <div class="flex gap-3 mb-4">
                    <label class="flex-1 border border-primary-400 rounded-lg px-3 py-2 text-sm text-primary-600 cursor-pointer">
                        <input type="radio" name="scenarioVisibility" value="private" checked> 私有
                    </label>
                    <label class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-600 cursor-pointer">
                        <input type="radio" name="scenarioVisibility" value="shared"> 共享
                    </label>
                </div>
                <div id="customScenarioDetails" class="hidden">
                    <label class="block text-sm text-gray-600 mb-1">标题</label>
                    <input id="customScenarioTitle" type="text" maxlength="200" class="input-field mb-3" />
                    <label class="block text-sm text-gray-600 mb-1">简介</label>
                    <input id="customScenarioDescription" type="text" maxlength="1000" class="input-field mb-3" />
                    <label class="block text-sm text-gray-600 mb-1">场景背景</label>
                    <textarea id="customScenarioContext" rows="4" maxlength="4000" class="input-field mb-4"></textarea>
                </div>
                <p id="customScenarioError" class="hidden text-sm text-red-500 mb-3"></p>
                <div class="flex gap-3">
                    <button id="enrichScenarioBtn" class="flex-1 btn-secondary" onclick="ScenariosPage.enrichCustomScenario()">丰富</button>
                    <button id="saveScenarioBtn" class="flex-1 btn-primary" onclick="ScenariosPage.saveCustomScenario()">保存</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        document.getElementById('customScenarioInput').focus();
    },

    closeCustomScenarioModal() {
        document.getElementById('customScenarioModal')?.remove();
    },

    _customScenarioError(message = '') {
        const node = document.getElementById('customScenarioError');
        if (!node) return;
        node.textContent = message;
        node.classList.toggle('hidden', !message);
    },

    _setCustomScenarioBusy(busy, label = '') {
        ['enrichScenarioBtn', 'saveScenarioBtn'].forEach(id => {
            const button = document.getElementById(id);
            if (button) button.disabled = busy;
        });
        const enrich = document.getElementById('enrichScenarioBtn');
        if (enrich && label) enrich.textContent = label;
    },

    async enrichCustomScenario() {
        const input = document.getElementById('customScenarioInput')?.value.trim();
        if (!input) {
            this._customScenarioError('请先输入想练习的场景。');
            return;
        }
        this._customScenarioError();
        this._setCustomScenarioBusy(true, '丰富中…');
        try {
            const draft = await API.enrichScenario(input);
            document.getElementById('customScenarioTitle').value = draft.title || '';
            document.getElementById('customScenarioDescription').value = draft.description || '';
            document.getElementById('customScenarioContext').value = draft.context || input;
            document.getElementById('customScenarioDetails').classList.remove('hidden');
        } catch (error) {
            this._customScenarioError(error.message || '场景丰富失败，请稍后重试。');
        } finally {
            this._setCustomScenarioBusy(false, '丰富');
        }
    },

    async saveCustomScenario() {
        const input = document.getElementById('customScenarioInput')?.value.trim();
        if (!input) {
            this._customScenarioError('请先输入想练习的场景。');
            return;
        }
        const detailsVisible = !document.getElementById('customScenarioDetails').classList.contains('hidden');
        const title = detailsVisible ? document.getElementById('customScenarioTitle').value.trim() : input.slice(0, 50);
        const description = detailsVisible ? document.getElementById('customScenarioDescription').value.trim() : '';
        const context = detailsVisible ? document.getElementById('customScenarioContext').value.trim() : input;
        if (!title || !context) {
            this._customScenarioError('标题和场景背景不能为空。');
            return;
        }
        const visibility = document.querySelector('input[name="scenarioVisibility"]:checked').value;
        this._customScenarioError();
        this._setCustomScenarioBusy(true);
        const saveButton = document.getElementById('saveScenarioBtn');
        if (saveButton) saveButton.textContent = '保存中…';
        try {
            const scenario = await API.createCustomScenario({ title, description, context, raw_input: input, visibility });
            this.scenarios.unshift(scenario);
            this.closeCustomScenarioModal();
            this.renderScenariosList();
            this.showToast('场景已保存');
        } catch (error) {
            this._customScenarioError(error.message || '场景保存失败，请稍后重试。');
        } finally {
            this._setCustomScenarioBusy(false);
            if (saveButton) saveButton.textContent = '保存';
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
