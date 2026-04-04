/**
 * Kiosk Form Logic
 * Handles interactive elements, camera, file uploads, and AJAX submission.
 */

document.addEventListener('DOMContentLoaded', function() {
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
});

// --- Chip/Pill Selection Logic ---
function initChips() {
    setupChipGroup('purpose-chips', 'purpose');
    setupChipGroup('vehicle-type-chips', 'vehicle_type');
    setupChipGroup('duration-chips', 'expected_duration');
}

function setupChipGroup(groupId, inputId) {
    const group = document.getElementById(groupId);
    if (!group) return;
    
    const hiddenInput = document.getElementById(inputId);
    const chips = group.querySelectorAll('.chip');
    
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            // Remove active from all
            chips.forEach(c => c.classList.remove('active'));
            // Add active to clicked
            chip.classList.add('active');
            // Update hidden input
            hiddenInput.value = chip.dataset.value;
            // Clear validation error if any
            hiddenInput.setCustomValidity('');
        });
    });
}

// --- Number Stepper Logic ---
function updatePersons(change) {
    const input = document.getElementById('num_persons');
    let val = parseInt(input.value) || 1;
    val += change;
    
    const min = parseInt(input.min) || 1;
    const max = parseInt(input.max) || 10;
    
    if (val >= min && val <= max) {
        input.value = val;
    }
}

// --- ID Type Logic ---
function initIDTypeLogic() {
    const idTypeSelect = document.getElementById('id_type');
    const idNumberInput = document.getElementById('id_number');
    const backRequiredStar = document.getElementById('back-required-star');
    const validationMsg = document.getElementById('id_validation_msg');
    
    idTypeSelect.addEventListener('change', function() {
        const type = this.value;
        validationMsg.textContent = '';
        idNumberInput.value = '';
        
        switch(type) {
            case 'aadhaar':
                idNumberInput.placeholder = "e.g. 1234 5678 9012";
                idNumberInput.pattern = "^[2-9]{1}[0-9]{3}\\s[0-9]{4}\\s[0-9]{4}$|^[2-9]{1}[0-9]{11}$";
                idNumberInput.title = "12 digit Aadhaar number";
                // Max length format with spaces: 12 digits + 2 spaces = 14
                idNumberInput.maxLength = 14; 
                backRequiredStar.style.display = 'inline'; // Aadhaar back is required for address
                break;
            case 'pan':
                idNumberInput.placeholder = "e.g. ABCDE1234F";
                idNumberInput.pattern = "^[A-Z]{5}[0-9]{4}[A-Z]{1}$";
                idNumberInput.title = "10 character PAN number";
                idNumberInput.maxLength = 10;
                backRequiredStar.style.display = 'none';
                break;
            case 'dl':
                idNumberInput.placeholder = "e.g. MH1420110062821";
                idNumberInput.pattern = "^[A-Z]{2}[0-9]{2}\\s?[0-9]{11}$";
                idNumberInput.title = "Driving License number";
                idNumberInput.maxLength = 20;
                backRequiredStar.style.display = 'none';
                break;
            case 'voter':
                idNumberInput.placeholder = "e.g. ABC1234567";
                idNumberInput.pattern = "^[a-zA-Z]{3}[0-9]{7}$";
                idNumberInput.title = "10 character Voter ID (EPIC)";
                idNumberInput.maxLength = 10;
                backRequiredStar.style.display = 'none';
                break;
            case 'passport':
                idNumberInput.placeholder = "e.g. A1234567";
                idNumberInput.pattern = "^[A-PR-WYa-pr-wy][1-9]\\d\\s?\\d{4}[1-9]$";
                idNumberInput.title = "Indian Passport number";
                idNumberInput.maxLength = 9;
                backRequiredStar.style.display = 'none';
                break;
            default:
                idNumberInput.placeholder = "Enter ID Document Number";
                idNumberInput.removeAttribute('pattern');
                idNumberInput.removeAttribute('title');
                idNumberInput.removeAttribute('maxLength');
                backRequiredStar.style.display = 'none';
        }
        
        // Auto format while typing for Aadhaar or PAN
        idNumberInput.oninput = function() {
            let val = this.value;
            if(type === 'pan') {
                this.value = val.toUpperCase();
            } else if (type === 'aadhaar') {
                // Auto insert spaces
                val = val.replace(/\D/g, ''); // retain only digits
                if(val.length > 0) {
                    val = val.match(new RegExp('.{1,4}', 'g')).join(' ');
                }
                this.value = val;
            }
        };
    });
}


// --- Inactivity Timeout ---
let inactivityTimeout;
function resetTimer() {
    clearTimeout(inactivityTimeout);
    // 120 seconds timeout => redirect to dashboard
    inactivityTimeout = setTimeout(() => {
        window.location.href = '/api/dashboard';
    }, 120000); 
}

function startInactivityTimer() {
    // Reset timer on any user interaction
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(evt => 
        document.addEventListener(evt, resetTimer, true)
    );
    resetTimer();
}


// --- Camera & Upload Logic ---
let currentCaptureSide = ''; // 'front' or 'back'
let isCameraActive = false;
let videoStream = null;

