/**
 * Fixed Dashboard JavaScript - Production Version
 */
const API_BASE = '/api';
let allVehicles = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadDashboard();
    loadWorkers(); // Load workers as well
    setInterval(loadDashboard, 5000); // Auto refresh every 5s
    setInterval(loadWorkers, 10000); // Workers refresh less often
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.getElementById('btn-' + tabId).classList.add('active');
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') document.body.classList.add('dark-mode');
}

async function loadDashboard() {
    try {
        const vResp = await fetch(`${API_BASE}/vehicles?t=${new Date().getTime()}`);
        const vData = await vResp.json();
        
        if (vData.status === 'success') {
            allVehicles = vData.vehicles;
            updateVehiclesTable(allVehicles);
            
            // Check for new visitor
            if (allVehicles.length > 0) {
                const latest = allVehicles[0];
                const isNew = !latest.visitor_name || latest.visitor_name === "" || latest.visitor_name.toLowerCase() === "pending";
                if (isNew) showVisitorAlert(latest.vehicle_no);
                else hideVisitorAlert();
            }
        }

        const sResp = await fetch(`${API_BASE}/stats`);
        const sData = await sResp.json();
        if (sData.status === 'success') updateStatistics(sData.statistics);
        
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString('en-IN');
    } catch (e) { console.error("Load Error:", e); }
}

function updateStatistics(stats) {
    document.getElementById('total-entries').textContent = stats.total_entries || 0;
    document.getElementById('open-entries').textContent = stats.open_entries || 0;
    document.getElementById('closed-entries').textContent = stats.closed_entries || 0;
    document.getElementById('unique-vehicles').textContent = stats.unique_vehicles || 0;
}

