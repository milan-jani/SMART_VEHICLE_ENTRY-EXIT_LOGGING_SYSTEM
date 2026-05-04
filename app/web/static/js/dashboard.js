/**
 * Fixed Dashboard JavaScript - Full Production Version
 * Includes: Vehicle monitoring, stats, worker management, and detail modals.
 */
const API_BASE = '/api';
let allVehicles = [];
let allWorkers = []; // For the workers tab

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadDashboard();
    setInterval(loadDashboard, 5000); // Auto refresh every 5s
});

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') document.body.classList.add('dark-mode');
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

async function loadDashboard() {
    try {
        const vResp = await fetch(`${API_BASE}/vehicles?t=${new Date().getTime()}`);
        if (!vResp.ok) throw new Error(`HTTP Error: ${vResp.status}`);
        const vData = await vResp.json();
        
        if (vData.status === 'success') {
            allVehicles = vData.vehicles;
            updateVehiclesTable(allVehicles);
            
            // Check for new visitor
            if (allVehicles.length > 0) {
                const latest = allVehicles[0];
                const isNew = !latest.visitor_name || latest.visitor_name === "" || latest.visitor_name.toLowerCase() === "pending";
                // Only show alert for pending visitors currently 'inside'
                if (isNew && latest.status === 'inside') showVisitorAlert(latest.vehicle_no);
                else hideVisitorAlert();
            }
        }

        const sResp = await fetch(`${API_BASE}/stats`);
        if (sResp.ok) {
            const sData = await sResp.json();
            if (sData.status === 'success') updateStatistics(sData.statistics);
        }
        
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString('en-IN');
    } catch (e) { 
        console.error("Load Error:", e);
        const tbody = document.getElementById('vehicles-tbody');
        if (tbody && tbody.innerHTML.includes('Loading data...')) {
            tbody.innerHTML = `<tr><td colspan="9" style="color:var(--danger-color);">Error loading data: ${e.message}. Please restart backend.</td></tr>`;
        }
    }
}

