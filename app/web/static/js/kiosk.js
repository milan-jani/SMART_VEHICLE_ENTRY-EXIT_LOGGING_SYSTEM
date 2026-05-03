/**
 * Kiosk Form Logic - Complete Version (Polling + ID Capture)
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("[KIOSK] Initializing Complete Logic...");
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
    startStandbyPolling();
});

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
                const isPending = !latest.visitor_name || latest.visitor_name.trim() === "" || latest.visitor_name.toLowerCase() === "pending";
                if (isPending) {
                    clearInterval(pollingInterval);
                    window.location.replace(`/api/kiosk?plate=${latest.vehicle_no}`);
                }
            }
        } catch (err) { console.error("Poll Error:", err); }
    }, 3000);
}

// --- ID Capture Modal Logic ---
let currentCaptureSide = ''; 
let isCameraActive = false;
let videoStream = null;

function openCameraModal(side) {
    currentCaptureSide = side;
    const modal = document.getElementById('camera-modal');
    const modalTitle = document.getElementById('modal-title');
    modalTitle.textContent = side === 'front' ? 'Capture Front of ID' : 'Capture Back of ID';
    modal.classList.remove('hidden');
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
    } catch (err) {
        console.error("Camera Error:", err);
        alert("Camera not available. Please use 'Upload' fallback.");
    }
}

function stopCamera() {
    if (videoStream) videoStream.getTracks().forEach(t => t.stop());
    isCameraActive = false;
}

function takeSnapshot() {
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
        }
    } catch (err) { alert("Upload failed"); }
}

function updateCaptureBox(side, filePath) {
    document.getElementById(`capture-${side}-box`).classList.add('has-image');
    document.getElementById(`${side}-preview-img`).src = `/${filePath}`;
    document.getElementById(`${side}-preview-img`).classList.remove('hidden');
    document.getElementById(`${side}-preview-container`).classList.add('hidden');
    document.getElementById(`id_card_${side}_path`).value = filePath;
}

// --- Chip/Pill Selection ---
function initChips() {
    setupChipGroup('purpose-chips', 'purpose');
    setupChipGroup('vehicle-type-chips', 'vehicle_type');
    setupChipGroup('duration-chips', 'expected_duration');
}

function setupChipGroup(groupId, inputId) {
    const group = document.getElementById(groupId);
    if (!group) return;
    const input = document.getElementById(inputId);
    const chips = group.querySelectorAll('.chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            input.value = chip.dataset.value;
        });
    });
}

function initIDTypeLogic() {
    const idType = document.getElementById('id_type');
    if (!idType) return;
    idType.addEventListener('change', function() {
        const input = document.getElementById('id_number');
        input.value = '';
        if (this.value === 'aadhaar') input.placeholder = "12 Digit Aadhaar";
        else input.placeholder = "ID Number";
    });
}

function startInactivityTimer() {
    let timer;
    const reset = () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            if (new URLSearchParams(window.location.search).has('plate')) window.location.href = '/api/kiosk';
        }, 120000);
    };
    ['mousedown', 'mousemove', 'keypress'].forEach(e => document.addEventListener(e, reset));
    reset();
}

// Form Submit
document.getElementById('kiosk-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const statusOverlay = document.getElementById('status-overlay');
    statusOverlay.classList.remove('hidden');
    const data = Object.fromEntries(new FormData(this).entries());
    try {
        const resp = await fetch('/api/kiosk', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (resp.ok) {
            document.getElementById('loading-spinner').classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
            setTimeout(() => { window.location.href = '/api/kiosk'; }, 3000);
        } else {
            statusOverlay.classList.add('hidden');
            alert("Error saving data");
        }
    } catch (err) { statusOverlay.classList.add('hidden'); }
});
