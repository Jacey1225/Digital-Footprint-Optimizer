let activityArray = new Array(24).fill(0);

function markActivity() {
  const now = new Date();
  const hour = now.getHours();
  activityArray[hour] += 5;

  // Save current activityArray to storage
  const formatted = activityArray.map((s) => Math.min(s / 3600, 1).toFixed(2));
  chrome.storage.local.set({ activity_array: formatted });
}

chrome.storage.local.get("tracking_enabled", (result) => {
  if (result.tracking_enabled) {
    ["mousemove", "keydown", "scroll", "click"].forEach((evt) =>
      window.addEventListener(evt, markActivity)
    );
    console.log("[content.js] Activity tracking enabled in this tab.");
  }
});
