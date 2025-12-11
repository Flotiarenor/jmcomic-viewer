document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        sidebar: document.getElementById('sidebar'),
        sidebarToggleBtn: document.getElementById('sidebar-toggle-btn'),
        navItems: document.querySelectorAll('.nav-item[data-view]'),
        views: document.querySelectorAll('.view'),
        viewToggleButtons: document.querySelectorAll('#view-toggle button'),
        mangaGrid: document.getElementById('manga-grid'),
        searchInput: document.getElementById('search-input')
    };

    // 检查PyWebView是否可用
    function isPyWebViewAvailable() {
        return typeof window.pywebview !== 'undefined' && window.pywebview.api;
    }

    // 等待PyWebView准备就绪
    function waitForPyWebView(maxAttempts = 50) {
        return new Promise((resolve, reject) => {
            if (isPyWebViewAvailable()) {
                resolve();
                return;
            }

            let attempts = 0;
            const checkInterval = setInterval(() => {
                attempts++;
                if (isPyWebViewAvailable()) {
                    clearInterval(checkInterval);
                    resolve();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('PyWebView not available after timeout'));
                }
            }, 100);
        });
    }

    // 防抖函数
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 切换侧边栏
    elements.sidebarToggleBtn.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });

    // 视图切换
    function switchView(viewId) {
        elements.views.forEach(view => {
            view.classList.remove('active');
        });
        
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
            
            // 根据视图加载对应数据
            switch(viewId) {
                case 'library-view':
                    loadComicsData();
                    break;
                case 'download-view':
                    loadDownloadsData();
                    break;
                case 'favorites-view':
                    loadFavoritesData();
                    break;
            }
        }
    }

    // 激活导航项
    function activateNavItem(navItem) {
        elements.navItems.forEach(item => item.classList.remove('active'));
        navItem.classList.add('active');
    }

    // 导航点击事件
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetViewId = item.dataset.view;
            switchView(targetViewId);
            activateNavItem(item);
        });
    });

    // 视图模式切换 (网格/列表)
    elements.viewToggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            elements.viewToggleButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const mode = button.dataset.viewMode;
            
            if (mode === 'grid') {
                elements.mangaGrid.className = 'manga-grid';
            } else {
                elements.mangaGrid.className = 'manga-list';
            }
        });
    });

    // 渲染漫画项
    function renderMangaItems(data) {
        if (!elements.mangaGrid) return;
        
        elements.mangaGrid.innerHTML = '';
        
        if (data.length === 0) {
            elements.mangaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">没有找到相关漫画</div>';
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
            elements.mangaGrid.appendChild(item);
        });
    }

    // 渲染下载项
    function renderDownloadItems(data) {
        const downloadView = document.getElementById('download-view');
        if (!downloadView) return;

        let html = '<h2>下载中心</h2>';
        
        if (data.length === 0) {
            html += '<p style="color: var(--text-secondary); margin-top: 20px;">暂无下载任务</p>';
        } else {
            html += '<div class="download-list">';
            data.forEach(download => {
                const statusText = download.status === 'downloading' ? '下载中' : '已完成';
                const statusClass = download.status === 'downloading' ? 'status-downloading' : 'status-completed';
                
                html += `
                    <div class="download-item">
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
                    </div>
                `;
            });
            html += '</div>';
        }
        
        downloadView.innerHTML = html;
    }

    // 从后端获取漫画数据
    async function loadComicsData() {
        try {
            console.log('尝试加载漫画数据...');
            
            // 等待PyWebView准备就绪
            await waitForPyWebView();
            
            console.log('PyWebView可用，调用API...');
            const data = await window.pywebview.api.get_comics_list();
            console.log('获取到数据:', data);
            renderMangaItems(data);
        } catch (error) {
            console.error('加载漫画数据失败:', error);
            if (elements.mangaGrid) {
                elements.mangaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #d9534f;">加载数据失败，请检查后端服务</div>';
            }
        }
    }

    // 从后端获取下载数据
    async function loadDownloadsData() {
        try {
            await waitForPyWebView();
            const data = await window.pywebview.api.get_downloads();
            renderDownloadItems(data);
        } catch (error) {
            console.error('加载下载数据失败:', error);
            const downloadView = document.getElementById('download-view');
            if (downloadView) {
                downloadView.innerHTML = '<h2>下载中心</h2><p style="color: #d9534f; margin-top: 20px;">加载数据失败，请检查后端服务</p>';
            }
        }
    }

    // 加载收藏夹数据
    async function loadFavoritesData() {
        try {
            await waitForPyWebView();
            const data = await window.pywebview.api.get_favorites();
            const favoritesView = document.getElementById('favorites-view');
            if (favoritesView) {
                if (data.length === 0) {
                    favoritesView.innerHTML = `
                        <h2>我的收藏</h2>
                        <p style="color: var(--text-secondary); margin-top: 20px;">暂无收藏的漫画</p>
                    `;
                } else {
                    favoritesView.innerHTML = '<h2>我的收藏</h2><div class="manga-grid" id="favorites-grid"></div>';
                    const grid = document.getElementById('favorites-grid');
                    if (grid) {
                        const tempGrid = elements.mangaGrid;
                        elements.mangaGrid = grid;
                        renderMangaItems(data);
                        elements.mangaGrid = tempGrid;
                    }
                }
            }
        } catch (error) {
            console.error('加载收藏数据失败:', error);
            const favoritesView = document.getElementById('favorites-view');
            if (favoritesView) {
                favoritesView.innerHTML = '<h2>我的收藏</h2><p style="color: #d9534f; margin-top: 20px;">加载数据失败</p>';
            }
        }
    }

    // 搜索功能
    const handleSearch = debounce(async (searchTerm) => {
        try {
            if (!searchTerm) {
                await loadComicsData();
                return;
            }
            
            await waitForPyWebView();
            const data = await window.pywebview.api.search_comics(searchTerm);
            renderMangaItems(data);
        } catch (error) {
            console.error('搜索失败:', error);
            if (elements.mangaGrid) {
                elements.mangaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #d9534f;">搜索失败</div>';
            }
        }
    }, 300);

    elements.searchInput.addEventListener('input', (e) => {
        handleSearch(e.target.value);
    });

    // 初始化 - 等待PyWebView准备就绪后加载数据
    waitForPyWebView()
        .then(() => {
            console.log('PyWebView已准备就绪，开始加载数据...');
            loadComicsData();
        })
        .catch((error) => {
            console.error('PyWebView初始化失败:', error);
            if (elements.mangaGrid) {
                elements.mangaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #d9534f;">前端与后端连接失败，请重启应用</div>';
            }
        });
});
