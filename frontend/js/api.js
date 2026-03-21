// API 调用封装

const API_BASE = '';

// 可用角色和语言配置（与后端同步）
const AVAILABLE_ROLES = [
    { id: 'ielts', name: '雅思考生', icon: '📝' },
    { id: 'toefl', name: '托福考生', icon: '📚' },
    { id: 'student', name: '留学生', icon: '🎓' },
    { id: 'business_trade', name: '外贸', icon: '🌐' },
    { id: 'business_dev', name: '程序员', icon: '💻' },
    { id: 'business_data', name: '数据科学家', icon: '📊' },
    { id: 'traveler', name: '旅游者', icon: '✈️' },
    { id: 'daily', name: '日常生活', icon: '🏠' },
    { id: 'custom', name: '自定义', icon: '✏️' },
];

const AVAILABLE_LANGUAGES = [
    { id: 'en', name: '英语', native_name: 'English', flag: '🇺🇸' },
    { id: 'ja', name: '日语', native_name: '日本語', flag: '🇯🇵' },
    { id: 'fr', name: '法语', native_name: 'Français', flag: '🇫🇷' },
    { id: 'es', name: '西班牙语', native_name: 'Español', flag: '🇪🇸' },
    { id: 'de', name: '德语', native_name: 'Deutsch', flag: '🇩🇪' },
    { id: 'ko', name: '韩语', native_name: '한국어', flag: '🇰🇷' },
];

const API = {
    // 内部请求方法
    async request(endpoint, options = {}, silent = false) {
        const url = `${API_BASE}${endpoint}`;
        const token = Storage.getToken();

        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...options.headers,
            }
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            if (!silent) {
                console.error('API Error:', error);
            }
            throw error;
        }
    },

    // GET 请求
    async get(endpoint, silent = false) {
        return this.request(endpoint, { method: 'GET' }, silent);
    },

    // POST 请求
    async post(endpoint, body = {}, silent = false) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        }, silent);
    },

    // PUT 请求
    async put(endpoint, body = {}, silent = false) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        }, silent);
    },

    // DELETE 请求
    async delete(endpoint, silent = false) {
        return this.request(endpoint, { method: 'DELETE' }, silent);
    },

    // === 认证相关 API ===
    async register(username, password, email = null) {
        const data = await this.post('/api/auth/register', { username, password, email });
        if (data.access_token) {
            Storage.setToken(data.access_token);
            Storage.setUser(data);
        }
        return data;
    },

    async login(username, password) {
        const data = await this.post('/api/auth/login', { username, password });
        if (data.access_token) {
            Storage.setToken(data.access_token);
            Storage.setUser(data);
        }
        return data;
    },

    logout() {
        Storage.removeToken();
    },

    // === 用户配置 API ===
    async getProfile(silent = false) {
        return this.get('/api/users/profile', silent);
    },

    async createProfile(profileData) {
        return this.post('/api/users/profile', profileData);
    },

    async updateProfile(profileData) {
        return this.put('/api/users/profile', profileData);
    },

    // === 场景相关 API ===
    async generateScenarios(count = 5) {
        return this.post('/api/scenarios/generate', { count });
    },

    async listScenarios() {
        return this.get('/api/scenarios');
    },

    async getScenario(scenarioId) {
        return this.get(`/api/scenarios/${scenarioId}`);
    },

    async selectScenario(scenarioId) {
        return this.post(`/api/scenarios/${scenarioId}/select`);
    },

    async deleteScenario(scenarioId) {
        return this.delete(`/api/scenarios/${scenarioId}`);
    },

    // === 句子相关 API ===
    async generateSentence(scenarioId) {
        return this.post('/api/sentences/generate', { scenario_id: scenarioId });
    },

    async getSentence(sentenceId) {
        return this.get(`/api/sentences/${sentenceId}`);
    },

    async completeSentence(sentenceId, userAttempt = null) {
        return this.post(`/api/sentences/${sentenceId}/complete`, { user_attempt: userAttempt });
    },

    async listScenarioSentences(scenarioId) {
        return this.get(`/api/sentences/scenario/${scenarioId}/list`);
    },

    // === 单词本相关 API ===
    async lookupWord(word, language) {
        return this.post('/api/vocabulary/lookup', { word, language });
    },

    async getVocabulary(page = 1, limit = 20, mastered = null) {
        const params = new URLSearchParams({ page, limit });
        if (mastered !== null) params.append('mastered', mastered);
        return this.get(`/api/vocabulary?${params}`);
    },

    async addVocabulary(vocabData) {
        return this.post('/api/vocabulary', vocabData);
    },

    async deleteVocabulary(vocabId) {
        return this.delete(`/api/vocabulary/${vocabId}`);
    },

    async markVocabularyMastered(vocabId) {
        return this.put(`/api/vocabulary/${vocabId}/mastered`);
    },

    // === 配置数据 ===
    getAvailableRoles() {
        return AVAILABLE_ROLES;
    },

    getAvailableLanguages() {
        return AVAILABLE_LANGUAGES;
    }
};

window.API = API;
