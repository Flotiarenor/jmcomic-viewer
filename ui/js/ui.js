class UIManager {
    constructor() {
        this.elements = {
            sidebar: document.getElementById('sidebar'),
            sidebarToggleBtn: document.getElementById('sidebar-toggle-btn'),
            navItems: document.querySelectorAll('.nav-item[data-view]'),
            views: document.querySelectorAll('.view'),
            mangaGrid: document.getElementById('manga-grid'),
            searchInput: document.getElementById('search-input'),
            tagList: document.getElementById('tag-list'),
            authorList: document.getElementById('author-list'),
            statusList: document.getElementById('status-list')
        };
        
        this.initEventListeners();
    }

    initEventListeners() {
        // 侧边栏切换
        this.elements.sidebarToggleBtn.addEventListener('click', () => {
            this.elements.sidebar.classList.toggle('collapsed');
        });

        // 导航点击事件
        this.elements.navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetViewId = item.dataset.view;
                this.switchView(targetViewId);
                this.activateNavItem(item);
            });
        });

        // 搜索功能
        const handleSearch = debounce(async (searchTerm) => {
            try {
                if (!searchTerm) {
                    await this.loadComicsData();
                    return;
                }
                
                const data = await ComicAPI.searchComics(searchTerm);
                this.renderMangaItems(this.elements.mangaGrid, data);
            } catch (error) {
                handleApiError(this.elements.mangaGrid, '搜索失败');
            }
        }, 300);

        this.elements.searchInput.addEventListener('input', (e) => {
            handleSearch(e.target.value);
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key >= '1' && e.key <= '7') {
                const viewIds = [
                    'library-view', 'favorites-view', 'recent-view', 
                    'download-view', 'recommend-view', 'user-view', 'settings-view'
                ];
                const viewId = viewIds[e.key - 1];
                if (viewId) {
                    this.switchView(viewId);
                    const navItem = document.querySelector(`.nav-item[data-view="${viewId}"]`);
                    if (navItem) {
                        this.activateNavItem(navItem);
                    }
                }
            }
        });
    }

    switchView(viewId) {
        this.elements.views.forEach(view => {
            view.classList.remove('active');
        });
        
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
            
            // 根据视图加载对应数据
            switch(viewId) {
                case 'library-view':
                    this.loadComicsData();
                    break;
                case 'download-view':
                    this.loadDownloadsData();
                    break;
                case 'favorites-view':
                    this.loadFavoritesData();
                    break;
                case 'recent-view':
                    this.loadRecentData();
                    break;
                case 'recommend-view':
                    this.loadRecommendData();
                    break;
            }
        }
    }

    activateNavItem(navItem) {
        this.elements.navItems.forEach(item => item.classList.remove('active'));
        navItem.classList.add('active');
    }

    renderMangaItems(gridElement, data) {
        if (!gridElement) return;
        
        gridElement.innerHTML = '';
        
        if (data.length === 0) {
            gridElement.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">没有找到相关漫画</div>';
            return;
        }

        data.forEach(manga => {
            // 计算阅读进度
            const progress = manga.page_count > 0 ? 
                Math.round((manga.last_read_page / manga.page_count) * 100) : 0;
            
            const item = document.createElement('div');
            item.className = 'manga-item';
            item.dataset.comicId = manga.comic_id;
            
            // 根据阅读状态设置样式
            let statusClass = '';
            let statusText = '';
            switch(manga.read_status) {
                case 'unread':
                    statusClass = 'status-unread';
                    statusText = '未读';
                    break;
                case 'reading':
                    statusClass = 'status-reading';
                    statusText = `${progress}%`;
                    break;
                case 'completed':
                    statusClass = 'status-completed';
                    statusText = '已完成';
                    break;
            }
            
            item.innerHTML = `
                <div class="manga-cover-container">
                    <img src="${manga.cover_url}" alt="${manga.title}" loading="lazy" 
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjIyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlNWU1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzljOWN5YyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WKoOi9veWksei0pTwvdGV4dD48L3N2Zz4='">
                    <div class="read-status ${statusClass}">${statusText}</div>
                </div>
                <div class="manga-info">
                    <p class="manga-title" title="${manga.title}">${manga.title}</p>
                    <p class="manga-author" title="${manga.author}">${manga.author}</p>
                    <p class="manga-stats">${manga.last_read_page}/${manga.page_count} 页</p>
                </div>
            `;
            gridElement.appendChild(item);
        });
    }

    renderDownloadItems(data) {
        const downloadList = document.getElementById('download-list');
        if (!downloadList) return;

        downloadList.innerHTML = '';
        
        if (data.length === 0) {
            downloadList.innerHTML = '<p style="color: var(--text-secondary); margin-top: 20px;">暂无下载任务</p>';
            return;
        }

        data.forEach(download => {
            const statusText = download.status === 'downloading' ? '下载中' : '已完成';
            const statusClass = download.status === 'downloading' ? 'status-downloading' : 'status-completed';
            
            const item = document.createElement('div');
            item.className = 'download-item';
            item.innerHTML = `
                <div class="download-info">
                    <p class="download-title" title="${download.title}">${download.title}</p>
                    <p class="download-status ${statusClass}">${statusText}</p>
                </div>
                <div class="download-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${download.progress}%"></div>
                    </div>
                    <span class="progress-text">${download.progress}%</span>
                </div>
            `;
            downloadList.appendChild(item);
        });
    }

    updateFilterPanel(data) {
        if (data.tags) {
            this.elements.tagList.innerHTML = data.tags.map(tag => 
                `<li data-filter="tag" data-value="${tag}">${tag}</li>`
            ).join('');
        }

        if (data.authors) {
            this.elements.authorList.innerHTML = data.authors.map(author => 
                `<li data-filter="author" data-value="${author}">${author}</li>`
            ).join('');
        }

        if (data.read_statuses) {
            this.elements.statusList.innerHTML = data.read_statuses.map(status => {
                const statusText = formatReadStatus(status);
                return `<li data-filter="status" data-value="${status}">${statusText}</li>`;
            }).join('');
        }

        // 添加筛选事件监听
        const filterPanel = document.querySelector('.filter-panel');
        if (filterPanel) {
            filterPanel.querySelectorAll('li').forEach(item => {
                item.addEventListener('click', (e) => {
                    const filterType = e.target.dataset.filter;
                    const filterValue = e.target.dataset.value;
                    this.applyFilter(filterType, filterValue);
                });
            });
        }
    }

    async applyFilter(filterType, filterValue) {
        try {
            const data = await ComicAPI.filterComics(filterType, filterValue);
            this.renderMangaItems(this.elements.mangaGrid, data);
        } catch (error) {
            handleApiError(this.elements.mangaGrid, '筛选失败');
        }
    }

        async loadComicsData() {
        try {
            const data = await ComicAPI.getComicsList();
            this.renderMangaItems(this.elements.mangaGrid, data);
            
            // 加载筛选器数据
            const filterData = await ComicAPI.getFilterOptions();
            this.updateFilterPanel(filterData);
        } catch (error) {
            handleApiError(this.elements.mangaGrid, '加载漫画数据失败');
        }
    }

    async loadDownloadsData() {
        try {
            const data = await ComicAPI.getDownloads();
            this.renderDownloadItems(data);
        } catch (error) {
            const downloadView = document.getElementById('download-view');
            handleApiError(downloadView, '加载下载数据失败');
        }
    }

    async loadFavoritesData() {
        try {
            const data = await ComicAPI.getFavorites();
            const grid = document.getElementById('favorites-grid');
            if (grid) {
                this.renderMangaItems(grid, data);
            }
        } catch (error) {
            const favoritesView = document.getElementById('favorites-view');
            handleApiError(favoritesView, '加载收藏数据失败');
        }
    }

    async loadRecentData() {
        try {
            const data = await ComicAPI.getRecentComics();
            const grid = document.getElementById('recent-grid');
            if (grid) {
                this.renderMangaItems(grid, data);
            }
        } catch (error) {
            const recentView = document.getElementById('recent-view');
            handleApiError(recentView, '加载最近阅读数据失败');
        }
    }

    async loadRecommendData() {
        try {
            const data = await ComicAPI.getRecommendations();
            const grid = document.getElementById('recommend-grid');
            if (grid) {
                this.renderMangaItems(grid, data);
            }
        } catch (error) {
            const recommendView = document.getElementById('recommend-view');
            handleApiError(recommendView, '加载推荐数据失败');
        }
    }
}

           
