// 单词本页面

const VocabularyPage = {
    vocabulary: [],
    page: 1,
    limit: 20,

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-container fade-in">
                <!-- 头部 -->
                <div class="flex items-center justify-between mb-4">
                    <h1 class="text-xl font-bold text-gray-800">📚 我的单词本</h1>
                    <button
                        class="text-primary-500 font-medium text-sm"
                        onclick="VocabularyPage.showAddModal()"
                    >
                        + 添加
                    </button>
                </div>

                <!-- 筛选 -->
                <div class="flex gap-2 mb-4">
                    <button
                        id="filterAll"
                        class="px-3 py-1 rounded-full text-sm bg-primary-500 text-white"
                        onclick="VocabularyPage.setFilter(null)"
                    >
                        全部
                    </button>
                    <button
                        id="filterUnmastered"
                        class="px-3 py-1 rounded-full text-sm bg-white border border-gray-200"
                        onclick="VocabularyPage.setFilter(false)"
                    >
                        未掌握
                    </button>
                    <button
                        id="filterMastered"
                        class="px-3 py-1 rounded-full text-sm bg-white border border-gray-200"
                        onclick="VocabularyPage.setFilter(true)"
                    >
                        已掌握
                    </button>
                </div>

                <!-- 单词列表 -->
                <div id="vocabularyContent">
                    <div class="text-center py-8">
                        <div class="loading" style="border-top-color: #F97316;"></div>
                        <p class="text-gray-500 mt-4">加载中...</p>
                    </div>
                </div>
            </div>

            <!-- 底部导航栏 -->
            ${this.renderTabBar('vocabulary')}
        `;

        await this.loadVocabulary();
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
                <div class="tab-item ${activeTab === 'vocabulary' ? 'active' : ''}" onclick="Router.navigate('/vocabulary')">
                    <div class="tab-icon">📖</div>
                    <div>单词本</div>
                </div>
            </div>
        `;
    },

    async loadVocabulary() {
        try {
            this.vocabulary = await API.getVocabulary(this.page, this.limit);
            this.renderVocabularyList();
        } catch (error) {
            document.getElementById('vocabularyContent').innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-4">😕</div>
                    <p class="text-gray-500 mb-4">加载失败</p>
                    <button class="btn-primary" onclick="VocabularyPage.render()">重试</button>
                </div>
            `;
        }
    },

    renderVocabularyList() {
        const container = document.getElementById('vocabularyContent');

        if (!this.vocabulary || this.vocabulary.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-4">📝</div>
                    <p class="text-gray-500">单词本是空的</p>
                    <p class="text-sm text-gray-400 mt-2">在练习中点击单词可以添加到这里</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            ${this.vocabulary.map(vocab => `
                <div class="card mb-3">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-2">
                                <h3 class="font-medium text-gray-800 text-lg">${this.escapeHtml(vocab.word)}</h3>
                                ${vocab.is_mastered ? '<span class="text-green-500 text-sm">✓</span>' : ''}
                            </div>
                            ${vocab.definition ? `
                                <p class="text-gray-600 mt-1">${this.escapeHtml(vocab.definition)}</p>
                            ` : ''}
                            ${vocab.pronunciation ? `
                                <p class="text-sm text-gray-400 mt-1">${this.escapeHtml(vocab.pronunciation)}</p>
                            ` : ''}
                            ${vocab.example_sentence ? `
                                <p class="text-sm text-gray-500 italic mt-2">"${this.escapeHtml(vocab.example_sentence)}"</p>
                            ` : ''}
                        </div>
                        <div class="flex gap-2">
                            ${!vocab.is_mastered ? `
                                <button
                                    class="text-green-500 text-sm"
                                    onclick="VocabularyPage.markMastered(${vocab.id})"
                                >
                                    掌握
                                </button>
                            ` : ''}
                            <button
                                class="text-red-400 text-sm"
                                onclick="VocabularyPage.deleteVocabulary(${vocab.id})"
                            >
                                删除
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
        `;
    },

    setFilter(mastered) {
        // 更新筛选按钮样式
        document.getElementById('filterAll').className = mastered === null ?
            'px-3 py-1 rounded-full text-sm bg-primary-500 text-white' :
            'px-3 py-1 rounded-full text-sm bg-white border border-gray-200';
        document.getElementById('filterUnmastered').className = mastered === false ?
            'px-3 py-1 rounded-full text-sm bg-primary-500 text-white' :
            'px-3 py-1 rounded-full text-sm bg-white border border-gray-200';
        document.getElementById('filterMastered').className = mastered === true ?
            'px-3 py-1 rounded-full text-sm bg-primary-500 text-white' :
            'px-3 py-1 rounded-full text-sm bg-white border border-gray-200';

        // 这里可以添加筛选逻辑，暂时简化处理
        this.renderVocabularyList();
    },

    async markMastered(vocabId) {
        try {
            await API.markVocabularyMastered(vocabId);
            this.showToast('已标记为掌握');
            this.loadVocabulary();
        } catch (error) {
            this.showToast(error.message);
        }
    },

    async deleteVocabulary(vocabId) {
        if (!confirm('确定要删除这个单词吗？')) {
            return;
        }

        try {
            await API.deleteVocabulary(vocabId);
            this.showToast('已删除');
            this.loadVocabulary();
        } catch (error) {
            this.showToast(error.message);
        }
    },

    showAddModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-xs w-full mx-4" onclick="event.stopPropagation()">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-bold text-gray-800">添加单词</h3>
                    <button class="text-gray-400 text-2xl" onclick="this.closest('.fixed').remove()">×</button>
                </div>
                <input
                    type="text"
                    id="newWord"
                    class="input-field mb-3"
                    placeholder="单词"
                />
                <input
                    type="text"
                    id="newDefinition"
                    class="input-field mb-3"
                    placeholder="中文释义"
                />
                <button
                    class="btn-primary"
                    onclick="VocabularyPage.addNewWord(() => this.closest('.fixed').remove())"
                >
                    添加
                </button>
            </div>
        `;
        modal.onclick = () => modal.remove();
        document.body.appendChild(modal);
    },

    async addNewWord(callback) {
        const word = document.getElementById('newWord').value.trim();
        const definition = document.getElementById('newDefinition').value.trim();

        if (!word) {
            this.showToast('请输入单词');
            return;
        }

        try {
            await API.addVocabulary({
                word,
                language: 'en', // 默认英语，可以从配置获取
                definition
            });
            this.showToast('添加成功');
            if (callback) callback();
            this.loadVocabulary();
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

    showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.querySelector('div').textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 2000);
    }
};

window.VocabularyPage = VocabularyPage;
