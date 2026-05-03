/**
 * Kiosk Form Logic - Production Version
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("[KIOSK] Page Loaded. Initializing...");
    initChips();
    initIDTypeLogic();
    startInactivityTimer();
    
    // FORCE START POLLING
    startStandbyPolling();
});

// --- Polling for Standby Mode ---
let pollingInterval;

function startStandbyPolling() {
    const urlParams = new URLSearchParams(window.location.search);
    const hasPlate = urlParams.has('plate');
    
    // If we already have a plate, don't poll
    if (hasPlate) {
        console.log("[KIOSK] Plate already present in URL. Form mode active.");
        return;
    }

    console.log("[POLLING] Starting aggressive standby monitoring...");
    
    // Clear any existing interval
    if (pollingInterval) clearInterval(pollingInterval);

    pollingInterval = setInterval(async () => {
        try {
            // Add timestamp to prevent browser caching the API response
            const response = await fetch('/api/vehicles?t=' + new Date().getTime());
            const data = await response.json();
            
            if (data.status === 'success' && data.vehicles && data.vehicles.length > 0) {
                const latest = data.vehicles[0];
                
                // If visitor_name is null, empty, or "Pending", it's our target!
                const isPending = !latest.visitor_name || 
                                 latest.visitor_name.trim() === "" || 
                                 latest.visitor_name.toLowerCase() === "pending";

                if (isPending) {
                    console.log(`[REDIRECT] Found pending vehicle: ${latest.vehicle_no}. Flipping to form...`);
                    clearInterval(pollingInterval);
                    // Use replace to prevent "Back" button loop
                    window.location.replace(`/api/kiosk?plate=${latest.vehicle_no}`);
                }
            }
        } catch (err) {
            console.error("[POLLING ERROR]", err);
        }
    }, 3000);
}

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
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            hiddenInput.value = chip.dataset.value;
            hiddenInput.setCustomValidity('');
        });
    });
}

function updatePersons(change) {
    const input = document.getElementById('num_persons');
    let val = parseInt(input.value) || 1;
    val += change;
    const min = parseInt(input.min) || 1;
    const max = parseInt(input.max) || 10;
    if (val >= min && val <= max) input.value = val;
}

function initIDTypeLogic() {
    const idTypeSelect = document.getElementById('id_type');
    if (!idTypeSelect) return;
    
    const idNumberInput = document.getElementById('id_number');
    const backRequiredStar = document.getElementById('back-required-star');
    const validationMsg = document.getElementById('id_validation_msg');
    
    idTypeSelect.addEventListener('change', function() {
        const type = this.value;
        if (validationMsg) validationMsg.textContent = '';
        idNumberInput.value = '';
        
        switch(type) {
            case 'aadhaar':
                idNumberInput.placeholder = "e.g. 1234 5678 9012";
                idNumberInput.pattern = "^[2-9]{1}[0-9]{3}\\s[0-9]{4}\\s[0-9]{4}$|^[2-9]{1}[0-9]{11}$";
                idNumberInput.maxLength = 14; 
                if (backRequiredStar) backRequiredStar.style.display = 'inline';
                break;
            case 'pan':
                idNumberInput.placeholder = "e.g. ABCDE1234F";
                idNumberInput.pattern = "^[A-Z]{5}[0-9]{4}[A-Z]{1}$";
                idNumberInput.maxLength = 10;
                if (backRequiredStar) backRequiredStar.style.display = 'none';
                break;
            default:
                idNumberInput.placeholder = "Enter ID Document Number";
                idNumberInput.removeAttribute('pattern');
                if (backRequiredStar) backRequiredStar.style.display = 'none';
        }
    });
}

let inactivityTimeout;
function resetTimer() {
    clearTimeout(inactivityTimeout);
    inactivityTimeout = setTimeout(() => {
        // If on standby, don't redirect. Only redirect if on form.
        const hasPlate = new URLSearchParams(window.location.search).has('plate');
        if (hasPlate) window.location.href = '/api/kiosk';
    }, 180000); // 3 minutes
}

function startInactivityTimer() {
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(evt => 
        document.addEventListener(evt, resetTimer, true)
    );
}

// Simplified form submission for focus
const form = document.getElementById('kiosk-form');
if (form) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Basic validation
        if (!document.getElementById('purpose').value) { alert("Select Purpose"); return; }
        
        const statusOverlay = document.getElementById('status-overlay');
        statusOverlay.classList.remove('hidden');
        
        const formData = new FormData(form);
        const dataObj = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch('/api/kiosk', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(dataObj)
            });
            const result = await response.json();
            if (response.ok && result.status === 'success') {
                document.getElementById('loading-spinner').classList.add('hidden');
                document.getElementById('success-message').classList.remove('hidden');
                setTimeout(() => { window.location.href = '/api/kiosk'; }, 3000);
            } else {
                alert("Error: " + (result.detail || "Submission failed"));
                statusOverlay.classList.add('hidden');
            }
        } catch (err) {
            console.error(err);
            alert("Submission failed. Check connection.");
            statusOverlay.classList.add('hidden');
        }
    });
}
