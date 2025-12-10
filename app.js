// app.js
document.addEventListener('DOMContentLoaded', () => {
    // --- 状态管理 ---
    let currentComicPath = null;
    let scale = 1;
    let isDragging = false;
    let startX, startY, scrollLeft, scrollTop;

    // --- DOM 元素 ---
    const selectionView = document.getElementById('selection-view');
    const viewerView = document.getElementById('viewer-view');
    const searchInput = document.getElementById('search-input');
    const clearFilterBtn = document.getElementById('clear-filter-btn');
    const tagsContainer = document.getElementById('tags-container');
    const comicsList = document.getElementById('comics-list');
    
    const backToListBtn = document.getElementById('back-to-list-btn');
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const resetZoomBtn = document.getElementById('reset-zoom-btn');
    const toggleAiBtn = document.getElementById('toggle-ai-btn');
    const pageInfo = document.getElementById('page-info');
    
    const comicImage = document.getElementById('comic-image');
    const imageContainer = document.getElementById('image-container');
    const infoContent = document.getElementById('info-content');

    // --- 初始化 ---
    async function initialize() {
        // 加载预定义标签
        const tags = await pywebview.api.get_predefined_tags();
        renderTags(tags);
        
        // 加载初始漫画列表
        const comics = await pywebview.api.get_comics_list();
        renderComicsList(comics);
    }

    // --- 事件监听器 ---
    searchInput.addEventListener('input', applyFilters);
    clearFilterBtn.addEventListener('click', () => {
        searchInput.value = '';
        document.querySelectorAll('.tag-btn.active').forEach(btn => btn.classList.remove('active'));
        applyFilters();
    });

    backToListBtn.addEventListener('click', showSelectionView);
    prevPageBtn.addEventListener('click', () => navigate('prev'));
    nextPageBtn.addEventListener('click', () => navigate('next'));
    zoomInBtn.addEventListener('click', () => setZoom(scale * 1.2));
    zoomOutBtn.addEventListener('click', () => setZoom(scale * 0.8));
    resetZoomBtn.addEventListener('click', () => setZoom(1));
    toggleAiBtn.addEventListener('click', toggleAiVersion);
    
    // 图片拖拽和滚轮缩放
    imageContainer.addEventListener('mousedown', startDrag);
    imageContainer.addEventListener('mousemove', drag);
    imageContainer.addEventListener('mouseup', endDrag);
    imageContainer.addEventListener('mouseleave', endDrag);
    comicImage.addEventListener('wheel', handleWheel);

    // --- 视图切换函数 ---
    function showSelectionView() {
        viewerView.classList.remove('active');
        selectionView.classList.add('active');
    }
    
    function showViewerView() {
        selectionView.classList.remove('active');
        viewerView.classList.add('active');
    }

    // --- 选择界面逻辑 ---
    function renderTags(tags) {
        tagsContainer.innerHTML = '';
        tags.forEach(tag => {
            const btn = document.createElement('button');
            btn.className = 'tag-btn';
            btn.textContent = tag;
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
                applyFilters();
            });
            tagsContainer.appendChild(btn);
        });
    }

    async function applyFilters() {
        const searchText = searchInput.value;
        const activeTags = Array.from(document.querySelectorAll('.tag-btn.active')).map(btn => btn.textContent);
        
        const comics = await pywebview.api.apply_filters(searchText, activeTags);
        renderComicsList(comics);
    }

    function renderComicsList(comics) {
        comicsList.innerHTML = '';
        comics.forEach(comic => {
            const item = document.createElement('div');
            item.className = 'comic-item';
            item.innerHTML = `
                <img src="${comic.thumbnail || ''}" alt="${comic.title} 封面">
                <div class="comic-details">
                    <h3>${comic.title}</h3>
                    <p><strong>作者:</strong> ${comic.author}</p>
                    <p><strong>标签:</strong> ${comic.tags.join(', ')}</p>
                </div>
            `;
            item.addEventListener('click', () => openComic(comic.path));
            comicsList.appendChild(item);
        });
    }

    // --- 查看器界面逻辑 ---
    async function openComic(path) {
        currentComicPath = path;
        const data = await pywebview.api.open_comic(path);
        
        // 更新信息面板
        let infoHtml = '';
        for (const key in data.info) {
            infoHtml += `<p><strong>${key}:</strong> ${data.info[key]}</p>`;
        }
        infoContent.innerHTML = infoHtml;

        // 更新AI按钮状态
        toggleAiBtn.disabled = !data.is_ai_available;
        toggleAiBtn.textContent = '切换修复版本';

        // 加载第一张图片
        await loadImage();
        showViewerView();
    }
    
    async function navigate(direction) {
        const imageData = await pywebview.api.navigate_image(direction);
        if (imageData) {
            displayImage(imageData);
        }
    }

    async function loadImage() {
        const imageData = await pywebview.api.get_current_image_data();
        if (imageData) {
            displayImage(imageData);
        }
    }

    function displayImage(imageData) {
        comicImage.src = imageData.image_data;
        pageInfo.textContent = imageData.page_info;
        setZoom(1); // 每次换图重置缩放
    }
    
    async function toggleAiVersion() {
        const data = await pywebview.api.toggle_ai_version();
        if (data.error) {
            alert(data.error);
            return;
        }
        
        toggleAiBtn.textContent = data.is_ai_version ? '切换原始版本' : '切换修复版本';
        pageInfo.textContent = data.current_image.page_info;
        comicImage.src = data.current_image.image_data;
        setZoom(1);
    }

    // --- 图片交互逻辑 ---
    function setZoom(newScale) {
        scale = Math.max(0.1, Math.min(newScale, 5));
        comicImage.style.transform = `scale(${scale})`;
    }

    function handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(scale * delta);
    }
    
    function startDrag(e) {
        isDragging = true;
        imageContainer.classList.add('dragging');
        startX = e.pageX - imageContainer.offsetLeft;
        startY = e.pageY - imageContainer.offsetTop;
        scrollLeft = imageContainer.scrollLeft;
        scrollTop = imageContainer.scrollTop;
    }

    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.pageX - imageContainer.offsetLeft;
        const y = e.pageY - imageContainer.offsetTop;
        const walkX = (x - startX) * 1.5;
        const walkY = (y - startY) * 1.5;
        imageContainer.scrollLeft = scrollLeft - walkX;
        imageContainer.scrollTop = scrollTop - walkY;
    }

    function endDrag() {
        isDragging = false;
        imageContainer.classList.remove('dragging');
    }
    
    // --- 启动应用 ---
    initialize();
});
