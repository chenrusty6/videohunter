const SERVER_BASE = "http://127.0.0.1:58231";
const SERVER_URL = `${SERVER_BASE}/api/download`;

function setupContextMenu() {
  chrome.contextMenus.removeAll(() => {
    // Parent Menu
    chrome.contextMenus.create({
      id: "vh_root",
      title: "🎬 影速獵手",
      contexts: ["all"]
    });

    // 1. Download to default directory
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_dl_default",
      title: "📥 下載影片至預設影片庫",
      contexts: ["all"]
    });

    // 2. Pick folder then download
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_dl_pick",
      title: "📂 選擇資料夾後下載...",
      contexts: ["all"]
    });

    // 3. Download MP3 only
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_dl_mp3",
      title: "🎵 僅下載高音質 MP3 (音樂)",
      contexts: ["all"]
    });

    // Separator
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_sep_1",
      type: "separator",
      contexts: ["all"]
    });

    // 4. Open destination folder
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_open_folder",
      title: "📁 打開影片庫資料夾",
      contexts: ["all"]
    });

    // 5. Open Web Dashboard
    chrome.contextMenus.create({
      parentId: "vh_root",
      id: "vh_open_dash",
      title: "🖥️ 開啟影速獵手管理台",
      contexts: ["all"]
    });
  });
}

// Ensure menu is registered on install, startup, and immediate evaluation
chrome.runtime.onInstalled.addListener(setupContextMenu);
chrome.runtime.onStartup.addListener(setupContextMenu);
setupContextMenu();

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const itemId = info.menuItemId;

  // 1. Open destination folder in Windows Explorer
  if (itemId === "vh_open_folder") {
    try {
      await fetch(`${SERVER_BASE}/api/open-folder`);
    } catch (err) {
      notifyError("後台服務尚未啟動，請執行 start_service.vbs！");
    }
    return;
  }

  // 2. Open Web Dashboard
  if (itemId === "vh_open_dash") {
    chrome.tabs.create({ url: `${SERVER_BASE}/` });
    return;
  }

  // 3. Download actions (vh_dl_default, vh_dl_pick, vh_dl_mp3)
  if (itemId === "vh_dl_default" || itemId === "vh_dl_pick" || itemId === "vh_dl_mp3") {
    let targetUrl = null;

    // A. Query content script for precisely clicked video element or card link
    if (tab && tab.id) {
      try {
        const response = await chrome.tabs.sendMessage(tab.id, { action: "getVideoUrl" });
        if (response && response.url) {
          targetUrl = response.url;
        }
      } catch (e) {
        // Tab might not support content scripts
      }
    }

    // B. Check linkUrl or media srcUrl
    if (!targetUrl) {
      targetUrl = info.linkUrl || info.srcUrl;
    }

    // C. Fallback to tab.url or pageUrl
    if (!targetUrl) {
      targetUrl = info.pageUrl || tab?.url;
    }

    // Guard against generic homepages
    if (!targetUrl || targetUrl === "https://www.instagram.com/" || targetUrl === "https://www.facebook.com/" || targetUrl === "https://www.threads.net/") {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon48.png",
        title: "影速獵手 · 提示",
        message: "請將滑鼠移至特定影片或貼文上方，再點擊右鍵下載！"
      });
      return;
    }

    const payload = {
      url: targetUrl,
      quality: itemId === "vh_dl_mp3" ? "mp3" : "best",
      pick_folder: itemId === "vh_dl_pick"
    };

    try {
      const response = await fetch(SERVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`伺服器回應錯誤: ${response.status}`);
      }

      const data = await response.json();
      if (data.status === "canceled") {
        return;
      }

      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon48.png",
        title: "影速獵手 · 下載已啟動",
        message: "已加入背景下載佇列，完成後將在右下角彈出截圖通知！"
      });
    } catch (err) {
      console.error("[影速獵手] 連線失敗:", err);
      notifyError("本機後台服務尚未啟動，請執行 start_service.vbs 或在資料夾右鍵「影速獵手」！");
    }
  }
});

function notifyError(msg) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon48.png",
    title: "影速獵手 · 連線提示",
    message: msg
  });
}