function updateStatistics(stats) {
    if (!document.getElementById('total-entries')) return;
    document.getElementById('total-entries').textContent = stats.total_entries || 0;
    document.getElementById('open-entries').textContent = stats.currently_inside || 0;
    
    // Calculate exited correctly
    const exited = (stats.total_entries || 0) - (stats.currently_inside || 0);
    document.getElementById('closed-entries').textContent = exited;
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
        <tr onclick="openVisitorDetail(${i})" class="clickable-row">
            <td><strong>${v.vehicle_no}</strong></td>
            <td>${v.visitor_type || 'Guest'}</td>
            <td>${v.visitor_name || '-'}</td>
            <td>${v.phone || '-'}</td>
            <td>${v.purpose || '-'}</td>
            <td>${v.in_time}</td>
            <td>${v.out_time ? v.out_time : '<span class="status-badge status-in">Inside</span>'}</td>
            <td>${v.status === 'inside' ? '<span class="status-badge status-in">Inside</span>' : '<span class="status-badge status-out">Exited</span>'}</td>
            <td style="text-align:center;">
                <button class="btn-danger" onclick="deleteVisit(${v.id}, event)" title="Delete this entry">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteVisit(visitId, event) {
    if (event) event.stopPropagation();
    if (!confirm('Are you sure you want to delete this entry? This will also un-stick the camera.')) return;
    try {
        const resp = await fetch(`${API_BASE}/delete-visit/${visitId}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.status === 'success') {
            loadDashboard(); // Force refresh
        } else {
            alert('Failed to delete: ' + (data.detail || data.message));
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// --- Tab Management ---
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById('btn-' + tabId).classList.add('active');
    
    if (tabId === 'workers-tab') loadWorkers();
}

// --- Visitor Detail Modal ---
function openVisitorDetail(index) {
    const v = allVehicles[index];
    if (!v) return;

    document.getElementById('vdetail-plate').textContent = v.vehicle_no;
    document.getElementById('vdetail-name').textContent = v.visitor_name || 'Not provided';
    document.getElementById('vdetail-phone').textContent = v.phone || '-';
    document.getElementById('vdetail-type').textContent = v.visitor_type || 'visitor';
    
    document.getElementById('vdetail-in').textContent = v.in_time;
    document.getElementById('vdetail-out').textContent = v.out_time || '-';
    document.getElementById('vdetail-status').innerHTML = v.status === 'inside' ? 
        '<span class="status-badge status-in">Inside</span>' : 
        '<span class="status-badge status-out">Exited</span>';

    // Set images
    const vImg = document.getElementById('vdetail-vehicle-img');
    if (v.vehicle_image_path) {
        vImg.src = v.vehicle_image_path.replace(/\\/g, '/');
        vImg.classList.remove('hidden');
        document.getElementById('vdetail-vehicle-img-na').classList.add('hidden');
    } else {
        vImg.classList.add('hidden');
        document.getElementById('vdetail-vehicle-img-na').classList.remove('hidden');
    }

    // Modal display
    document.getElementById('visitor-detail-modal').classList.remove('hidden');
}

function closeVisitorDetail() {
    document.getElementById('visitor-detail-modal').classList.add('hidden');
}

// --- Worker Management ---
async function loadWorkers() {
    try {
        const resp = await fetch(`${API_BASE}/workers`);
        const data = await resp.json();
        if (data.status === 'success') {
            allWorkers = data.workers;
            const tbody = document.getElementById('workers-tbody');
            if (!tbody) return;
            
            if (allWorkers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No regular workers registered.</td></tr>';
                return;
            }

            tbody.innerHTML = allWorkers.map(w => `
                <tr>
                    <td><strong>${w.vehicle_no}</strong></td>
                    <td>${w.user_name}</td>
                    <td>${w.flat_no || '-'}</td>
                    <td>${w.phone || '-'}</td>
                    <td>${w.created_at}</td>
                    <td><button class="btn-danger" onclick="deleteWorker('${w.vehicle_no}')"><i class="fas fa-trash"></i></button></td>
                </tr>
            `).join('');
        }
    } catch (e) { console.error("Workers Load Error:", e); }
}

function openAddWorkerModal() { document.getElementById('add-worker-modal').classList.remove('hidden'); }
function closeAddWorkerModal() { document.getElementById('add-worker-modal').classList.add('hidden'); }

async function submitNewWorker() {
    const vno = document.getElementById('worker_vno').value;
    const name = document.getElementById('worker_name').value;
    if (!vno || !name) { alert("Vehicle No and Name are required"); return; }

    try {
        const resp = await fetch(`${API_BASE}/add-worker`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vehicle_no: vno, name: name, phone: "" })
        });
        const data = await resp.json();
        if (data.status === 'success') {
            closeAddWorkerModal();
            loadWorkers();
        } else alert("Error: " + data.message);
    } catch (e) { alert("Failed to save"); }
}

async function deleteWorker(vehicleNo) {
    if (!confirm(`Are you sure you want to remove worker ${vehicleNo}?`)) return;
    try {
        const resp = await fetch(`${API_BASE}/delete-worker/${vehicleNo}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.status === 'success') {
            loadWorkers();
        } else alert("Error: " + data.message);
    } catch (e) { alert("Failed to delete"); }
}

// --- Search / Filter ---
function filterTable() {
    const query = document.querySelector('.search-input').value.toLowerCase();
    const filtered = allVehicles.filter(v => 
        v.vehicle_no.toLowerCase().includes(query) || 
        (v.visitor_name && v.visitor_name.toLowerCase().includes(query))
    );
    updateVehiclesTable(filtered);
}

// --- Export ---
function exportToCSV() {
    if (allVehicles.length === 0) return;
    const headers = ['Vehicle No', 'Type', 'Name', 'In Time', 'Out Time', 'Status'];
    const rows = allVehicles.map(v => [v.vehicle_no, v.visitor_type, v.visitor_name, v.in_time, v.out_time, v.status]);
    
    let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map(r => r.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `vehicle_log_${new Date().toLocaleDateString()}.csv`);
    document.body.appendChild(link);
    link.click();
}

// --- Lightbox ---
function openLightbox(src) {
    const lb = document.getElementById('image-lightbox');
    const img = document.getElementById('lightbox-img');
    img.src = src;
    lb.classList.remove('hidden');
}
function closeLightbox() { document.getElementById('image-lightbox').classList.add('hidden'); }

// --- Alerts ---
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
        <a href="/api/kiosk?plate=${plate}" class="btn-alert">Open Form</a>
    `;
    alertBanner.style.display = 'flex';
}

function hideVisitorAlert() {
    const banner = document.getElementById('visitor-alert-banner');
    if (banner) banner.style.display = 'none';
}

// Alert CSS
const style = document.createElement('style');
style.textContent = `
    .visitor-alert {
        position: fixed; top: 20px; right: 20px; background: white; padding: 15px; 
        border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); z-index: 1000;
        display: none; flex-direction: column; gap: 10px; border-left: 5px solid #10b981;
    }
    .btn-alert { background: #10b981; color: white; padding: 8px; text-decoration: none; border-radius: 5px; text-align: center; font-weight: 600; }
    .clickable-row { cursor: pointer; }
    .clickable-row:hover { background-color: rgba(13, 148, 136, 0.05); }
    .hidden { display: none !important; }
`;
document.head.appendChild(style);
