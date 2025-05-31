chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "showAlternatives") {
    chrome.storage.local.get("alternatives", (res) => {
      if (res.alternatives && Array.isArray(res.alternatives)) {
        showSuggestions(res.alternatives);
      }
    });
  }
});

// Function to display suggestions in the popup
function showSuggestions(alternatives) {
  $(".successful_login").removeClass("hide");
  const $list = $("#suggestionsList");
  $list.empty();
  alternatives.forEach(suggestion => {
    if (suggestion) {
      $list.append(`<li>${suggestion}</li>`);
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