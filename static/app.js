document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("urlInput");
  const qualitySelect = document.getElementById("qualitySelect");
  const btnDownload = document.getElementById("btnDownload");
  const btnFromClipboard = document.getElementById("btnFromClipboard");
  const btnOpenFolder = document.getElementById("btnOpenFolder");
  const taskList = document.getElementById("taskList");
  const activeCountBadge = document.getElementById("activeCountBadge");
  const historyList = document.getElementById("historyList");
  const btnRefreshHistory = document.getElementById("btnRefreshHistory");
  
  // Settings elements
  const cfgDownloadDir = document.getElementById("cfgDownloadDir");
  const cfgDefaultQuality = document.getElementById("cfgDefaultQuality");
  const cfgCookies = document.getElementById("cfgCookies");
  const cfgEnableSubtitles = document.getElementById("cfgEnableSubtitles");
  const cfgNotify = document.getElementById("cfgNotify");
  const btnSaveConfig = document.getElementById("btnSaveConfig");
  const btnBrowseDir = document.getElementById("btnBrowseDir");
  const btnReinstallMenu = document.getElementById("btnReinstallMenu");

  // Load Initial Config
  async function loadConfig() {
    try {
      const res = await fetch("/api/config");
      const cfg = await res.json();
      cfgDownloadDir.value = cfg.download_dir || "";
      cfgDefaultQuality.value = cfg.quality || "best";
      qualitySelect.value = cfg.quality || "best";
      cfgCookies.value = cfg.browser_cookies || "auto";
      cfgEnableSubtitles.checked = !!cfg.enable_subtitles;
      cfgNotify.checked = !!cfg.notify;
    } catch (e) {
      console.error("無法載入設定:", e);
    }
  }

  // Browse Directory
  btnBrowseDir.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/browse-dir", { method: "POST" });
      const data = await res.json();
      if (data.status === "ok" && data.path) {
        cfgDownloadDir.value = data.path;
      }
    } catch (e) {
      alert("瀏覽失敗: " + e);
    }
  });

  // Reinstall Context Menu
  btnReinstallMenu.addEventListener("click", async () => {
    try {
      btnReinstallMenu.disabled = true;
      const res = await fetch("/api/reinstall-menu", { method: "POST" });
      const data = await res.json();
      if (data.status === "ok") {
        alert("✅ Windows 階層式右鍵選單已成功註冊！");
      } else {
        alert("註冊失敗: " + data.message);
      }
    } catch (e) {
      alert("錯誤: " + e);
    } finally {
      btnReinstallMenu.disabled = false;
    }
  });

  // Save Config
  btnSaveConfig.addEventListener("click", async () => {
    try {
      const newCfg = {
        download_dir: cfgDownloadDir.value.trim(),
        quality: cfgDefaultQuality.value,
        browser_cookies: cfgCookies.value,
        enable_subtitles: cfgEnableSubtitles.checked,
        notify: cfgNotify.checked
      };
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newCfg)
      });
      const data = await res.json();
      if (data.status === "ok") {
        alert("✅ 設定儲存成功！");
      }
    } catch (e) {
      alert("儲存失敗: " + e);
    }
  });

  // Start Download
  async function startDownload(url, quality) {
    if (!url) {
      alert("請輸入影片網址！");
      return;
    }
    btnDownload.disabled = true;
    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url,
          quality: quality || qualitySelect.value
        })
      });
      const data = await res.json();
      if (data.status === "ok") {
        urlInput.value = "";
        fetchTasks();
      } else {
        alert("❌ 下載啟動失敗: " + data.message);
      }
    } catch (e) {
      alert("連線伺服器失敗: " + e);
    } finally {
      btnDownload.disabled = false;
    }
  }

  btnDownload.addEventListener("click", () => {
    startDownload(urlInput.value.trim());
  });

  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      startDownload(urlInput.value.trim());
    }
  });

  // Clipboard Trigger
  btnFromClipboard.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/clipboard", { method: "POST" });
      const data = await res.json();
      if (data.status === "ok") {
        fetchTasks();
      } else {
        alert("💡 " + data.message);
      }
    } catch (e) {
      alert("錯誤: " + e);
    }
  });

  // Open Folder
  btnOpenFolder.addEventListener("click", async () => {
    try {
      await fetch("/api/open-folder");
    } catch (e) {
      console.error(e);
    }
  });

  // Poll Active Tasks
  async function fetchTasks() {
    try {
      const res = await fetch("/api/tasks");
      const data = await res.json();
      renderTasks(data.tasks || []);
    } catch (e) {
      // server down or restarting
    }
  }

  function renderTasks(tasks) {
    const activeTasks = tasks.filter(t => t.status !== "completed" && t.status !== "failed");
    activeCountBadge.textContent = `${activeTasks.length} 個任務`;

    if (tasks.length === 0) {
      taskList.innerHTML = `<div class="empty-state">目前無進行中的下載任務</div>`;
      return;
    }

    taskList.innerHTML = tasks.map(t => {
      let statusBadge = `<span class="badge">處理中</span>`;
      if (t.status === "completed") {
        statusBadge = `<span class="badge badge-success">完成</span>`;
      } else if (t.status === "failed") {
        statusBadge = `<span class="badge badge-failed">失敗</span>`;
      }

      return `
        <div class="task-item">
          <div class="task-info">
            <span class="task-title" title="${t.title}">${t.title}</span>
            <div>${statusBadge}</div>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${t.progress || 0}%;"></div>
          </div>
          <div class="task-details">
            <span>下載進度: ${t.progress || 0}% (${t.speed || '0 KB/秒'})</span>
            <span>預估剩餘時間: ${t.eta || '--:--'}</span>
          </div>
        </div>
      `;
    }).join("");
  }

  // Load History
  async function fetchHistory() {
    try {
      const res = await fetch("/api/history");
      const data = await res.json();
      renderHistory(data.history || []);
    } catch (e) {
      console.error(e);
    }
  }

  function renderHistory(list) {
    if (!list || list.length === 0) {
      historyList.innerHTML = `<div class="empty-state">尚無歷史紀錄</div>`;
      return;
    }

    historyList.innerHTML = list.map(item => `
      <div class="history-item">
        <span class="history-title" title="${item.title}">${item.title}</span>
        <div style="display: flex; gap: 8px; align-items: center;">
          <span style="font-size: 11px; color: var(--text-muted);">${item.timestamp}</span>
          <span class="badge ${item.status === 'success' ? 'badge-success' : 'badge-failed'}">
            ${item.status === 'success' ? '下載成功' : '下載未完成'}
          </span>
        </div>
      </div>
    `).join("");
  }

  btnRefreshHistory.addEventListener("click", fetchHistory);

  // Initialize
  loadConfig();
  fetchTasks();
  fetchHistory();
  setInterval(fetchTasks, 1500);
});
