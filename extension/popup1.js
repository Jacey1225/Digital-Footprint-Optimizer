document.addEventListener("DOMContentLoaded", function() {
  // Always hide both first
  document.getElementById("loginSection").style.display = "none";
  document.getElementById("dashboardSection").style.display = "none";

  chrome.storage.local.get(["user_id", "username"], (result) => {
    if (result.user_id && result.username) {
      document.getElementById("dashboardSection").style.display = "block";
    } else {
      document.getElementById("loginSection").style.display = "block";
    }
  });

// 1. User registration/login
  const loginForm = document.getElementById("openLogin");
  if (loginForm) {
    loginForm.addEventListener("submit", async function(e) {
      e.preventDefault();
      const username = document.getElementById("loginUsername").value.trim();
      if (!username) return;
      // Your login logic here (API call, chrome.storage, etc.)
      // Example:
      const res = await fetch("http://localhost:5000/set-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      const data = await res.json();
      chrome.storage.local.set({ user_id: data.user_id, username }, () => {
        // Hide login, show dashboard
        document.getElementById("loginSection").style.display = "none";
        document.getElementById("dashboardSection").style.display = "block";
      });
    });
  }

  // Logout logic
  const logoutBtn = document.querySelector("#logout a"); // or use "#logoutBtn" if you have a button with that id
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      // Optionally clear user info from storage
      chrome.storage.local.remove(["user_id", "username", "tracking_enabled"]);
      // Show login, hide dashboard
      document.getElementById("dashboardSection").style.display = "none";
      document.getElementById("loginSection").style.display = "block";
      // Optionally reset tracking status message
      const statusMsg = document.getElementById("trackingStatus");
      if (statusMsg) statusMsg.style.display = "none";
    });
  }

  const closeIds = ["closeLogin", "closeDashboard", "closeSuggestions"];
  closeIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("click", () => {
        window.close();
      });
    }
  });

  const backBtn = document.getElementById("backToDashboard");
    if (backBtn) {
      backBtn.addEventListener("click", () => {
        document.getElementById("suggestionsSection").style.display = "none";
        document.getElementById("dashboardSection").style.display = "block";
      });
    }

});

chrome.storage.local.get("pattern", (result) => {
  console.log("[popup1.js] Pattern from storage:", result.pattern);
  const pattern = result.pattern;
  if (pattern) {
    const hour = new Date().getHours();
    const inPattern = pattern.some(([start, end]) => hour >= start && hour < end);
    if (inPattern) {
      // Turn on tracker
      chrome.runtime.sendMessage({ type: "start_tracking" });
    } else {
      // Turn off tracker
      chrome.runtime.sendMessage({ type: "stop_tracking" });
    }
  }
});

// Start Tracking logic
const startTrackingBtn = document.getElementById("start_tracking");
if (startTrackingBtn) {
  startTrackingBtn.addEventListener("click", () => {
    // Set tracking state in storage
    chrome.storage.local.set({ tracking_enabled: true });
    // Send message to content script in the active tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, { type: "start_tracking" });
      if (chrome.runtime.lastError) {
        console.warn("No content script in this tab:", chrome.runtime.lastError.message);
      }
    });
    // Show status message
    const statusMsg = document.getElementById("trackingStatus");
    if (statusMsg) {
      statusMsg.style.display = "block";
      statusMsg.textContent = "Tracking has started!";
    }
  });
}

// Stop Tracking logic (if you have a stop button)
const stopTrackingBtn = document.getElementById("stop_tracking");
if (stopTrackingBtn) {
  stopTrackingBtn.addEventListener("click", () => {
    chrome.storage.local.set({ tracking_enabled: false });
    chrome.runtime.sendMessage({ type: "stop_tracking" });
    // Optionally update UI
    document.getElementById("trackingStatus").textContent = "Tracking stopped.";
  });
}

// Optionally, update UI on popup open based on tracking state
chrome.storage.local.get("tracking_enabled", (result) => {
  const statusMsg = document.getElementById("trackingStatus");
  if (result.tracking_enabled && statusMsg) {
    statusMsg.style.display = "block";
    statusMsg.textContent = "Tracking is active.";
  } else if (statusMsg) {
    statusMsg.style.display = "none";
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "showAlternatives") {
    chrome.storage.local.get("alternatives", (res) => {
      if (res.alternatives && Array.isArray(res.alternatives)) {
        showSuggestions(res.alternatives);
      }
    });
  }
});

function showSuggestions(alternatives) {
  document.getElementById("dashboardSection").style.display = "none";
  document.getElementById("suggestionsSection").style.display = "block";
  const list = document.getElementById("suggestionsList");
  list.innerHTML = "";
  alternatives.forEach(suggestion => {
    if (suggestion) {
      const li = document.createElement("li");
      li.textContent = suggestion;
      list.appendChild(li);
    }
  });
}
// Optionally, show suggestions if alternatives are already in storage when popup opens
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get("alternatives", (res) => {
    if (res.alternatives && Array.isArray(res.alternatives)) {
      showSuggestions(res.alternatives);
    }
  });
});

