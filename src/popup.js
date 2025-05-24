let id = "";
let activities = [];

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
  const activityArray = new Array(24).fill(0);
  const hoursTouched = new Set();

  function markActivity() {
    const now = new Date();
    const hour = now.getHours();
    activityArray[hour] += 5;
    hoursTouched.add(hour);
  }

  ["mousemove", "keydown", "scroll", "click"].forEach((evt) =>
    window.addEventListener(evt, markActivity)
  );

  function showActivity() {
    return activityArray.map((seconds) => Math.min(seconds / 3600, 1).toFixed(2));
  }

  document.getElementById("dashboardPage").style.display = "none";
  document.getElementById("loginPage").style.display = "none";
  document.getElementById("activityPage").style.display = "block";

  //Send to /set-user
  fetch("http://localhost:5000/set-user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ uuid: id }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("Set user response:", data);
    })
    .catch((err) => console.error("Set user error:", err));

  // ⏱ Wait till 12AM and send /add-behavior
  const now = new Date();
  const millisTillMidnight =
    new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0) - now;

  setTimeout(() => {
    activities = showActivity();
    const dayOfWeek = new Date().toLocaleDateString("en-US", { weekday: "long" });

    fetch("http://localhost:5000/add-behavior", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        uuid: id,
        day: dayOfWeek,
        array: activities,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("Add behavior response:", data);
        chrome.storage.local.set({ has_tracked: true }); // Mark that user has tracked
        document.getElementById("trackBtn").style.display = "none";
      })
      .catch((err) => console.error("Add behavior error:", err));
  }, millisTillMidnight);
});
