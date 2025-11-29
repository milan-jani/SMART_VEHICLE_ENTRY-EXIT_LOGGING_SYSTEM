/**
 * Enhanced Dashboard JavaScript
 * Handles data fetching, filtering, theming, and dynamic updates
 */

// API Configuration
const API_BASE = '/api';

// Global data storage
let allVehicles = [];
let vehicleChart = null;

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        document.getElementById('theme-icon').classList.replace('fa-moon', 'fa-sun');
    }
}

// Toggle dark/light mode
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    
    body.classList.toggle('dark-mode');
    
    if (body.classList.contains('dark-mode')) {
        themeIcon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('theme', 'dark');
    } else {
        themeIcon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('theme', 'light');
    }
    
    // Reload dashboard to update chart colors
    loadDashboard();
}

/**
 * Load dashboard data (statistics and vehicles)
 */
async function loadDashboard() {
    try { 
        // Show loading state with spinner
        document.getElementById('vehicles-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading"><i class="fas fa-spinner"></i><div>Loading data...</div></td></tr>';
        
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
            allVehicles = vehiclesData.vehicles;
            updateVehiclesTable(allVehicles);
        }
        
        // Update last updated timestamp
        document.getElementById('last-updated').textContent = new Date().toLocaleString('en-IN');
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        document.getElementById('vehicles-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading"><i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i><div>Error loading data. Please check if the API is running.</div></td></tr>';
    }
}

/**
 * Update statistics cards with animation and chart
 */
function updateStatistics(stats) {
    animateNumber('total-entries', stats.total_entries || 0);
    animateNumber('open-entries', stats.open_entries || 0);
    animateNumber('closed-entries', stats.closed_entries || 0);
    animateNumber('unique-vehicles', stats.unique_vehicles || 0);
    
    // Update pie chart
    updatePieChart(stats);
}

/**
 * Animate number counting effect
 */
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const currentValue = parseInt(element.textContent) || 0;
    const duration = 1000;
    const steps = 30;
    const increment = (targetValue - currentValue) / steps;
    let current = currentValue;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        current += increment;
        element.textContent = Math.round(current);
        
        if (step >= steps) {
            element.textContent = targetValue;
            clearInterval(timer);
        }
    }, duration / steps);
}

/**
 * Update or create pie chart
 */
