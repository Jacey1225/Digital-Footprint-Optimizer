const activityArray = new Array(24).fill(0);
const hoursTouched = new Set();
function markActivity() {
    const now = new Date();
    const hour = now.getHours();

    activityArray[hour] += 5;
    hoursTouched.add(hour); 
}

['mousemove', 'keydown', 'scroll', 'click'].forEach(evt =>
    window.addEventListener(evt, markActivity)
  );

  function showActivity(){
    if (hoursTouched.size < 24) {
        alert(`not enough data yet`);
        return;
      }
    
   const resultArray =activityArray.map(seconds => Math.min(seconds / 3600, 1).toFixed(2))

  }