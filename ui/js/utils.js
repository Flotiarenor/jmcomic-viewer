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

// 统一错误处理
function handleApiError(viewElement, message = '加载失败') {
    if (viewElement) {
        viewElement.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #d9534f;">${message}</div>`;
    }
}

// 格式化阅读状态
function formatReadStatus(status) {
    switch(status) {
        case 'unread': return '未读';
        case 'reading': return '在读';
        case 'completed': return '已完成';
        default: return status;
    }
}
