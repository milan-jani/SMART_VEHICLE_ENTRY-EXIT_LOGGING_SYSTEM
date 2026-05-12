/**
 * Kiosk Form Logic - Integrated Version
 * Hybrid Keyboard, Staff Autocomplete, and Smooth Animations
 */

document.addEventListener('DOMContentLoaded', function() {
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
    startStandbyPolling();
    updateStandbyTime();
    setInterval(updateStandbyTime, 1000);
    
    // Init Virtual Keyboard for all text/tel inputs
    initVirtualKeyboard();
    
    // Init Staff Autocomplete
    initStaffAutocomplete();
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
            const response = await fetch('/api/kiosk-status?t=' + new Date().getTime());
            const data = await response.json();
            if (data.status === 'busy' && data.vehicle_no) {
                console.log(`[TRIGGER] New detection: ${data.vehicle_no}`);
                clearInterval(pollingInterval);
                window.location.replace(`/api/kiosk?plate=${data.vehicle_no}`);
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

function takeSnapshot() {
    if (!isCameraActive) return;
    
    // START 3 SECOND COUNTDOWN
    const videoContainer = document.querySelector('.video-container');
    const template = document.getElementById('counter-template');
    const counter = template.content.cloneNode(true).querySelector('.camera-counter');
    videoContainer.appendChild(counter);

    let count = 3;
    counter.textContent = count;
    
    const interval = setInterval(() => {
        count--;
        if (count > 0) {
            counter.textContent = count;
        } else {
            clearInterval(interval);
            counter.remove();
            performCapture();
        }
    }, 1000);
}

function performCapture() {
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

// --- Hybrid Virtual Keyboard ---
let currentActiveInput = null;

const layouts = {
    qwerty: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'BACKSPACE'],
        ['SPACE', 'DONE']
    ],
    numpad: [
        ['1', '2', '3'],
        ['4', '5', '6'],
        ['7', '8', '9'],
        ['CLEAR', '0', 'BACKSPACE'],
        ['DONE']
    ]
};

function initVirtualKeyboard() {
    const inputs = document.querySelectorAll('input[type="text"], input[type="tel"], textarea');
    inputs.forEach(input => {
        input.addEventListener('click', (e) => {
            // Don't open for hidden inputs
            if (input.type === 'hidden') return;
            openKeyboard(input);
        });
        // Prevent physical keyboard on mobile if needed
        input.setAttribute('inputmode', 'none');
    });
}

function openKeyboard(input) {
    currentActiveInput = input;
    const keyboard = document.getElementById('virtual-keyboard');
    const keysContainer = document.getElementById('keyboard-keys');
    const title = document.getElementById('keyboard-title');
    
    // Choose layout
    const isPhone = input.type === 'tel' || input.id === 'phone';
    const layoutType = isPhone ? 'numpad' : 'qwerty';
    
    title.textContent = isPhone ? 'Numeric Entry' : 'Alpha-Numeric Entry';
    keysContainer.className = 'keys-grid ' + layoutType;
    
    renderKeys(layoutType);
    keyboard.classList.remove('hidden');
    
    // Highlight input
    document.querySelectorAll('.input-wrapper input, .input-wrapper textarea').forEach(el => el.classList.remove('keyboard-active'));
    input.classList.add('keyboard-active');
}

function closeKeyboard() {
    document.getElementById('virtual-keyboard').classList.add('hidden');
    if (currentActiveInput) currentActiveInput.classList.remove('keyboard-active');
}

function renderKeys(layoutType) {
    const container = document.getElementById('keyboard-keys');
    container.innerHTML = '';
    
    layouts[layoutType].forEach(row => {
        const rowEl = document.createElement('div');
        rowEl.className = 'keyboard-row';
        
        row.forEach(key => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'key';
            btn.textContent = key;
            
            if (key === 'BACKSPACE') {
                btn.innerHTML = '<i class="fas fa-backspace"></i>';
                btn.classList.add('backspace');
                btn.onclick = () => handleKeyPress('BACKSPACE');
            } else if (key === 'SPACE') {
                btn.textContent = 'SPACE';
                btn.classList.add('extra-wide');
                btn.onclick = () => handleKeyPress(' ');
            } else if (key === 'DONE') {
                btn.classList.add('done', 'wide');
                btn.onclick = () => closeKeyboard();
            } else if (key === 'CLEAR') {
                btn.classList.add('special');
                btn.onclick = () => { if(currentActiveInput) currentActiveInput.value = ''; };
            } else {
                btn.onclick = () => handleKeyPress(key);
            }
            
            rowEl.appendChild(btn);
        });
        container.appendChild(rowEl);
    });
}

function handleKeyPress(key) {
    if (!currentActiveInput) return;
    
    const val = currentActiveInput.value;
    if (key === 'BACKSPACE') {
        currentActiveInput.value = val.slice(0, -1);
    } else {
        currentActiveInput.value += key;
    }
    
    // Trigger input event for listeners
    currentActiveInput.dispatchEvent(new Event('input', { bubbles: true }));
}

// --- Staff Autocomplete ---
function initStaffAutocomplete() {
    const staffInput = document.getElementById('person_to_meet');
    const suggestionsBox = document.getElementById('staff-suggestions');
    
    if (!staffInput) return;
    
    staffInput.addEventListener('input', async (e) => {
        const query = e.target.value;
        if (query.length < 2) {
            suggestionsBox.classList.add('hidden');
            return;
        }
        
        try {
            const resp = await fetch(`/api/staff-search?q=${encodeURIComponent(query)}`);
            const results = await resp.json();
            
            if (results.length > 0) {
                renderSuggestions(results);
            } else {
                suggestionsBox.classList.add('hidden');
            }
        } catch (err) { console.error("Search error:", err); }
    });
    
    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!staffInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.classList.add('hidden');
        }
    });
}

