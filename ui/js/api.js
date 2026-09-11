class ComicAPI {
    static async getComicsList() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_comics_list();
        } catch (error) {
            console.error('获取漫画列表失败:', error);
            throw error;
        }
    }

    static async searchComics(keyword) {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.search_comics(keyword);
        } catch (error) {
            console.error('搜索漫画失败:', error);
            throw error;
        }
    }

    static async getDownloads() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_downloads();
        } catch (error) {
            console.error('获取下载列表失败:', error);
            throw error;
        }
    }

    static async getFavorites() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_favorites();
        } catch (error) {
            console.error('获取收藏列表失败:', error);
            throw error;
        }
    }

    static async getFilterOptions() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_filter_options();
        } catch (error) {
            console.error('获取筛选选项失败:', error);
            throw error;
        }
    }

    static async filterComics(filterType, filterValue) {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.filter_comics(filterType, filterValue);
        } catch (error) {
            console.error('筛选漫画失败:', error);
            throw error;
        }
    }

    static async getRecentComics() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_recent_comics();
        } catch (error) {
            console.error('获取最近阅读失败:', error);
            throw error;
        }
    }

    static async getRecommendations() {
        try {
            await waitForPyWebView();
            return await window.pywebview.api.get_recommendations();
        } catch (error) {
            console.error('获取推荐列表失败:', error);
            throw error;
        }
    }
}
