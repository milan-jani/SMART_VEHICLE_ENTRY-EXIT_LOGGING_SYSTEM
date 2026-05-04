/**
 * Kiosk Form Logic - Final Production Version
 */

document.addEventListener('DOMContentLoaded', function() {
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
    startStandbyPolling();
    updateStandbyTime();
    setInterval(updateStandbyTime, 1000);
});

function updateStandbyTime() {
    const el = document.getElementById('current-time');
    if (el) {
        const now = new Date();
        el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
}

// --- Polling for Standby Mode ---
let pollingInterval;
function startStandbyPolling() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('plate')) return;

    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/vehicles?t=' + new Date().getTime());
            const data = await response.json();
            if (data.status === 'success' && data.vehicles && data.vehicles.length > 0) {
                const latest = data.vehicles[0];
                
                // 1. Check if it's pending
                const isPending = !latest.visitor_name || latest.visitor_name.trim() === "" || latest.visitor_name.toLowerCase() === "pending";
                
                // 2. Check if it's RECENT (within last 60 seconds)
                const entryTime = new Date(latest.in_time).getTime();
                const now = new Date().getTime();
                const isRecent = (now - entryTime) < 60000; // 60 seconds

                if (isPending && isRecent) {
                    console.log(`[TRIGGER] New detection: ${latest.vehicle_no}`);
                    clearInterval(pollingInterval);
                    window.location.replace(`/api/kiosk?plate=${latest.vehicle_no}`);
                }
            }
        } catch (err) { console.error("Poll Error:", err); }
    }, 3000);
}

// --- ID Capture & OCR ---
let currentCaptureSide = ''; 
let isCameraActive = false;
let videoStream = null;

function openCameraModal(side) {
    currentCaptureSide = side;
    document.getElementById('modal-title').textContent = side === 'front' ? 'Capture Front of ID' : 'Capture Back of ID';
    document.getElementById('camera-modal').classList.remove('hidden');
    initCamera();
}

function closeCameraModal() {
    document.getElementById('camera-modal').classList.add('hidden');
    stopCamera();
}

async function initCamera() {
    const video = document.getElementById('camera-video');
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        videoStream = stream;
        video.srcObject = stream;
        isCameraActive = true;
    } catch (err) { alert("Camera Error: " + err); }
}

function stopCamera() {
    if (videoStream) videoStream.getTracks().forEach(t => t.stop());
    isCameraActive = false;
}

let isCountingDown = false;

function takeSnapshot() {
    if (!isCameraActive || isCountingDown) return;
    
    isCountingDown = true;
    const btnSnap = document.getElementById('btn-snap');
    if (btnSnap) btnSnap.disabled = true;
    
    const counterEl = document.getElementById('camera-counter');
    let count = 3;
    
    if (counterEl) {
        counterEl.textContent = count;
        counterEl.classList.remove('hidden');
    }
    
    const countInterval = setInterval(() => {
        count--;
        if (count > 0) {
            if (counterEl) counterEl.textContent = count;
        } else {
            clearInterval(countInterval);
            if (counterEl) counterEl.classList.add('hidden');
            isCountingDown = false;
            if (btnSnap) btnSnap.disabled = false;
            executeSnapshot();
        }
    }, 1000);
}

function executeSnapshot() {
    if (!isCameraActive) return;
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(blob => {
        const file = new File([blob], 'id_capture.jpg', { type: 'image/jpeg' });
        uploadFileToAPI(file);
    }, 'image/jpeg', 0.9);
}

async function uploadFileToAPI(file) {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const resp = await fetch('/api/upload-id-card', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.status === 'success') {
            updateCaptureBox(currentCaptureSide, data.file_path);
            closeCameraModal();
            // START OCR PROCESS
            processOCR(data.file_path, currentCaptureSide);
        }
    } catch (err) { alert("Upload failed"); }
}

