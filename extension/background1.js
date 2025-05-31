importScripts('mock_test_pattern.js');
let pattern = null;
let tabDataUsage = {};

chrome.webRequest.onCompleted.addListener(
  function(details) {
    if (!tabDataUsage[details.tabId]) tabDataUsage[details.tabId] = 0;
    if (details.responseHeaders) {
      const contentLengthHeader = details.responseHeaders.find(h => h.name.toLowerCase() === "content-length");
      if (contentLengthHeader) {
        tabDataUsage[details.tabId] += parseInt(contentLengthHeader.value, 10) || 0;
      }
    }
  },
  {urls: ["<all_urls>"]},
  ["responseHeaders"]
);

// 1. Upload activity at midnight and fetch new pattern
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "uploadActivity") {
    chrome.storage.local.get(["user_id", "activityArray"], async (res) => {
      // Send to /track-behavior
      await fetch("http://localhost:5000/track-behavior", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: res.user_id, daily_hours: res.activity_array }),
      });
      // Fetch new pattern for next day
      const patternRes = await fetch("http://localhost:5000/fetch-pattern", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: res.user_id }),
      });
      const patternData = await patternRes.json();
      pattern = patternData.pattern;
      chrome.storage.local.set({ pattern });
    });
  }
});

// 2. On tab update, check if current hour is in pattern and fetch transfers
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    chrome.storage.local.get(["user_id", "pattern", "tracking_enabled"], async (res) => {
      if (res.tracking_enabled === false) return;
      if (!res.pattern) return;
      const hour = new Date().getHours();
      const inPattern = res.pattern.some(([start, end]) => hour >= start && hour < end);
      if (inPattern) {
        const response = await fetch("http://localhost:5000/fetch-transfers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: res.user_id,
            url: tab.url,
            data_transfer_bytes: tabDataUsage[tab.id] || 0
          }),
        });
        const data = await response.json();
        if (data.alternatives) {
          chrome.storage.local.set({ alternatives: data.alternatives }, () => {
            // Notify popup (if open)
            chrome.runtime.sendMessage({ type: "showAlternatives" });
            // Show browser notification
            chrome.notifications.create({
              type: "basic",
              iconUrl: chrome.runtime.getURL("free-leaf-icon.png"),
              title: "Eco Alternatives Available!",
              message: "Click to view suggestions to reduce your carbon footprint.",
              priority: 2
            }, function(notificationId) {
              if (chrome.runtime.lastError) {
                console.error("Notification error:", chrome.runtime.lastError.message);
              } else {
                console.log("Notification created with ID:", notificationId);
              }
            });
          });
        }
      }
    });
  }
});

chrome.notifications.onClicked.addListener(function(notificationId) {
  // Open the extension popup
  chrome.action.openPopup();
});