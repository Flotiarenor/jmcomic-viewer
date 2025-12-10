/**
 * 个人数字漫画库 - 前端交互脚本
 * 负责处理所有UI交互和状态管理
 */

// 等待DOM完全加载后执行
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. DOM元素缓存 ---
    // 频繁操作的DOM元素会被缓存到变量中，提高性能
    const elements = {
        sidebar: document.getElementById('sidebar'),
        sidebarToggleBtn: document.getElementById('sidebar-toggle-btn'),
        navItems: document.querySelectorAll('.nav-item[data-view]'),
        views: document.querySelectorAll('.view'),
        userMenuTrigger: document.getElementById('user-menu-trigger'),
        userPanel: document.getElementById('user-panel'),
        mangaGrid: document.getElementById('manga-grid'),
        searchInput: document.getElementById('search-input'),
        viewToggleButtons: document.querySelectorAll('#view-toggle button'),
        filterPanelItems: document.querySelectorAll('.filter-panel li')
    };

    // --- 2. 核心功能函数 ---

    /**
     * 切换侧边栏的折叠/展开状态
     */
    function toggleSidebar() {
        elements.sidebar.classList.toggle('collapsed');
    }

    /**
     * 切换主内容区的视图
     * @param {string} viewId - 要切换到的视图的ID
     */
    function switchView(viewId) {
        // 移除所有导航项和视图的active类
        elements.navItems.forEach(item => item.classList.remove('active'));
        elements.views.forEach(view => view.classList.remove('active'));

        // 激活目标视图
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
        }
    }

    /**
     * 激活指定的导航项
     * @param {HTMLElement} navItem - 要激活的导航项元素
     */
    function activateNavItem(navItem) {
        elements.navItems.forEach(item => item.classList.remove('active'));
        navItem.classList.add('active');
    }

    /**
     * 渲染漫画网格
     * @param {Array} mangaData - 漫画数据数组
     */
    function renderMangaGrid(mangaData) {
        elements.mangaGrid.innerHTML = ''; // 清空现有内容

        if (mangaData.length === 0) {
            elements.mangaGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">没有找到漫画。</p>';
            return;
        }

        mangaData.forEach(manga => {
            const item = document.createElement('div');
            item.className = 'manga-item';
            item.innerHTML = `
                <img src="${manga.cover}" alt="${manga.title}" onerror="this.src='https://via.placeholder.com/160x220/e9ecef/6c757d?text=No+Cover'">
                <p title="${manga.title}">${manga.title}</p>
            `;
            // 未来可以在这里添加点击事件，例如打开阅读器
            // item.addEventListener('click', () => openReader(manga.id));
            elements.mangaGrid.appendChild(item);
        });
    }

    /**
     * 模拟从后端获取漫画数据
     * 在实际项目中，这里会是一个API调用，例如 fetch('/api/comics')
     * @returns {Promise<Array>} 漫画数据
     */
    function fetchMangaData() {
        return new Promise(resolve => {
            const data = [
                { id: 1, title: '海贼王', author: '尾田荣一郎', cover: 'https://i.imgur.com/placeholder1.png' },
                { id: 2, title: '龙珠', author: '鸟山明', cover: 'https://i.imgur.com/placeholder2.png' },
                { id: 3, title: '鬼灭之刃', author: '吾峠呼世晴', cover: 'https://i.imgur.com/placeholder3.png' },
                { id: 4, title: '咒术回战', author: '芥见下々', cover: 'https://i.imgur.com/placeholder4.png' },
                { id: 5, title: '一拳超人', author: 'ONE', cover: 'https://i.imgur.com/placeholder5.png' },
                { id: 6, title: '间谍过家家', author: '远藤达哉', cover: 'https://i.imgur.com/placeholder6.png' },
                { id: 7, title: '电锯人', author: '藤本树', cover: 'https://i.imgur.com/placeholder7.png' },
                { id: 8, title: '进击的巨人', author: '谏山创', cover: 'https://i.imgur.com/placeholder8.png' },
                { id: 9, title: '石纪元', author: '稲垣理一郎', cover: 'https://i.imgur.com/placeholder9.png' },
                { id: 10, title: '我的英雄学院', author: '堀越耕平', cover: 'https://i.imgur.com/placeholder10.png' },
            ];
            resolve(data);
        });
    }

    /**
     * 处理搜索逻辑
     * @param {string} searchTerm - 搜索关键词
     */
    async function handleSearch(searchTerm) {
        const allManga = await fetchMangaData();
        const filteredManga = allManga.filter(manga => 
            manga.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            manga.author.toLowerCase().includes(searchTerm.toLowerCase())
        );
        renderMangaGrid(filteredManga);
    }


    // --- 3. 事件监听器绑定 ---

    // 侧边栏折叠按钮
    elements.sidebarToggleBtn.addEventListener('click', toggleSidebar);

    // 导航项点击
    elements.navItems.forEach(item => {
        item.addEventListener('click', (event) => {
            const targetViewId = item.dataset.view;
            if (targetViewId) {
                switchView(targetViewId);
                activateNavItem(item);
            }
        });
    });

    // 用户菜单特殊逻辑
    elements.userMenuTrigger.addEventListener('click', (event) => {
        event.stopPropagation(); // 阻止事件冒泡
        elements.userPanel.classList.toggle('active');
        // 激活用户菜单项，但不切换主视图
        activateNavItem(elements.userMenuTrigger);
    });

    // 点击页面其他地方关闭用户面板
    document.body.addEventListener('click', () => {
        if (elements.userPanel.classList.contains('active')) {
            elements.userPanel.classList.remove('active');
            // 恢复“漫画库”为默认激活状态
            activateNavItem(document.querySelector('.nav-item[data-view="library-view"]'));
            switchView('library-view');
        }
    });

    // 阻止点击用户面板内部时关闭面板
    elements.userPanel.addEventListener('click', (event) => {
        event.stopPropagation();
    });

    // 搜索框输入
    elements.searchInput.addEventListener('input', (event) => {
        handleSearch(event.target.value);
    });

    // 视图切换按钮 (网格/列表)
    elements.viewToggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            elements.viewToggleButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const viewMode = button.dataset.viewMode;
            console.log(`切换到 ${viewMode} 视图`); // 未来根据viewMode改变CSS类
            // 例如： elements.mangaGrid.className = viewMode === 'grid' ? 'manga-grid' : 'manga-list';
        });
    });

    // 筛选面板点击
    elements.filterPanelItems.forEach(item => {
        item.addEventListener('click', () => {
            console.log(`筛选器被点击: ${item.textContent}`); // 未来用于筛选
            // 可以在这里添加active状态的样式，并触发筛选逻辑
        });
    });


    // --- 4. 初始化 ---
    async function initializeApp() {
        const initialData = await fetchMangaData();
        renderMangaGrid(initialData);
        console.log('漫画库UI初始化完成');
    }

    initializeApp();

});
