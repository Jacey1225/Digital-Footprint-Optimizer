const canvas = document.getElementById("pieChart");
const ctx = canvas.getContext("2d");
const tooltip = document.getElementById("tooltip");

let data = [];
let slices = [];
let total = 0;
let maxRadius = 150;
let currentRadius = 0;
let animationFrame;

function startAnimation() {
    cancelAnimationFrame(animationFrame);
    currentRadius = 0;

    try {
    data = JSON.parse(document.getElementById("jsonInput").value);
    } catch (e) {
    alert("Invalid JSON data!");
    return;
    }

    total = data.reduce((sum, item) => sum + item.value, 0);
    slices = computeAngles(data);
    animatePie();
}

function computeAngles(data) {
    let startAngle = -0.5 * Math.PI;
    return data.map(item => {
    const angle = (item.value / total) * 2 * Math.PI;
    const slice = {
        ...item,
        startAngle,
        endAngle: startAngle + angle
    };
    startAngle += angle;
    return slice;
    });
}

function animatePie() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Draw slices
    slices.forEach(slice => {
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.fillStyle = slice.color;
    ctx.arc(centerX, centerY, currentRadius, slice.startAngle, slice.endAngle);
    ctx.closePath();
    ctx.fill();
    });

    // After animation, draw labels and percentages
    if (currentRadius >= maxRadius) {
    drawLabels(centerX, centerY);
    }

    if (currentRadius < maxRadius) {
    currentRadius += 5;
    animationFrame = requestAnimationFrame(animatePie);
    } else {
    currentRadius = maxRadius;
    }
}

function drawLabels(cx, cy) {
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    slices.forEach(slice => {
    const midAngle = (slice.startAngle + slice.endAngle) / 2;

    // Label position
    const labelRadius = maxRadius * 0.6;
    const x = cx + Math.cos(midAngle) * labelRadius;
    const y = cy + Math.sin(midAngle) * labelRadius;

    // Percentage position (slightly below label)
    const percent = ((slice.value / total) * 100).toFixed(1);
    const yPercent = y + 18; // 18px below label

    // Label
    ctx.fillStyle = "black";
    ctx.font = "bold 14px Poppins";
    ctx.fillText(slice.label, x, y);

    // Percentage
    ctx.fillStyle = "black";
    ctx.font = "12px Poppins";
    ctx.fillText(`${percent}%`, x, yPercent);
    });
}

// Tooltip on hover
canvas.addEventListener("mousemove", function (event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const dx = x - centerX;
    const dy = y - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance > currentRadius) {
    tooltip.style.display = "none";
    return;
    }

    let angle = Math.atan2(dy, dx);
    if (angle < -0.5 * Math.PI) angle += 2 * Math.PI;

    for (let slice of slices) {
    if (angle >= slice.startAngle && angle < slice.endAngle) {
        const percent = ((slice.value / total) * 100).toFixed(1);
        tooltip.innerText = `${slice.label}: ${percent}%`;
        tooltip.style.left = event.pageX + 10 + "px";
        tooltip.style.top = event.pageY + 10 + "px";
        tooltip.style.display = "block";
        return;
    }
    }

    tooltip.style.display = "none";
});

canvas.addEventListener("mouseleave", () => {
    tooltip.style.display = "none";
});

// Animate on scroll into view
const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
    if (entry.isIntersecting) {
        startAnimation();
        observer.unobserve(entry.target);
    }
    });
}, {
    threshold: 0.5
});

observer.observe(canvas);



// Animate on scroll into view
// const observer = new IntersectionObserver((entries, observer) => {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             startAnimation(); // 👈 This starts the chart animation
//             observer.unobserve(entry.target); // Stop observing after first trigger
//         }
//     });
// }, {
//     threshold: 0.5 // 👈 Trigger when 50% of the canvas is visible in the viewport
// });

// observer.observe(canvas); // 👈 Start observing the canvas element
