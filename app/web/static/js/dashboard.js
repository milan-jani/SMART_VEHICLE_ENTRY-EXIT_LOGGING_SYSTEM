/**
 * Fixed Dashboard JavaScript
 */
const API_BASE = '/api';
let allVehicles = [];
let vehicleChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadDashboard();
    setInterval(loadDashboard, 5000); // Auto refresh every 5s
});

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
        tbody.innerHTML = '<tr><td colspan="7">No vehicles logged yet.</td></tr>';
        return;
    }

    tbody.innerHTML = vehicles.map((v, i) => `
        <tr onclick="openVisitorDetail(${i})">
            <td><strong>${v.vehicle_no}</strong></td>
            <td>${v.visitor_type || 'Guest'}</td>
            <td>${v.visitor_name || '-'}</td>
            <td>${v.phone || '-'}</td>
            <td>${v.purpose || '-'}</td>
            <td>${v.in_time}</td>
            <td>${v.out_time ? v.out_time : '<span class="status-badge status-in">Inside</span>'}</td>
        </tr>
    `).join('');
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
        <a href="/api/kiosk?plate=${plate}" class="btn-alert">Open Form</a>
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
        position: fixed; top: 20px; right: 20px; background: white; padding: 15px; 
        border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); z-index: 1000;
        display: none; flex-direction: column; gap: 10px; border-left: 5px solid #10b981;
    }
    .btn-alert { background: #10b981; color: white; padding: 8px; text-decoration: none; border-radius: 5px; text-align: center; }
`;
document.head.appendChild(style);