async function processOCR(filePath, side) {
    const ocrStatus = document.getElementById(`ocr-status-${side}`);
    if (ocrStatus) {
        ocrStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        ocrStatus.classList.remove('hidden');
    }
    
    try {
        const response = await fetch('/api/id-ocr', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ image_path: filePath, side: side })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            if (ocrStatus) ocrStatus.innerHTML = '<i class="fas fa-check"></i> Done';
            const d = result.data;
            if (d.name) document.getElementById('visitor_name').value = d.name;
            if (d.id_number) document.getElementById('id_number').value = d.id_number;
            if (d.dob) document.getElementById('dob').value = d.dob;
            if (d.address) document.getElementById('address').value = d.address;
        } else {
            if (ocrStatus) ocrStatus.innerHTML = '<i class="fas fa-times"></i> Scan Failed';
        }
    } catch (err) {
        if (ocrStatus) ocrStatus.innerHTML = '<i class="fas fa-times"></i> Error';
    }
}

function updateCaptureBox(side, filePath) {
    document.getElementById(`capture-${side}-box`).classList.add('has-image');
    document.getElementById(`${side}-preview-img`).src = `/${filePath}`;
    document.getElementById(`${side}-preview-img`).classList.remove('hidden');
    document.getElementById(`${side}-preview-container`).classList.add('hidden');
    document.getElementById(`id_card_${side}_path`).value = filePath;
}

// UI Helpers
function initChips() {
    ['purpose-chips', 'vehicle-type-chips', 'duration-chips'].forEach(id => {
        const group = document.getElementById(id);
        if (!group) return;
        const inputId = id.split('-')[0] + (id.includes('duration') ? '_expected' : '');
        const input = document.getElementById(id.replace('-chips', '').replace('duration', 'expected_duration'));
        group.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('click', () => {
                group.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                input.value = chip.dataset.value;
            });
        });
    });
}

function initIDTypeLogic() {
    const s = document.getElementById('id_type');
    if (s) s.addEventListener('change', function() {
        document.getElementById('id_number').value = '';
    });
}

function startInactivityTimer() {
    let t;
    const r = () => { clearTimeout(t); t = setTimeout(() => { if (window.location.search.includes('plate')) window.location.href='/api/kiosk'; }, 180000); };
    ['mousedown', 'mousemove', 'keypress'].forEach(e => document.addEventListener(e, r));
    r();
}

document.getElementById('kiosk-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const overlay = document.getElementById('status-overlay');
    overlay.classList.remove('hidden');
    try {
        const resp = await fetch('/api/kiosk', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(Object.fromEntries(new FormData(this).entries()))
        });
        if (resp.ok) {
            document.getElementById('loading-spinner').classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
            setTimeout(() => { window.location.href = '/api/kiosk'; }, 2000);
        } else { overlay.classList.add('hidden'); alert("Save failed"); }
    } catch (err) { overlay.classList.add('hidden'); }
});

// --- Virtual Numpad Logic ---
let currentTargetInputId = null;

function openNumpad(inputId) {
    currentTargetInputId = inputId;
    const targetInput = document.getElementById(inputId);
    const numpadDisplay = document.getElementById('numpad-display');
    numpadDisplay.value = targetInput.value;
    document.getElementById('numpad-overlay').classList.remove('hidden');
}

function closeNumpad() {
    document.getElementById('numpad-overlay').classList.add('hidden');
    currentTargetInputId = null;
}

function numpadPress(num) {
    const display = document.getElementById('numpad-display');
    // For phone numbers, limit to 10 digits
    if (currentTargetInputId === 'phone' && display.value.length >= 10) return;
    display.value += num;
}

function numpadBackspace() {
    const display = document.getElementById('numpad-display');
    display.value = display.value.slice(0, -1);
}

function numpadClear() {
    document.getElementById('numpad-display').value = '';
}

function numpadDone() {
    if (currentTargetInputId) {
        const targetInput = document.getElementById(currentTargetInputId);
        targetInput.value = document.getElementById('numpad-display').value;
        // Trigger input event
        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        if (currentTargetInputId === 'phone' && targetInput.value.length === 10) {
            targetInput.setCustomValidity('');
        }
    }
    closeNumpad();
}

// Support physical keyboard when Virtual Numpad is open
document.addEventListener('keydown', function(e) {
    if (!currentTargetInputId) return;
    if (e.key === 'Enter') {
        e.preventDefault();
        numpadDone();
    } else if (e.key === 'Escape') {
        closeNumpad();
    } else if (e.key === 'Backspace') {
        numpadBackspace();
    } else if (/^[0-9]$/.test(e.key)) {
        numpadPress(e.key);
    }
});
