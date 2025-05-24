let id = "";

document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.addEventListener("click", () => {
      chrome.storage.local.get(["user_id", "has_tracked"], (result) => {
        if (!result.user_id) {
          id = crypto.randomUUID();
          chrome.storage.local.set({ user_id: id }, () => {
            document.getElementById("trackBtn").style.display = "block";
            document.getElementById("loginPage").style.display = "none";
            document.getElementById("dashboardPage").style.display = "block";
          });
        } else {
          id = result.user_id;
          const hasTracked = result.has_tracked || false;
          document.getElementById("trackBtn").style.display = hasTracked ? "none" : "block";
          document.getElementById("loginPage").style.display = "none";
          document.getElementById("dashboardPage").style.display = "block";
        }
      });
    });
  }
});

document.getElementById("trackBtn").addEventListener("click", () => {
  chrome.storage.local.set({ tracking_enabled: true });

  document.getElementById("dashboardPage").style.display = "none";
  document.getElementById("loginPage").style.display = "none";
  document.getElementById("activityPage").style.display = "block";

  chrome.storage.local.get("user_id", (res) => {
    const uuid = res.user_id;

    // Set user on backend
    fetch("http://localhost:5000/set-user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uuid: uuid }),
    });

    // Wait until midnight, then send the behavior data
    const now = new Date();
    const millisTillMidnight =
      new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0) - now;

    setTimeout(() => {
      chrome.storage.local.get("activity_array", (result) => {
        const activities = result.activity_array || new Array(24).fill("0.00");
        const dayOfWeek = new Date().toLocaleDateString("en-US", { weekday: "long" });

        fetch("http://localhost:5000/add-behavior", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            uuid: uuid,
            day: dayOfWeek,
            array: activities,
          }),
        })
          .then(() => {
            chrome.storage.local.set({ has_tracked: true });
            document.getElementById("trackBtn").style.display = "none";
          })
          .catch((err) => console.error("Add behavior error:", err));
      });
    }, millisTillMidnight);
  });
});
