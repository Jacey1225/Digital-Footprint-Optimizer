console.log("[content1.js] Content script loaded!");

let activityArray = new Array(24).fill(0);
let trackingEnabled = false;
let listenersAdded = false;
let hourlyTimeoutId = null;
let midnightTimeoutId = null;

// Track activity per minute
let minuteActiveFlags = new Array(60).fill(false); // For current hour

function markActivity(event) {
  try {
    if (!trackingEnabled) return;
    const now = new Date();
    const minute = now.getMinutes();
    minuteActiveFlags[minute] = true;
    console.log(`[Activity] ${event.type} detected at minute ${minute}: user is active.`);
  } catch (err) {
    console.warn("markActivity error:", err);
  }
}

// At the start of each hour, calculate and store the previous hour's activity percentage
function scheduleHourlyUpdate() {
  if (!trackingEnabled) return;
  const now = new Date();
  const millisTillNextHour = (60 - now.getMinutes()) * 60 * 1000 - now.getSeconds() * 1000 - now.getMilliseconds();
  hourlyTimeoutId = setTimeout(() => {
    if (!trackingEnabled) return;
    const prevHour = (new Date().getHours() - 1 + 24) % 24;
    const activeMinutes = minuteActiveFlags.filter(Boolean).length;
    activityArray[prevHour] = activeMinutes / 60; // Store as percentage (0 to 1)
    chrome.storage.local.set({ activity_array: activityArray });
    console.log(`[Activity] Hourly update: Hour ${prevHour}, Active minutes: ${activeMinutes}, Percentage: ${activityArray[prevHour]}`);
    // Reset for new hour
    minuteActiveFlags = new Array(60).fill(false);
    if (trackingEnabled) scheduleHourlyUpdate();
  }, millisTillNextHour);
}

function addActivityListeners() {
  if (listenersAdded) return;
  ["mousemove", "keydown", "scroll", "click"].forEach(evt =>
    window.addEventListener(evt, markActivity)
  );
  listenersAdded = true;
  scheduleHourlyUpdate();
  scheduleMidnightUpload();
  console.log("[Activity] Activity listeners added.");
}

function removeActivityListeners() {
  if (!listenersAdded) return;
  ["mousemove", "keydown", "scroll", "click"].forEach(evt =>
    window.removeEventListener(evt, markActivity)
  );
  listenersAdded = false;
  // Clear any pending timeouts
  if (hourlyTimeoutId) clearTimeout(hourlyTimeoutId);
  if (midnightTimeoutId) clearTimeout(midnightTimeoutId);
  hourlyTimeoutId = null;
  midnightTimeoutId = null;
  console.log("[Activity] Activity listeners removed.");
}

// Listen for tracking state changes from popup
if (chrome && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "start_tracking") {
      if (!trackingEnabled) {
        trackingEnabled = true;
        addActivityListeners();
        console.log("[Activity] Tracking enabled.");
      }
    } else if (msg.type === "stopTracking") {
      trackingEnabled = false;
      removeActivityListeners();
      console.log("[Activity] Tracking disabled.");
    }
  });
}

// At midnight, send activity array to background for upload
function scheduleMidnightUpload() {
  if (!trackingEnabled) return;
  const now = new Date();
  const millisTillMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0) - now;
  midnightTimeoutId = setTimeout(() => {
    try {
      if (!trackingEnabled) return;
      if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
        chrome.runtime.sendMessage({ type: "uploadActivity" });
        console.log("[Activity] Activity array sent for upload at midnight.");
      }
      if (trackingEnabled) scheduleMidnightUpload();
    } catch (err) {
      console.warn("[Activity] Could not send uploadActivity message:", err);
    }
  }, millisTillMidnight);
}

// Optionally, check chrome.storage.local for persisted tracking state on load
if (chrome && chrome.storage && chrome.storage.local) {
  chrome.storage.local.get("tracking_enabled", (result) => {
    if (result.tracking_enabled) {
      trackingEnabled = true;
      addActivityListeners();
      console.log("[Activity] Tracking resumed on load.");
    }
  });
}