const modal = document.getElementById('camera-modal');
const video = document.getElementById('camera-video');
const canvas = document.getElementById('camera-canvas');
const fileUpload = document.getElementById('file-upload');
const btnSnap = document.getElementById('btn-snap');
const btnUploadFile = document.getElementById('btn-upload-file');
const cameraError = document.getElementById('camera-error');
const modalTitle = document.getElementById('modal-title');

function openCameraModal(side) {
    currentCaptureSide = side;
    modalTitle.textContent = side === 'front' ? 'Capture Front of ID' : 'Capture Back of ID';
    
    modal.classList.remove('hidden');
    fileUpload.value = ''; // Reset file input
    
    // First setup buttons based on default assumptions
    btnSnap.classList.remove('hidden');
    btnUploadFile.classList.add('hidden');
    cameraError.classList.add('hidden');
    video.style.display = 'block';
    
    initCamera();
}

function closeCameraModal() {
    modal.classList.add('hidden');
    stopCamera();
}

async function initCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showCameraFallback();
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } // Prefer back camera on touch devices
        });
        
        videoStream = stream;
        video.srcObject = stream;
        isCameraActive = true;
        
        // Ensure buttons are correct
        btnSnap.classList.remove('hidden');
        btnUploadFile.classList.add('hidden');
        cameraError.classList.add('hidden');
        video.style.display = 'block';
        
    } catch (err) {
        console.error("Camera error:", err);
        showCameraFallback();
    }
}

function showCameraFallback() {
    isCameraActive = false;
    video.style.display = 'none';
    cameraError.classList.remove('hidden');
    btnSnap.classList.add('hidden');
    btnUploadFile.classList.remove('hidden');
}

function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    isCameraActive = false;
}

// When user selects a file from the fallback input
fileUpload.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        // If file selected, make sure upload button is visible
        btnSnap.classList.add('hidden');
        btnUploadFile.classList.remove('hidden');
    }
});

function takeSnapshot() {
    if (!isCameraActive) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to Blob and upload
    canvas.toBlob((blob) => {
        const file = new File([blob], `${currentCaptureSide}_capture.jpg`, { type: 'image/jpeg' });
        uploadFileToAPI(file);
    }, 'image/jpeg', 0.85);
}

function uploadSelectedFile() {
    if (fileUpload.files && fileUpload.files[0]) {
        uploadFileToAPI(fileUpload.files[0]);
    } else {
        alert("Please select a file first.");
    }
}

async function uploadFileToAPI(file) {
    // Show quick loading state on button
    const btn = isCameraActive ? btnSnap : btnUploadFile;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
    btn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload-id-card', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            updateCaptureBox(currentCaptureSide, data.file_path);
            closeCameraModal();
        } else {
            throw new Error(data.detail || "Upload failed");
        }
    } catch (err) {
        console.error("Upload Error:", err);
        alert("Failed to upload image. Please try again.");
    } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    }
}

function updateCaptureBox(side, filePath) {
    // Show preview and store path
    const box = document.getElementById(`capture-${side}-box`);
    const previewContainer = document.getElementById(`${side}-preview-container`);
    const img = document.getElementById(`${side}-preview-img`);
    const pathInput = document.getElementById(`id_card_${side}_path`);
    
    // Create object URL for immediate display (or could use API path if served)
    const timestamp = new Date().getTime(); // cache buster
    img.src = `/${filePath}?t=${timestamp}`; 
    img.classList.remove('hidden');
    
    previewContainer.classList.add('hidden');
    box.classList.add('has-image');
    
    pathInput.value = filePath;
}


// --- Form Submission Logic ---
const form = document.getElementById('kiosk-form');
const statusOverlay = document.getElementById('status-overlay');
const spinner = document.getElementById('loading-spinner');
const successMsg = document.getElementById('success-message');
const errorMsg = document.getElementById('error-message');
const errorText = document.getElementById('error-text');

form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Explicitly check custom hidden required fields
    if (!document.getElementById('purpose').value) {
        alert("Please select a Purpose of Visit");
        return;
    }
    if (!document.getElementById('vehicle_type').value) {
        alert("Please select a Vehicle Type");
        return;
    }
    if (!document.getElementById('id_card_front_path').value) {
        alert("Please capture the Front side of the ID card.");
        return;
    }
    
    const idType = document.getElementById('id_type').value;
    const backImageRequired = idType === 'aadhaar';
    
    if (backImageRequired && !document.getElementById('id_card_back_path').value) {
        alert("Back side of Aadhaar card is required to capture the address.");
        return;
    }
    
    // Show loading
    statusOverlay.classList.remove('hidden');
    spinner.classList.remove('hidden');
    successMsg.classList.add('hidden');
    errorMsg.classList.add('hidden');
    
    // Collect JSON data
    const formData = new FormData(form);
    const dataObj = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch('/api/kiosk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataObj)
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            // Show success
            spinner.classList.add('hidden');
            successMsg.classList.remove('hidden');
            
            // Redirect after 2 seconds
            setTimeout(() => {
                window.location.href = '/api/dashboard';
            }, 2000);
            
        } else {
            throw new Error(result.detail || result.message || "Unknown error occurred.");
        }
        
    } catch (err) {
        console.error("Submission Error:", err);
        spinner.classList.add('hidden');
        errorMsg.classList.remove('hidden');
        errorText.textContent = err.message;
    }
});

function closeStatusOverlay() {
    statusOverlay.classList.add('hidden');
}
