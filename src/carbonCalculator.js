let trackingHours = [];

async function fetchTrackingHours(userId) {
  try {
    const res = await fetch("http://localhost:8000/fetch-pattern", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId }),
    });

    const data = await res.json();
    trackingHours = data.pattern;
    console.log("✅ Got tracking hours:", trackingHours);
  } catch (err) {
    console.error("❌ Failed to fetch tracking hours", err);
  }
}

function isWithinTrackingHours(ranges) {
  const currentHour = new Date().getHours();
  return ranges.some(([start, end]) => currentHour >= start && currentHour < end);
}

// Call this once on extension load or login
fetchTrackingHours("YOUR_USER_ID");

// Later in your logic
document.addEventListener("click", () => {
  if (isWithinTrackingHours(trackingHours)) {
  ////something
    // Send data to backend
  } else {
    console.log("Outside tracking window");
  }
});
//need to add co2.js