function updateVehiclesTable(vehicles) {
    const tbody = document.getElementById('vehicles-tbody');
    if (!tbody) return;
    
    if (vehicles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9">No vehicles logged yet.</td></tr>';
        return;
    }

    tbody.innerHTML = vehicles.map((v, i) => `
        <tr class="clickable-row">
            <td><strong>${v.vehicle_no}</strong></td>
            <td>${v.visitor_type || 'Guest'}</td>
            <td>${v.visitor_name || '-'}</td>
            <td>${v.phone || '-'}</td>
            <td>${v.purpose || '-'}</td>
            <td>${v.in_time}</td>
            <td>${v.out_time ? v.out_time : '<span class="status-badge status-in">Inside</span>'}</td>
            <td>
                ${v.status === 'inside' ? '<span class="status-badge status-in"><i class="fas fa-sign-in-alt"></i> Inside</span>' : '<span class="status-badge status-out"><i class="fas fa-sign-out-alt"></i> Exited</span>'}
            </td>
            <td style="text-align: center;">
                <div style="display: flex; gap: 8px; justify-content: center;">
                    <button onclick="openVisitorDetail(${i})" class="btn-icon" title="View Details" style="color: var(--primary-color); background: none; border: none; cursor: pointer;">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button onclick="deleteVisit(${v.id})" class="btn-icon" title="Delete Entry" style="color: var(--danger-color); background: none; border: none; cursor: pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function deleteVisit(visitId) {
    if (!confirm("Are you sure you want to delete this entry?")) return;
    try {
        const resp = await fetch(`${API_BASE}/delete-visit/${visitId}`, { method: 'DELETE' });
        if (resp.ok) loadDashboard();
        else alert("Failed to delete entry");
    } catch (e) { alert("Error deleting entry"); }
}

function openVisitorDetail(index) {
    const v = allVehicles[index];
    if (!v) return;

    document.getElementById('vdetail-plate').textContent = v.vehicle_no;
    document.getElementById('vdetail-type').textContent = v.visitor_type;
    document.getElementById('vdetail-name').textContent = v.visitor_name || '-';
    document.getElementById('vdetail-phone').textContent = v.phone || '-';
    document.getElementById('vdetail-company').textContent = v.company || '-';
    document.getElementById('vdetail-dob').textContent = v.dob || '-';
    document.getElementById('vdetail-idtype').textContent = v.id_type || '-';
    document.getElementById('vdetail-idno').textContent = v.id_number || '-';
    document.getElementById('vdetail-street').textContent = v.address_street || '-';
    document.getElementById('vdetail-city').textContent = v.address_city || '-';
    document.getElementById('vdetail-state').textContent = v.address_state || '-';
    document.getElementById('vdetail-purpose').textContent = v.purpose || '-';
    document.getElementById('vdetail-meet').textContent = v.person_to_meet || '-';
    document.getElementById('vdetail-flat').textContent = v.flat_no || '-';
    document.getElementById('vdetail-persons').textContent = v.num_persons || '1';
    document.getElementById('vdetail-exp-duration').textContent = v.expected_duration || '-';
    document.getElementById('vdetail-remarks').textContent = v.remarks || '-';
    document.getElementById('vdetail-in').textContent = v.in_time;
    document.getElementById('vdetail-out').textContent = v.out_time || '-';
    
    // Status Badge
    const statusEl = document.getElementById('vdetail-status');
    statusEl.innerHTML = v.status === 'inside' ? 
        '<span class="status-badge status-in">Inside</span>' : 
        '<span class="status-badge status-out">Exited</span>';

    // Images
    updateDetailImage('vdetail-vehicle-img', v.vehicle_image_path);
    updateDetailImage('vdetail-idfront-img', v.id_card_front_path);
    updateDetailImage('vdetail-idback-img', v.id_card_back_path);

    document.getElementById('visitor-detail-modal').classList.add('show');
}

async function loadWorkers() {
    try {
        const resp = await fetch(`${API_BASE}/workers?t=${new Date().getTime()}`);
        const data = await resp.json();
        if (data.status === 'success') {
            updateWorkersTable(data.workers);
        }
    } catch (e) { console.error("Worker Load Error:", e); }
}

function updateWorkersTable(workers) {
    const tbody = document.getElementById('workers-tbody');
    if (!tbody) return;
    
    if (workers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No authorized workers added yet.</td></tr>';
        return;
    }

    tbody.innerHTML = workers.map(w => `
        <tr>
            <td><strong>${w.vehicle_no}</strong></td>
            <td>${w.user_name}</td>
            <td>${w.phone || '-'}</td>
            <td>${w.flat_no || '-'}</td>
            <td>${w.created_at || '-'}</td>
            <td>
                <button onclick="deleteWorker('${w.vehicle_no}')" class="btn-danger">
                    <i class="fas fa-user-minus"></i> Remove
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteWorker(plate) {
    if (!confirm(`Remove ${plate} from authorized workers?`)) return;
    try {
        const resp = await fetch(`${API_BASE}/delete-worker/${plate}`, { method: 'DELETE' });
        if (resp.ok) loadWorkers();
    } catch (e) { alert("Error removing worker"); }
}

async function submitNewWorker() {
    const data = {
        vehicle_no: document.getElementById('new-worker-plate').value,
        name: document.getElementById('new-worker-name').value,
        phone: document.getElementById('new-worker-phone').value,
        department: document.getElementById('new-worker-dept').value
    };
    
    if (!data.vehicle_no || !data.name) {
        alert("Plate and Name are required");
        return;
    }

    try {
        const resp = await fetch(`${API_BASE}/add-worker`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (resp.ok) {
            closeAddWorkerModal();
            loadWorkers();
        }
    } catch (e) { alert("Error adding worker"); }
}

function openAddWorkerModal() { document.getElementById('add-worker-modal').classList.add('show'); }
function closeAddWorkerModal() { document.getElementById('add-worker-modal').classList.remove('show'); }

function updateDetailImage(elId, path) {
    const img = document.getElementById(elId);
    const na = document.getElementById(elId + '-na');
    if (path) {
        img.src = `/${path}`;
        img.classList.remove('hidden');
        if (na) na.classList.add('hidden');
    } else {
        img.classList.add('hidden');
        if (na) na.classList.remove('hidden');
    }
}

function closeVisitorDetail() {
    document.getElementById('visitor-detail-modal').classList.remove('show');
}

function showVisitorAlert(plate) {
    let alertBanner = document.getElementById('visitor-alert-banner');
    if (!alertBanner) {
        alertBanner = document.createElement('div');
        alertBanner.id = 'visitor-alert-banner';
        alertBanner.className = 'visitor-alert';
        document.body.appendChild(alertBanner);
    }
    alertBanner.innerHTML = `
        <div class="alert-header"><i class="fas fa-bell"></i> New Visitor!</div>
        <div class="alert-body">Vehicle <b>${plate}</b> is at the gate.</div>
        <div style="display: flex; gap: 8px; margin-top: 5px;">
            <a href="/api/kiosk?plate=${plate}" class="btn-alert">Open Form</a>
            <button onclick="hideVisitorAlert()" class="btn-alert" style="background: #64748b;">Dismiss</button>
        </div>
    `;
    alertBanner.style.display = 'flex';
}

function hideVisitorAlert() {
    const banner = document.getElementById('visitor-alert-banner');
    if (banner) banner.style.display = 'none';
}

// Add CSS for alerts dynamically
const style = document.createElement('style');
style.textContent = `
    .visitor-alert {
        position: fixed; top: 20px; right: 20px; background: white; padding: 20px; 
        border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); z-index: 2000;
        display: none; flex-direction: column; gap: 12px; border-left: 8px solid #10b981;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
    .alert-header { font-weight: 700; color: #1e293b; font-size: 1.1rem; }
    .btn-alert { background: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 600; cursor: pointer; border: none; }
`;
document.head.appendChild(style);
