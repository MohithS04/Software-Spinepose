
// Real-Time Connection
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
let socket;
let isStreaming = false;
let isRecording = false;
let isCameraHidden = false;

function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = function () {
        console.log("Connected to Spine-AI Engine");
        const badge = document.getElementById('sys-status');
        if (badge) {
            badge.innerHTML = '<span class="status-dot" style="background:var(--accent-cyan); box-shadow: 0 0 8px var(--accent-cyan);"></span> System Online';
            badge.style.borderColor = 'var(--accent-cyan)';
        }
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);

        // Update Video Feed ONLY if Camera is NOT hidden
        if (!isCameraHidden) {
            if (data.image) updateScanView('scan-1', data.image);
            if (data.image_sagittal) updateScanView('scan-2', data.image_sagittal);
            if (data.image_coronal) updateScanView('scan-3', data.image_coronal);
            if (data.image_heatmap) updateScanView('scan-4', data.image_heatmap);
        }

        // Update Metrics
        if (data.metrics) {
            updateMetrics(data.metrics);
        }

        // Update Status
        if (data.status === 'recording' && !isRecording) {
            isRecording = true;
            updateRecordBtn();
        } else if (data.status !== 'recording' && isRecording) {
            isRecording = false;
            updateRecordBtn();
        }
    };

    socket.onclose = function () {
        console.log("Disconnected.");
        isStreaming = false;
        isRecording = false;
        updateControls();
        const badge = document.getElementById('sys-status');
        if (badge) {
            badge.innerHTML = '<span class="status-dot" style="background:var(--accent-red);"></span> Disconnected';
            badge.style.borderColor = 'var(--accent-red)';
        }
    };
}

function updateScanView(elementId, base64Image) {
    const el = document.getElementById(elementId);
    if (el) {
        el.style.backgroundImage = `url(data:image/jpeg;base64,${base64Image})`;
        el.style.opacity = '1';
        el.style.filter = 'none';
        el.innerHTML = ''; // Clear any placeholder text
    }
}

function updateMetrics(metrics) {
    // Helper for color coding
    const getStatusColor = (val, threshold, reverse = false) => {
        if (!val) return 'var(--accent-cyan)';
        if (reverse) return val > threshold ? 'var(--accent-cyan)' : 'var(--accent-red)';
        return val > threshold ? 'var(--accent-red)' : 'var(--accent-cyan)';
    };

    // Update Text Values
    const setVal = (id, val, unit = '°') => {
        const el = document.getElementById(id);
        if (el) el.innerText = val !== undefined && val !== null ? val.toFixed(1) + unit : '0' + unit;
    };

    setVal('val-cobb', metrics.cobb_angle);
    setVal('val-lumbar', metrics.lumbar_flexion);
    setVal('val-cervical', metrics.cervical_flexion);

    // Update Score Circle
    const score = metrics.health_score || 0;
    document.querySelector('.score-text').innerText = `${score}%`;
    const circle = document.querySelector('.c-val');
    // Circumference is ~377 (r=60)
    const offset = 377 - (377 * score / 100);
    circle.style.strokeDashoffset = offset;

    // Color circle based on score
    if (score < 70) circle.style.stroke = 'var(--accent-red)';
    else circle.style.stroke = 'var(--accent-cyan)';
}


// Patient Management
let currentPatient = null;

async function loadPatients() {
    try {
        const res = await fetch('/patients');
        const patients = await res.json();
        const sel = document.getElementById('patient-selector');

        // Clear existing options except first two
        while (sel.options.length > 2) {
            sel.remove(2);
        }

        patients.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.innerText = p.name;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to load patients", e);
    }
}

async function setPatient(val) {
    if (val === 'new') {
        const name = prompt("Enter Patient Name:");
        if (name) {
            const age = prompt("Enter Age:");
            const gender = prompt("Enter Gender (M/F):");

            const res = await fetch('/patients', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, age, gender })
            });
            const newP = await res.json();
            await loadPatients();
            document.getElementById('patient-selector').value = newP.id;
            updatePatientDisplay(newP);
        } else {
            document.getElementById('patient-selector').value = "";
        }
    } else if (val) {
        const res = await fetch('/patients');
        const patients = await res.json();
        const p = patients.find(x => x.id === val);
        updatePatientDisplay(p);
    } else {
        updatePatientDisplay(null);
    }
}

