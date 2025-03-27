// background.js
console.log("CodeSmart Assistant background script running.");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'setPopup') {
        chrome.action.setPopup({ popup: request.popup }, () => {
            sendResponse({ status: 'success' });
        });
        return true;
    } else if (request.action === 'logout') {
        chrome.storage.local.remove('user', () => {
            chrome.action.setPopup({ popup: 'login.html' }, () => {
                sendResponse({ status: 'success' });
            });
        });
        return true;
    }
});

// Reset popup to login.html on extension startup
chrome.runtime.onStartup.addListener(() => {
    chrome.action.setPopup({ popup: 'login.html' });
});

// background.js
console.log("CodeSmart Assistant background script running.");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'setPopup') {
        chrome.action.setPopup({ popup: request.popup }, () => {
            sendResponse({ status: 'success' });
        });
        return true;
    } else if (request.action === 'logout') {
        chrome.storage.local.remove('user', () => {
            chrome.action.setPopup({ popup: 'login.html' }, () => {
                sendResponse({ status: 'success' });
            });
        });
        return true;
    }
});

// Reset popup to login.html on extension startup
chrome.runtime.onStartup.addListener(() => {
    chrome.action.setPopup({ popup: 'login.html' });
});