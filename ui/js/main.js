// 主应用启动文件
let uiManager = null;

// 初始化应用
async function initApp() {
    try {
        // 等待PyWebView准备就绪
        await waitForPyWebView();
        console.log('PyWebView已准备就绪');
        
        // 初始化UI管理器
        uiManager = new UIManager();
        
        // 加载初始数据
        await uiManager.loadComicsData();
        
    } catch (error) {
        console.error('应用初始化失败:', error);
        const mangaGrid = document.getElementById('manga-grid');
        if (mangaGrid) {
            mangaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #d9534f;">前端与后端连接失败，请重启应用</div>';
        }
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', initApp);