function renderSuggestions(staffList) {
    const box = document.getElementById('staff-suggestions');
    box.innerHTML = '';
    
    staffList.forEach(staff => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `
            <span class="suggestion-name">${staff.name}</span>
            <span class="suggestion-dept">${staff.department} | ${staff.room_no}</span>
        `;
        item.onclick = () => selectStaff(staff);
        box.appendChild(item);
    });
    
    box.classList.remove('hidden');
}

function selectStaff(staff) {
    document.getElementById('person_to_meet').value = staff.name;
    document.getElementById('person_to_meet_email').value = staff.email;
    document.getElementById('person_to_meet_code').value = staff.emp_code;
    
    // Auto-fill Room/Flat No
    const flatInput = document.getElementById('flat_no');
    if (flatInput && staff.room_no) {
        flatInput.value = staff.room_no;
        flatInput.classList.add('highlight-fill');
        setTimeout(() => flatInput.classList.remove('highlight-fill'), 1500);
    }
    
    document.getElementById('staff-suggestions').classList.add('hidden');
}

// UI Helpers
function initChips() {
    ['purpose-chips', 'vehicle-type-chips', 'duration-chips'].forEach(id => {
        const group = document.getElementById(id);
        if (!group) return;
        const inputId = id.includes('purpose') ? 'purpose' : 
                       (id.includes('vehicle') ? 'vehicle_type' : 'expected_duration');
        const input = document.getElementById(inputId);
        
        group.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('click', () => {
                group.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                if (input) input.value = chip.dataset.value;
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

function updatePersons(delta) {
    const input = document.getElementById('num_persons');
    let val = parseInt(input.value) || 1;
    val = Math.max(1, Math.min(10, val + delta));
    input.value = val;
}

function startInactivityTimer() {
    let t;
    const r = () => { 
        clearTimeout(t); 
        t = setTimeout(() => { 
            if (window.location.search.includes('plate')) {
                window.location.href='/api/kiosk'; 
            }
        }, 180000); 
    };
    ['mousedown', 'mousemove', 'keypress'].forEach(e => document.addEventListener(e, r));
    r();
}

document.getElementById('kiosk-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const overlay = document.getElementById('status-overlay');
    overlay.classList.remove('hidden');
    
    try {
        const formData = new FormData(this);
        const payload = Object.fromEntries(formData.entries());
        
        const resp = await fetch('/api/kiosk', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (resp.ok) {
            document.getElementById('loading-spinner').classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
            setTimeout(() => { window.location.href = '/api/kiosk'; }, 2000);
        } else { 
            overlay.classList.add('hidden'); 
            const errData = await resp.json();
            alert("Save failed: " + (errData.detail || "Unknown error")); 
        }
    } catch (err) { 
        overlay.classList.add('hidden'); 
        alert("Connection error");
    }
});
