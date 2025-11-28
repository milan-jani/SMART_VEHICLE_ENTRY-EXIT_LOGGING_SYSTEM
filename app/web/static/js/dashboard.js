/**
 * Dashboard JavaScript
 * Handles data fetching and dynamic updates for the dashboard
 */

// API Configuration
const API_BASE = '/api';

/**
 * Load dashboard data (statistics and vehicles)
 */
async function loadDashboard() {
    try {
        // Show loading state
        document.getElementById('vehicles-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading">Loading data...</td></tr>';
        
        // Fetch statistics
        const statsResponse = await fetch(`${API_BASE}/stats`);
        const statsData = await statsResponse.json();
        
        if (statsData.status === 'success') {
            updateStatistics(statsData.statistics);
        }
        
        // Fetch vehicles
        const vehiclesResponse = await fetch(`${API_BASE}/vehicles`);
        const vehiclesData = await vehiclesResponse.json();
        
        if (vehiclesData.status === 'success') {
            updateVehiclesTable(vehiclesData.vehicles);
        }
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        document.getElementById('vehicles-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading">Error loading data. Is the API running?</td></tr>';
    }
}

/**
 * Update statistics cards
 */
function updateStatistics(stats) {
    document.getElementById('total-entries').textContent = stats.total_entries || 0;
    document.getElementById('open-entries').textContent = stats.open_entries || 0;
    document.getElementById('closed-entries').textContent = stats.closed_entries || 0;
    document.getElementById('unique-vehicles').textContent = stats.unique_vehicles || 0;
}

/**
 * Update vehicles table
 */
function updateVehiclesTable(vehicles) {
    const tbody = document.getElementById('vehicles-tbody');
    
    if (vehicles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No vehicles logged yet.</td></tr>';
        return;
    }
    
    // Reverse to show newest first
    const reversedVehicles = [...vehicles].reverse();
    
    tbody.innerHTML = reversedVehicles.map(vehicle => {
        const status = vehicle.out_time ? 
            '<span class="status-badge status-out">Exited</span>' : 
            '<span class="status-badge status-in">Inside</span>';
        
        return `
            <tr>
                <td><strong>${escapeHtml(vehicle.vehicle_no)}</strong></td>
                <td>${escapeHtml(vehicle.visitor_name) || '-'}</td>
                <td>${escapeHtml(vehicle.phone) || '-'}</td>
                <td>${escapeHtml(vehicle.purpose) || '-'}</td>
                <td>${formatDateTime(vehicle.in_time)}</td>
                <td>${vehicle.out_time ? formatDateTime(vehicle.out_time) : '-'}</td>
                <td>${status}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Format datetime for display
 */
function formatDateTime(datetime) {
    if (!datetime) return '-';
    try {
        const date = new Date(datetime);
        return date.toLocaleString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return datetime;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Auto-refresh dashboard every 30 seconds
 */
setInterval(loadDashboard, 30000);
