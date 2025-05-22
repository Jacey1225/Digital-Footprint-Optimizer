document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("loginBtn");
  if (loginBtn) {
    loginBtn.addEventListener("click", () => {
      chrome.storage.local.get("user_id", (result) => {
        if (!result.user_id) {
          const id = crypto.randomUUID();
          console.log("User ID:", id);
          chrome.storage.local.set({ user_id: id }, () => {
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('dashboardPage').style.display = 'block';
          });
        } else {
          console.log("User ID:", result.user_id);
          document.getElementById('loginPage').style.display = 'none';
          document.getElementById('dashboardPage').style.display = 'block';
        }
      });
    });
  } 
});



document.getElementById('trackBtn').addEventListener('click', () => {
  // show login, hide dashboard
  document.getElementById('dashboardPage').style.display = 'none';
  document.getElementById('loginPage').style.display = 'none';
  document.getElementById('activityPage').style.display = 'block';
});
