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

// --- Staff Autocomplete System ---
function initStaffAutocomplete() {
    const input = document.getElementById('person_to_meet');
    const suggestionsBox = document.getElementById('staff-suggestions');
    const emailInput = document.getElementById('person_to_meet_email');
    const codeInput = document.getElementById('person_to_meet_code');
    
    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();
        
        if (query.length < 2) {
            suggestionsBox.classList.add('hidden');
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const resp = await fetch(`/api/staff-search?q=${encodeURIComponent(query)}`);
                const result = await resp.json();
                
                if (result.status === 'success' && result.data.length > 0) {
                    renderSuggestions(result.data);
                } else {
                    suggestionsBox.classList.add('hidden');
                }
            } catch (err) { console.error("Search Error:", err); }
        }, 300);
    });

    function renderSuggestions(staff) {
        suggestionsBox.innerHTML = '';
        staff.forEach(person => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `
                <div class="suggestion-name">${person.name}</div>
                <div class="suggestion-meta">
                    <span><i class="fas fa-building"></i> ${person.department}</span>
                    <span><i class="fas fa-map-marker-alt"></i> ${person.room_no || '-'}</span>
                    <span><i class="fas fa-id-badge"></i> ${person.emp_code}</span>
                </div>
            `;
            div.addEventListener('mousedown', (e) => {
                e.preventDefault();
                selectStaff(person);
            });
            suggestionsBox.appendChild(div);
        });
        suggestionsBox.classList.remove('hidden');
    }

    function selectStaff(person) {
        input.value = person.name;
        emailInput.value = person.email;
        codeInput.value = person.emp_code;
        
        // Auto-fill Flat/Room No field
        const flatInput = document.getElementById('flat_no');
        if (flatInput && person.room_no) {
            flatInput.value = person.room_no;
            // Highlight it briefly
            flatInput.style.backgroundColor = 'rgba(13, 148, 136, 0.1)';
            setTimeout(() => { flatInput.style.backgroundColor = ''; }, 1000);
        }

        suggestionsBox.classList.add('hidden');
        // Briefly highlight the input to show it's selected
        input.style.backgroundColor = 'rgba(13, 148, 136, 0.1)';
        setTimeout(() => { input.style.backgroundColor = ''; }, 500);
    }

    // Hide on click outside
    document.addEventListener('mousedown', (e) => {
        if (!input.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.classList.add('hidden');
        }
    });
}

// --- Virtual Keyboard & Numpad System ---
let currentFocusInput = null;
const keyboardContainer = document.getElementById('keyboard-container');
const keyboardKeys = document.getElementById('keyboard-keys');

const layouts = {
    numpad: [
        ['1', '2', '3'],
        ['4', '5', '6'],
        ['7', '8', '9'],
        ['Clear', '0', 'Back']
    ],
    qwerty: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Back'],
        ['Space', 'Done']
    ]
};

function initKeyboard() {
    const inputs = document.querySelectorAll('input[type="text"], input[type="tel"], textarea, input[type="hashtag"]');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            currentFocusInput = input;
            const type = (input.type === 'tel' || input.id === 'id_number') ? 'numpad' : 'qwerty';
            showKeyboard(type);
        });
    });

    // Close keyboard when clicking outside
    document.addEventListener('mousedown', (e) => {
        if (!keyboardContainer.contains(e.target) && !e.target.matches('input, textarea')) {
            hideKeyboard();
        }
    });
}

function showKeyboard(type) {
    keyboardKeys.innerHTML = '';
    keyboardKeys.className = type === 'numpad' ? 'numpad-container' : 'keyboard-grid';
    
    layouts[type].forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'keyboard-row';
        row.forEach(key => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'key';
            btn.textContent = key;
            
            if (key === 'Back') {
                btn.innerHTML = '<i class="fas fa-backspace"></i>';
                btn.classList.add('wide');
            } else if (key === 'Clear') {
                btn.classList.add('wide');
            } else if (key === 'Space') {
                btn.classList.add('space');
            } else if (key === 'Done') {
                btn.classList.add('done');
            }

            btn.addEventListener('mousedown', (e) => {
                e.preventDefault(); // Prevent focus loss
                handleKeyPress(key);
            });
            rowDiv.appendChild(btn);
        });
        keyboardKeys.appendChild(rowDiv);
    });

    keyboardContainer.style.display = 'flex';
    document.body.classList.add('keyboard-active');
    
    // Scroll input into view
    setTimeout(() => {
        currentFocusInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

function hideKeyboard() {
    keyboardContainer.style.display = 'none';
    document.body.classList.remove('keyboard-active');
    if (currentFocusInput) currentFocusInput.blur();
    currentFocusInput = null;
}

function handleKeyPress(key) {
    if (!currentFocusInput) return;

    const start = currentFocusInput.selectionStart;
    const end = currentFocusInput.selectionEnd;
    const value = currentFocusInput.value;

    if (key === 'Back') {
        currentFocusInput.value = value.slice(0, start === end ? start - 1 : start) + value.slice(end);
        currentFocusInput.setSelectionRange(start === end ? start - 1 : start, start === end ? start - 1 : start);
    } else if (key === 'Clear') {
        currentFocusInput.value = '';
    } else if (key === 'Space') {
        currentFocusInput.value = value.slice(0, start) + ' ' + value.slice(end);
        currentFocusInput.setSelectionRange(start + 1, start + 1);
    } else if (key === 'Done') {
        hideKeyboard();
    } else {
        // Limit phone to 10
        if (currentFocusInput.type === 'tel' && value.length >= 10) return;
        
        currentFocusInput.value = value.slice(0, start) + key + value.slice(end);
        currentFocusInput.setSelectionRange(start + 1, start + 1);
    }

    currentFocusInput.dispatchEvent(new Event('input', { bubbles: true }));
}

// Update DOMContentLoaded to include initKeyboard
document.addEventListener('DOMContentLoaded', function() {
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
    startStandbyPolling();
    updateStandbyTime();
    initKeyboard();
    initStaffAutocomplete();
    setInterval(updateStandbyTime, 1000);
});
