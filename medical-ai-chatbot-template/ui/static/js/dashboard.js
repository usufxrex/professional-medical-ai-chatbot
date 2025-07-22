// Dashboard functionality (placeholder for future expansion)
class DashboardManager {
    constructor() {
        console.log('📊 Dashboard manager ready');
    }
    
    async loadDashboard() {
        try {
            const response = await fetch('/api/diseases');
            const diseases = await response.json();
            console.log('Diseases loaded:', diseases);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});