function updatePieChart(stats) {
    const ctx = document.getElementById('vehicleChart');
    if (!ctx) return;
    
    const isDarkMode = document.body.classList.contains('dark-mode');
    const textColor = isDarkMode ? '#f1f5f9' : '#1e293b';
    
    const data = {
        labels: ['Currently Inside', 'Exited Today'],
        datasets: [{
            data: [stats.open_entries || 0, stats.closed_entries || 0],
            backgroundColor: [
                'rgba(16, 185, 129, 0.8)',
                'rgba(245, 158, 11, 0.8)'
            ],
            borderColor: [
                'rgba(16, 185, 129, 1)',
                'rgba(245, 158, 11, 1)'
            ],
            borderWidth: 2
        }]
    };
    
    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        padding: 15,
                        font: {
                            size: 13,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
    
    // Destroy existing chart if it exists
    if (vehicleChart) {
        vehicleChart.destroy();
    }
    
    // Create new chart
    vehicleChart = new Chart(ctx, config);
}

/**
 * Update vehicles table
 */
function updateVehiclesTable(vehicles) {
    const tbody = document.getElementById('vehicles-tbody');
    
    if (vehicles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading"><i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 10px;"></i><div>No vehicles logged yet.</div></td></tr>';
        return;
    }
    
    // Reverse to show newest first
    const reversedVehicles = [...vehicles].reverse();
    
    tbody.innerHTML = reversedVehicles.map((vehicle, index) => {
        const status = vehicle.out_time ? 
            '<span class="status-badge status-out"><i class="fas fa-check-circle"></i> Exited</span>' : 
            '<span class="status-badge status-in"><i class="fas fa-car-side"></i> Inside</span>';
        
        const vehicleIcon = getVehicleIcon(index);
        const statusColor = vehicle.out_time ? '#f59e0b' : '#10b981';
        
        return `
            <tr style="animation: slideInUp 0.6s ease ${index * 0.08}s backwards;">
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5rem;">${vehicleIcon}</span>
                        <strong style="font-size: 1.1rem;">${escapeHtml(vehicle.vehicle_no)}</strong>
                    </div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-user-circle" style="color: #8b5cf6; font-size: 1.2rem;"></i>
                        <span>${escapeHtml(vehicle.visitor_name) || '-'}</span>
                    </div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-phone-alt" style="color: #3b82f6; font-size: 1rem;"></i>
                        <span>${escapeHtml(vehicle.phone) || '-'}</span>
                    </div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-clipboard-list" style="color: #ec4899; font-size: 1rem;"></i>
                        <span>${escapeHtml(vehicle.purpose) || '-'}</span>
                    </div>
                </td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        <span style="display: flex; align-items: center; gap: 6px;">
                            <i class="fas fa-sign-in-alt" style="color: #10b981; font-size: 1rem;"></i>
                            <strong>${formatDateTime(vehicle.in_time)}</strong>
                        </span>
                    </div>
                </td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        ${vehicle.out_time ? `
                            <span style="display: flex; align-items: center; gap: 6px;">
                                <i class="fas fa-sign-out-alt" style="color: #f59e0b; font-size: 1rem;"></i>
                                <strong>${formatDateTime(vehicle.out_time)}</strong>
                            </span>
                        ` : '<span style="color: #94a3b8;">-</span>'}
                    </div>
                </td>
                <td>${status}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Get random vehicle icon for visual variety
 */
function getVehicleIcon(index) {
    return '<i class="fas fa-car"></i>';
}

/**
 * Add slide up animation
 */
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

/**
 * Filter table based on search and status
 */
function filterTable() {
    const searchInput = document.getElementById('search-input');
    const searchTerm = searchInput.value.toLowerCase().trim();
    const statusFilter = document.getElementById('status-filter').value;
    
    if (!allVehicles || allVehicles.length === 0) {
        return;
    }
    
    // Visual feedback for active search
    if (searchTerm !== '' || statusFilter !== 'all') {
        searchInput.style.borderColor = '#10b981';
        searchInput.style.boxShadow = '0 0 0 4px rgba(16, 185, 129, 0.15)';
    } else {
        searchInput.style.borderColor = '';
        searchInput.style.boxShadow = '';
    }
    
    let filteredVehicles = allVehicles.filter(vehicle => {
        // Search filter with better null handling
        const vehicleNo = vehicle.vehicle_no ? String(vehicle.vehicle_no).toLowerCase() : '';
        const visitorName = vehicle.visitor_name ? String(vehicle.visitor_name).toLowerCase() : '';
        const phone = vehicle.phone ? String(vehicle.phone).toLowerCase() : '';
        const purpose = vehicle.purpose ? String(vehicle.purpose).toLowerCase() : '';
        
        const matchesSearch = searchTerm === '' ||
            vehicleNo.includes(searchTerm) ||
            visitorName.includes(searchTerm) ||
            phone.includes(searchTerm) ||
            purpose.includes(searchTerm);
        
        // Status filter
        const matchesStatus = 
            statusFilter === 'all' ||
            (statusFilter === 'inside' && !vehicle.out_time) ||
            (statusFilter === 'exited' && vehicle.out_time);
        
        return matchesSearch && matchesStatus;
    });
    
    updateVehiclesTable(filteredVehicles);
    
    // Show filtered count
    const tableHeader = document.querySelector('.table-header h3');
    if (tableHeader) {
        const filterInfo = (searchTerm !== '' || statusFilter !== 'all') ? 
            ` <span style="color: #10b981; font-size: 0.9rem;">(${filteredVehicles.length} results)</span>` : '';
        tableHeader.innerHTML = `<i class="fas fa-table"></i> Recent Vehicle Entries${filterInfo}`;
    }
}

/**
 * Export table data to CSV
 */
function exportToCSV() {
    if (allVehicles.length === 0) {
        alert('No data to export!');
        return;
    }
    
    // Create CSV content
    let csvContent = 'Vehicle No,Visitor Name,Phone,Purpose,In Time,Out Time,Status\n';
    
    allVehicles.forEach(vehicle => {
        const status = vehicle.out_time ? 'Exited' : 'Inside';
        csvContent += `"${vehicle.vehicle_no}","${vehicle.visitor_name || ''}","${vehicle.phone || ''}","${vehicle.purpose || ''}","${vehicle.in_time}","${vehicle.out_time || ''}","${status}"\n`;
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `vehicle_log_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

// Initialize theme and load dashboard on page load
window.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadDashboard();
});