function updatePatientDisplay(p) {
    currentPatient = p;
    if (p) {
        document.getElementById('p-name').innerText = p.name;
        document.getElementById('p-id').innerText = p.id;
    } else {
        document.getElementById('p-name').innerText = "Guest User";
        document.getElementById('p-id').innerText = "---";
    }
}

// Medical Report Generation
async function generateReport() {
    if (!currentPatient) {
        alert("Please select a patient first.");
        return;
    }

    const note = prompt("Add clinical notes for this report:", "Routine checkup.");

    // In a real app, we would POST to /report endpoint.
    // For now, we simulate a report download.

    const reportContent = `
    SPINE AI - CLINICAL DIAGNOSTIC REPORT
    -------------------------------------
    Patient: ${currentPatient.name}
    ID: ${currentPatient.id}
    Date: ${new Date().toLocaleString()}
    Clinical Notes: ${note}
    
    METRICS SUMMARY:
    - Health Score: ${document.querySelector('.score-text').innerText}
    - Analysis Status: Completed
    
    DISCLAIMER: This is an AI-assisted tool. Not for medical diagnosis.
    `;

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Report_${currentPatient.name}_${Date.now()}.txt`;
    a.click();
}

// Initialize
loadPatients();

function toggleStream() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        connectWebSocket();
        setTimeout(() => {
            if (socket.readyState === WebSocket.OPEN) {
                sendStart();
            }
        }, 500);
    } else {
        if (isStreaming) {
            socket.send(JSON.stringify({ command: "stop" }));
            isStreaming = false;
        } else {
            sendStart();
        }
    }
    updateControls();
}

function sendStart() {
    socket.send(JSON.stringify({ command: "start" }));
    isStreaming = true;
    updateControls();
}

function updateControls() {
    const btn = document.getElementById('main-ctl');
    if (isStreaming) {
        btn.innerText = "STOP ANALYSIS";
        btn.style.boxShadow = "0 0 15px var(--accent-red)";
        btn.style.borderColor = "var(--accent-red)";
        btn.style.color = "var(--accent-red)";
    } else {
        btn.innerText = "START LIVE ANALYSIS";
        btn.style.boxShadow = "none";
        btn.style.borderColor = "var(--accent-cyan)";
        btn.style.color = "var(--accent-cyan)";
    }
}

function setMode(mode) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ command: "set_mode", value: mode }));
    }
    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    if (mode === 'medical') document.getElementById('btn-medical').classList.add('active');
    if (mode === 'sports') document.getElementById('btn-sports').classList.add('active');
}

function toggleRecord() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ command: "record_toggle" }));
    } else {
        alert("Connect to system first!");
    }
}

function updateRecordBtn() {
    const btn = document.getElementById('btn-record');
    if (isRecording) {
        btn.style.background = "var(--accent-red)";
        btn.style.color = "#fff";
        btn.classList.add("recording-pulse");
        btn.innerHTML = '<svg class="icon-fallback" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="10" height="10" fill="currentColor" style="margin-right:5px;"><path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512z"/></svg> REC ON';
    } else {
        btn.style.background = "";
        btn.style.color = "";
        btn.classList.remove("recording-pulse");
        btn.innerHTML = '<svg class="icon-fallback" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="10" height="10" fill="currentColor" style="margin-right:5px;"><path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512z"/></svg> REC';
    }
}

function setActivity(val) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ command: "set_activity", value: val }));
        console.log("Activity set to:", val);
    }
}

function toggleCameraVisibility() {
    isCameraHidden = !isCameraHidden;
    const btn = document.getElementById('btn-cam-toggle');
    const feed = document.getElementById('scan-1');

    if (isCameraHidden) {
        btn.classList.remove('active');
        btn.style.color = "var(--text-secondary)";
        feed.style.opacity = '0'; // Hide feed
    } else {
        btn.classList.add('active');
        btn.style.color = "var(--accent-cyan)";
        feed.style.opacity = '1'; // Show feed
    }
}

async function uploadFile(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const formData = new FormData();
        formData.append("file", file);

        // Pause Stream if Active
        if (isStreaming) {
            toggleStream(); // Stop stream to focus on file
        }

        // Show Loading
        const scan1 = document.getElementById('scan-1');
        scan1.style.opacity = '0.5';

        try {
            const response = await fetch('/analyze_file', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.image) {
                // Force show camera view if it was hidden
                if (isCameraHidden) toggleCameraVisibility();

                updateScanView('scan-1', data.image);
                if (data.image_sagittal) updateScanView('scan-2', data.image_sagittal);
                if (data.image_coronal) updateScanView('scan-3', data.image_coronal);
                if (data.image_heatmap) updateScanView('scan-4', data.image_heatmap);

                if (data.metrics) updateMetrics(data.metrics);

                if (data.report) {
                    const reportContainer = document.querySelector('.info-panel');
                    // Inject Report Text
                    const dateStr = new Date().toLocaleString();
                    const reportHTML = `
                        <div class="report-header">
                            <h2>AI Diagnostic Report</h2>
                            <p class="timestamp">${dateStr}</p>
                        </div>
                        <div class="patient-card" style="border-left: 2px solid var(--accent-cyan);">
                            <div class="p-row" style="color: #fff; font-size: 0.9rem; line-height: 1.4;">
                                <strong>IMPRESSION:</strong><br>
                                ${data.report.replace(/\n/g, '<br>')}
                            </div>
                        </div>
                    `;
                    // Insert after original header or replace part of it. 
                    // Let's prepend or replace the top section for visibility.
                    const existingHeader = reportContainer.querySelector('.report-header');
                    if (existingHeader) existingHeader.remove();

                    const existingPatient = reportContainer.querySelector('.patient-card');
                    if (existingPatient) existingPatient.remove();

                    reportContainer.insertAdjacentHTML('afterbegin', reportHTML);
                }

                alert("File Analyzed Successfully. Report Generated.");
            } else {
                alert("Analysis Failed");
            }

        } catch (error) {
            console.error("Error:", error);
            alert("Upload Error");
        }
    }
}

// Initial Connect
connectWebSocket();

function takeScreenshot() {
    const scan1 = document.getElementById('scan-1');
    const style = window.getComputedStyle(scan1);
    const bgImage = style.backgroundImage;

    // Extract base64 URL
    if (bgImage && bgImage.startsWith('url("data:image/jpeg;base64,')) {
        const url = bgImage.slice(5, -2); // Remove 'url("' and '")'

        // Create link
        const a = document.createElement('a');
        a.href = url;
        a.download = `spine_scan_${Date.now()}.jpg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // Visual Feedback
        const btn = document.getElementById('btn-screenshot');
        btn.style.color = 'var(--accent-green)';
        setTimeout(() => {
            btn.style.color = 'var(--text-secondary)';
        }, 500);
    } else {
        alert("No active feed to capture.");
    }
}

function updateClock() {
    const timeElement = document.querySelector('.timestamp');
    if (timeElement) {
        const now = new Date();
        const options = {
            weekday: 'short',
            // year: 'numeric', 
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            // second: '2-digit'
        };
        timeElement.innerText = now.toLocaleString('en-US', options).toUpperCase();

        // Dynamic Greeting
        const greetingEl = document.getElementById('greeting-msg');
        if (greetingEl) {
            const hr = now.getHours();
            let msg = "Welcome Back";
            if (hr < 12) msg = "Good Morning, Dr. User";
            else if (hr < 18) msg = "Good Afternoon, Dr. User";
            else msg = "Good Evening, Dr. User";
            greetingEl.innerText = msg;
        }
    }
}

// Start Clock immediately
setInterval(updateClock, 1000);
updateClock(); // Initial call
