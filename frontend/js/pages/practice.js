// 练习页面（核心页面）

const PracticePage = {
    currentSentence: null,
    scenario: null,
    showAnswer: false,
    userInput: '',

    async render() {
        const app = document.getElementById('app');

        // 加载练习状态
        const state = Storage.getPracticeState();
        if (!state || !state.scenarioId) {
            // 没有选择场景，跳转到场景页面
            Router.navigate('/scenarios');
            return;
        }

        app.innerHTML = `
            <div class="page-container fade-in" style="padding-bottom: 100px;">
                <!-- 场景标题 -->
                <div class="flex items-center mb-4">
                    <button
                        class="text-gray-400 mr-3"
                        onclick="Router.navigate('/scenarios')"
                    >
                        ←
                    </button>
                    <h1 class="text-lg font-bold text-gray-800" id="scenarioTitle">加载中...</h1>
                </div>

                <!-- 场景描述 -->
                <div class="card mb-4">
                    <p class="text-sm text-gray-600" id="scenarioContext">正在加载场景信息...</p>
                </div>

                <!-- 句子练习区域 -->
                <div id="practiceContent">
                    <div class="text-center py-8">
                        <div class="loading"></div>
                        <p class="text-gray-500 mt-4">正在生成句子...</p>
                    </div>
                </div>
            </div>

            <!-- 底部导航栏 -->
            ${this.renderTabBar('practice')}
        `;

        await this.loadScenario();
    },

    renderTabBar(activeTab) {
        return `
            <div class="tab-bar safe-area-inset-bottom">
                <div class="tab-item" onclick="Router.navigate('/scenarios')">
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

    async loadScenario() {
        const state = Storage.getPracticeState();

        try {
            // 获取场景详情
            this.scenario = await API.getScenario(state.scenarioId);
            document.getElementById('scenarioTitle').textContent = this.scenario.title;
            document.getElementById('scenarioContext').textContent = this.scenario.context || this.scenario.description;

            // 检查是否有已生成的句子
            const sentences = await API.listScenarioSentences(state.scenarioId);

            if (sentences && sentences.length > 0) {
                // 使用最后一个句子
                this.currentSentence = sentences[sentences.length - 1];
                this.showAnswer = false;
                this.renderSentence();
            } else {
                // 生成新句子
                await this.generateNewSentence();
            }
        } catch (error) {
            document.getElementById('practiceContent').innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-4">😕</div>
                    <p class="text-gray-500 mb-4">${error.message}</p>
                    <button class="btn-primary" onclick="PracticePage.render()">重试</button>
                </div>
            `;
        }
    },

    async generateNewSentence() {
        this.showLoading('正在生成句子...');

        try {
            this.currentSentence = await API.generateSentence(this.scenario.id);
            this.showAnswer = false;
            Storage.setPracticeState({
                scenarioId: this.scenario.id,
                sentenceId: this.currentSentence.id,
                showAnswer: false
            });
            this.renderSentence();
        } catch (error) {
            document.getElementById('practiceContent').innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500 mb-4">生成句子失败</p>
                    <button class="btn-primary" onclick="PracticePage.generateNewSentence()">重试</button>
                </div>
            `;
        } finally {
            this.hideLoading();
        }
    },

    renderSentence() {
        const container = document.getElementById('practiceContent');

        if (!this.currentSentence) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500">该场景练习已完成</p>
                    <button class="btn-primary mt-4" onclick="Router.navigate('/scenarios')">选择新场景</button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <!-- 中文提示 -->
            <div class="card mb-4 text-center">
                <p class="text-gray-500 text-sm">场景提示</p>
                <p class="text-base text-gray-800 mt-2">${this.escapeHtml(this.currentSentence.native_text)}</p>
            </div>

            <!-- 输入区域 -->
            <div class="card mb-4">
                <p class="text-gray-500 text-sm mb-2">用目标语言练习说出来</p>
                <textarea
                    id="userInput"
                    class="input-field min-h-[80px]"
                    placeholder="在这里输入你的回答（可选）..."
                    value="${this.userInput || ''}"
                ></textarea>
            </div>

            <!-- 显示答案按钮 -->
            ${!this.showAnswer ? `
                <button
                    class="btn-primary"
                    onclick="PracticePage.toggleAnswer()"
                >
                    显示答案
                </button>
            ` : `
                <!-- 答案区域 -->
                <div class="answer-card mb-4">
                    <p class="text-sm text-gray-500 mb-2">参考答案</p>
                    <p class="text-base font-medium text-gray-800">${this.escapeHtml(this.currentSentence.target_text)}</p>
                </div>

                <!-- 单词查询折叠区域 -->
                <div class="card mb-4">
                    <button
                        class="w-full py-2 text-sm text-gray-500 flex items-center justify-center"
                        onclick="PracticePage.toggleWordQuery()"
                    >
                        <span>📖 单词查询</span>
                        <span id="wordQueryArrow" class="ml-2 transition-transform">▼</span>
                    </button>
                    <div id="wordQueryContent" class="hidden pt-3 border-t border-gray-200">
                        <p class="text-xs text-gray-400 mb-2">点击单词查询释义</p>
                        <div id="wordTags">
                            ${this.renderWordTags(this.currentSentence.target_text)}
                        </div>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="grid grid-cols-2 gap-3">
                    <button
                        class="btn-secondary"
                        onclick="PracticePage.nextSentence()"
                    >
                        下一句
                    </button>
                    <button
                        class="btn-secondary"
                        onclick="PracticePage.nextScenario()"
                    >
                        下一场景
                    </button>
                </div>

                <!-- 标记完成按钮 -->
                <button
                    class="btn-primary mt-3 bg-green-500"
                    onclick="PracticePage.completeSentence()"
                >
                    ✓ 我学会了
                </button>
            `}
        `;

        // 绑定输入事件
        const inputEl = document.getElementById('userInput');
        if (inputEl) {
            inputEl.oninput = (e) => {
                this.userInput = e.target.value;
            };
        }
    },

    renderWordTags(text) {
        // 简单地将句子按空格分割成单词（适用于英文）
        const words = text.split(/[\s\n]+/).filter(w => w.length > 0);
        return words.map(word => {
            // 去除标点符号
            const cleanWord = word.replace(/[.,!?;:"'()]/g, '');
            if (cleanWord.length === 0) return '';
            return `<span class="word-tag" onclick="PracticePage.lookupWord('${this.escapeJs(cleanWord)}')">${this.escapeHtml(cleanWord)}</span>`;
        }).join('');
    },

    async toggleAnswer() {
        this.showAnswer = true;
        Storage.setPracticeState({
            scenarioId: this.scenario.id,
            sentenceId: this.currentSentence.id,
            showAnswer: true
        });
        this.renderSentence();
    },

    toggleWordQuery() {
        const content = document.getElementById('wordQueryContent');
        const arrow = document.getElementById('wordQueryArrow');
        if (content && arrow) {
            content.classList.toggle('hidden');
            arrow.style.transform = content.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
        }
    },

    async completeSentence() {
        try {
            await API.completeSentence(this.currentSentence.id, this.userInput);
            this.showToast('太棒了！继续练习～');
        } catch (error) {
            // 忽略错误
        }
    },

    async nextSentence() {
        // 生成下一句
        this.userInput = '';
        await this.generateNewSentence();
    },

    async nextScenario() {
        // 返回场景列表，让用户选择新场景
        Storage.clearPracticeState();
        Router.navigate('/scenarios');
    },

    async lookupWord(word) {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.querySelector('div').textContent = `正在查询 "${word}"...`;
            toast.classList.remove('hidden');
        }

        try {
            const result = await API.lookupWord(word, this.scenario.language);
            this.showWordDetail(result);
        } catch (error) {
            this.showToast(`查询失败：${error.message}`);
        }
    },

    showWordDetail(wordData) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-xs w-full mx-4" onclick="event.stopPropagation()">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-bold text-gray-800">${this.escapeHtml(wordData.word)}</h3>
                    <button class="text-gray-400 text-2xl" onclick="this.closest('.fixed').remove()">×</button>
                </div>
                <p class="text-gray-600 mb-2">${this.escapeHtml(wordData.definition || '')}</p>
                ${wordData.pronunciation ? `
                    <p class="text-sm text-gray-500 mb-2">发音：${this.escapeHtml(wordData.pronunciation)}</p>
                ` : ''}
                ${wordData.example_sentence ? `
                    <p class="text-sm text-gray-600 italic">"${this.escapeHtml(wordData.example_sentence)}"</p>
                ` : ''}
                <button
                    class="btn-primary mt-4"
                    onclick="PracticePage.addToVocabulary('${this.escapeJs(wordData.word)}', () => this.closest('.fixed').remove())"
                >
                    添加到单词本
                </button>
            </div>
        `;
        modal.onclick = () => modal.remove();
        document.body.appendChild(modal);
    },

    async addToVocabulary(word, callback) {
        try {
            await API.lookupWord(word, this.scenario.language);
            this.showToast('已添加到单词本');
            if (callback) callback();
        } catch (error) {
            this.showToast(error.message);
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    escapeJs(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
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

window.PracticePage = PracticePage;
