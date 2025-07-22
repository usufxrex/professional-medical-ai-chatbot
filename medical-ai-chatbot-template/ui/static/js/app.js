// ===== GLOBAL STATE AND UTILITIES =====
const AppState = {
    currentSection: 'chat',
    diseases: [],
    selectedDisease: null,
    systemHealth: null,
    isLoading: false,
    uploadInProgress: false
};

// Utility functions
const utils = {
    formatNumber: (num) => {
        return new Intl.NumberFormat().format(num);
    },
    
    formatDate: (date) => {
        return new Intl.DateTimeFormat().format(new Date(date));
    },
    
    showNotification: (title, message, type = 'info', duration = 5000) => {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-header">
                <i class="${iconMap[type]} notification-icon"></i>
                <h4 class="notification-title">${title}</h4>
            </div>
            <p class="notification-message">${message}</p>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add click handler for close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        container.appendChild(notification);
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, duration);
        }
        
        return notification;
    },
    
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// ===== API CLIENT =====
const API = {
    baseURL: '',
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}/api${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Chat endpoints
    async sendMessage(message, diseaseFilter = null) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                disease_filter: diseaseFilter
            })
        });
    },
    
    // Disease endpoints
    async getDiseases() {
        return this.request('/diseases');
    },
    
    async getDiseaseStatistics(diseaseName) {
        return this.request(`/diseases/${diseaseName}/statistics`);
    },
    
    // System endpoints
    async getSystemOverview() {
        return this.request('/system/overview');
    },
    
    async getHealth() {
        return this.request('/health');
    },
    
    // Dataset management
    async listDatasets() {
        return this.request('/datasets');
    },
    
    async addDataset(datasetData) {
        return this.request('/datasets/add', {
            method: 'POST',
            body: JSON.stringify(datasetData)
        });
    },
    
    async removeDataset(diseaseName) {
        return this.request(`/datasets/${diseaseName}`, {
            method: 'DELETE'
        });
    },
    
    // File upload
    async uploadFile(formData) {
        return fetch('/api/upload', {
            method: 'POST',
            body: formData
        }).then(response => response.json());
    }
};

// ===== INITIALIZATION =====
async function initializeApp() {
    showLoadingScreen();
    
    try {
        // Initialize loading progress
        const progressBar = document.getElementById('loading-progress-bar');
        let progress = 0;
        
        const updateProgress = (value) => {
            progress = Math.min(value, 100);
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
        };
        
        // Load system health
        updateProgress(20);
        await loadSystemHealth();
        
        // Load diseases
        updateProgress(50);
        await loadDiseases();
        
        // Initialize UI components
        updateProgress(80);
        initializeEventListeners();
        initializeFileUpload();
        initializeDatasetManagement();
        
        updateProgress(100);
        
        // Show main app after delay
        setTimeout(() => {
            hideLoadingScreen();
            utils.showNotification(
                'System Ready',
                'Medical AI Assistant is now online and ready to help!',
                'success'
            );
        }, 1000);
        
    } catch (error) {
        console.error('App initialization failed:', error);
        utils.showNotification(
            'Initialization Error',
            'Failed to load the application. Please refresh the page.',
            'error',
            0
        );
        hideLoadingScreen();
    }
}

function showLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    const appContainer = document.getElementById('app-container');
    
    if (loadingScreen) loadingScreen.classList.remove('hidden');
    if (appContainer) appContainer.style.display = 'none';
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    const appContainer = document.getElementById('app-container');
    
    if (loadingScreen) loadingScreen.classList.add('hidden');
    if (appContainer) appContainer.style.display = 'block';
}

async function loadSystemHealth() {
    try {
        AppState.systemHealth = await API.getHealth();
        updateSystemStatus();
    } catch (error) {
        console.error('Failed to load system health:', error);
    }
}

async function loadDiseases() {
    try {
        AppState.diseases = await API.getDiseases();
        populateDiseaseSelector();
        updateDiseaseStats();
    } catch (error) {
        console.error('Failed to load diseases:', error);
        AppState.diseases = [];
    }
}

function updateSystemStatus() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.system-status span');
    const totalRecords = document.getElementById('total-records');
    const liveRecords = document.getElementById('live-records');
    const liveDiseases = document.getElementById('live-diseases');
    
    if (AppState.systemHealth) {
        const isHealthy = AppState.systemHealth.status === 'healthy';
        
        if (statusDot) {
            statusDot.className = `status-dot ${isHealthy ? 'online' : 'offline'}`;
        }
        
        if (statusText) {
            statusText.textContent = isHealthy ? 'System Online' : 'System Offline';
        }
        
        if (totalRecords) {
            totalRecords.textContent = utils.formatNumber(AppState.systemHealth.total_records || 0);
        }
        
        if (liveRecords) {
            liveRecords.textContent = utils.formatNumber(AppState.systemHealth.total_records || 0);
        }
        
        if (liveDiseases) {
            liveDiseases.textContent = AppState.systemHealth.diseases_loaded || 0;
        }
    }
}

function populateDiseaseSelector() {
    const diseaseSelect = document.getElementById('disease-filter');
    if (!diseaseSelect) return;
    
    // Clear existing options (except the first one)
    while (diseaseSelect.children.length > 1) {
        diseaseSelect.removeChild(diseaseSelect.lastChild);
    }
    
    // Add disease options
    Object.entries(AppState.diseases).forEach(([key, disease]) => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = disease.name || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        diseaseSelect.appendChild(option);
    });
}

function updateDiseaseStats() {
    // Update disease count in sidebar
    const diseaseCount = Object.keys(AppState.diseases).length;
    // Additional stats updates can be added here
}

// ===== EVENT LISTENERS =====
function initializeEventListeners() {
    // Navigation
    initializeNavigation();
    
    // Quick question buttons
    initializeQuickQuestions();
    
    // Disease filter
    const diseaseFilter = document.getElementById('disease-filter');
    if (diseaseFilter) {
        diseaseFilter.addEventListener('change', (e) => {
            AppState.selectedDisease = e.target.value || null;
        });
    }
    
    // Modal controls
    initializeModals();
    
    // Mobile menu (if needed)
    initializeMobileMenu();
}

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            if (section) {
                switchSection(section);
                
                // Update active state
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
            }
        });
    });
}

function switchSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Show target section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.add('active');
        AppState.currentSection = sectionName;
        
        // Load section-specific content
        loadSectionContent(sectionName);
    }
}

async function loadSectionContent(sectionName) {
    switch (sectionName) {
        case 'analytics':
            await loadAnalytics();
            break;
        case 'diseases':
            await loadDiseasesSection();
            break;
        case 'insights':
            await loadInsights();
            break;
    }
}

function initializeQuickQuestions() {
    const quickQuestionBtns = document.querySelectorAll('.quick-question-btn');
    
    quickQuestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            if (question) {
                // Simulate typing the question in the input
                const userInput = document.getElementById('user-input');
                if (userInput) {
                    userInput.value = question;
                    userInput.focus();
                    
                    // Auto-send after a brief delay
                    setTimeout(() => {
                        sendMessage();
                    }, 500);
                }
            }
        });
    });
}

function initializeModals() {
    // Upload modal
    const uploadModal = document.getElementById('upload-modal');
    const uploadModalClose = document.getElementById('upload-modal-close');
    const datasetModal = document.getElementById('dataset-modal');
    const datasetModalClose = document.getElementById('dataset-modal-close');
    
    // Close modal handlers
    if (uploadModalClose) {
        uploadModalClose.addEventListener('click', () => {
            closeModal('upload-modal');
        });
    }
    
    if (datasetModalClose) {
        datasetModalClose.addEventListener('click', () => {
            closeModal('dataset-modal');
        });
    }
    
    // Close on outside click
    [uploadModal, datasetModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal(modal.id);
                }
            });
        }
    });
    
    // Action buttons
    const attachmentBtn = document.getElementById('attachment-btn');
    if (attachmentBtn) {
        attachmentBtn.addEventListener('click', () => {
            showModal('upload-modal');
        });
    }
    
    // Dataset management button (can be added to sidebar)
    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="manage-datasets"]')) {
            showModal('dataset-modal');
            loadDatasetManagement();
        }
    });
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        
        // Reset upload modal content
        if (modalId === 'upload-modal') {
            resetUploadModal();
        }
    }
}

function initializeMobileMenu() {
    // Mobile menu implementation if needed
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // Create mobile menu button if it doesn't exist
    let mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    if (!mobileMenuBtn && window.innerWidth <= 1024) {
        mobileMenuBtn = document.createElement('button');
        mobileMenuBtn.className = 'mobile-menu-btn';
        mobileMenuBtn.innerHTML = '<i class="fas fa-bars"></i>';
        mobileMenuBtn.style.cssText = `
            position: fixed;
            top: 1rem;
            left: 1rem;
            z-index: 101;
            width: 48px;
            height: 48px;
            border: none;
            border-radius: 12px;
            background: var(--primary-blue);
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-lg);
        `;
        
        document.body.appendChild(mobileMenuBtn);
        
        mobileMenuBtn.addEventListener('click', () => {
            sidebar?.classList.toggle('mobile-open');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (!sidebar?.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar?.classList.remove('mobile-open');
            }
        });
    }
}

// ===== FILE UPLOAD SYSTEM =====
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const uploadZone = uploadArea?.querySelector('.upload-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    
    if (!uploadZone || !fileInput) return;
    
    // Click to browse
    browseBtn?.addEventListener('click', () => {
        fileInput.click();
    });
    
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
}

async function handleFileUpload(file) {
    if (AppState.uploadInProgress) return;
    
    // Validate file size
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        utils.showNotification(
            'File Too Large',
            'Please select a file smaller than 16MB.',
            'error'
        );
        return;
    }
    
    // Validate file type
    const allowedTypes = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx', 'xls'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
        utils.showNotification(
            'Invalid File Type',
            'Please select a PDF, image, or dataset file.',
            'error'
        );
        return;
    }
    
    AppState.uploadInProgress = true;
    
    try {
        // Show upload progress
        showUploadProgress();
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload file
        const result = await API.uploadFile(formData);
        
        // Show result
        showUploadResult(result);
        
        utils.showNotification(
            'Upload Successful',
            'File has been processed successfully.',
            'success'
        );
        
    } catch (error) {
        console.error('Upload failed:', error);
        showUploadResult({
            success: false,
            error: error.message || 'Upload failed'
        });
        
        utils.showNotification(
            'Upload Failed',
            error.message || 'Please try again.',
            'error'
        );
    } finally {
        AppState.uploadInProgress = false;
    }
}

function showUploadProgress() {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadResult = document.getElementById('upload-result');
    
    uploadArea.style.display = 'none';
    uploadProgress.style.display = 'block';
    uploadResult.style.display = 'none';
    
    // Simulate progress
    const progressFill = document.getElementById('upload-progress-fill');
    const progressText = document.getElementById('upload-progress-text');
    
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 95) progress = 95;
        
        if (progressFill) progressFill.style.width = `${progress}%`;
        if (progressText) progressText.textContent = `Uploading... ${Math.round(progress)}%`;
        
        if (progress >= 95) {
            clearInterval(progressInterval);
        }
    }, 200);
    
    // Store interval for cleanup
    uploadProgress.dataset.interval = progressInterval;
}

function showUploadResult(result) {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadResult = document.getElementById('upload-result');
    
    // Clean up progress interval
    const progressInterval = uploadProgress?.dataset.interval;
    if (progressInterval) {
        clearInterval(parseInt(progressInterval));
    }
    
    uploadArea.style.display = 'none';
    uploadProgress.style.display = 'none';
    uploadResult.style.display = 'block';
    
    // Set result class
    uploadResult.className = `upload-result ${result.success ? 'success' : 'error'}`;
    
    // Create result content
    let resultHTML = '';
    
    if (result.success) {
        resultHTML = `
            <div class="upload-success">
                <i class="fas fa-check-circle" style="font-size: 2rem; color: var(--accent-green); margin-bottom: 1rem;"></i>
                <h4>File Processed Successfully</h4>
                
                ${result.file_info ? `
                    <div class="file-info">
                        <p><strong>File:</strong> ${result.file_info.filename}</p>
                        <p><strong>Size:</strong> ${(result.file_info.size / 1024).toFixed(1)} KB</p>
                        <p><strong>Type:</strong> ${result.file_info.type.toUpperCase()}</p>
                    </div>
                ` : ''}
                
                ${result.extracted_text ? `
                    <div class="extracted-content">
                        <h5>Extracted Content:</h5>
                        <div class="content-preview">
                            ${result.extracted_text}
                        </div>
                    </div>
                ` : ''}
                
                ${result.analysis ? `
                    <div class="ai-analysis">
                        <h5>AI Analysis:</h5>
                        <div class="analysis-content">
                            ${result.analysis.document_analysis || 'Analysis completed'}
                        </div>
                    </div>
                ` : ''}
                
                ${result.dataset_info ? `
                    <div class="dataset-info">
                        <h5>Dataset Information:</h5>
                        <p><strong>Rows:</strong> ${result.dataset_info.rows}</p>
                        <p><strong>Columns:</strong> ${result.dataset_info.columns}</p>
                        <p>${result.message}</p>
                    </div>
                ` : ''}
            </div>
        `;
    } else {
        resultHTML = `
            <div class="upload-error">
                <i class="fas fa-exclamation-circle" style="font-size: 2rem; color: var(--accent-red); margin-bottom: 1rem;"></i>
                <h4>Upload Failed</h4>
                <p>${result.error || 'An error occurred during upload'}</p>
            </div>
        `;
    }
    
    uploadResult.innerHTML = resultHTML;
}

function resetUploadModal() {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadResult = document.getElementById('upload-result');
    const fileInput = document.getElementById('file-input');
    
    if (uploadArea) uploadArea.style.display = 'block';
    if (uploadProgress) uploadProgress.style.display = 'none';
    if (uploadResult) uploadResult.style.display = 'none';
    if (fileInput) fileInput.value = '';
    
    AppState.uploadInProgress = false;
}

// ===== DATASET MANAGEMENT =====
function initializeDatasetManagement() {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Update active tab
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding pane
            tabPanes.forEach(pane => pane.classList.remove('active'));
            const targetPane = document.getElementById(tabName === 'existing' ? 'existing-datasets' : 'add-new-dataset');
            if (targetPane) targetPane.classList.add('active');
        });
    });
    
    // New dataset form
    const newDatasetForm = document.getElementById('new-dataset-form');
    if (newDatasetForm) {
        newDatasetForm.addEventListener('submit', handleNewDatasetSubmit);
    }
    
    // Cancel button
    const cancelBtn = document.getElementById('cancel-dataset');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            closeModal('dataset-modal');
        });
    }
}

async function loadDatasetManagement() {
    try {
        const datasets = await API.listDatasets();
        populateExistingDatasets(datasets.datasets || []);
    } catch (error) {
        console.error('Failed to load datasets:', error);
        utils.showNotification(
            'Load Error',
            'Failed to load dataset information.',
            'error'
        );
    }
}

function populateExistingDatasets(datasets) {
    const grid = document.getElementById('datasets-grid');
    if (!grid) return;
    
    if (datasets.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--gray-500);">
                <i class="fas fa-database" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3>No Datasets Found</h3>
                <p>Add your first medical dataset to get started.</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = datasets.map(dataset => `
        <div class="dataset-card">
            <div class="dataset-header">
                <h3 class="dataset-title">${dataset.display_name}</h3>
                <span class="dataset-category">${dataset.category}</span>
            </div>
            <p class="dataset-description">${dataset.description || 'No description available'}</p>
            <div class="dataset-stats">
                <div class="dataset-stat">
                    <span class="stat-number">${utils.formatNumber(dataset.records)}</span>
                    <span class="stat-label">Records</span>
                </div>
                <div class="dataset-stat">
                    <span class="stat-number">${dataset.features}</span>
                    <span class="stat-label">Features</span>
                </div>
                <div class="dataset-stat">
                    <span class="stat-number">${dataset.keywords_count}</span>
                    <span class="stat-label">Keywords</span>
                </div>
            </div>
            <div class="dataset-actions">
                <button class="dataset-action-btn" onclick="viewDatasetDetails('${dataset.name}')">
                    <i class="fas fa-eye"></i>
                    View
                </button>
                <button class="dataset-action-btn danger" onclick="removeDataset('${dataset.name}')">
                    <i class="fas fa-trash"></i>
                    Remove
                </button>
            </div>
        </div>
    `).join('');
}

async function handleNewDatasetSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const datasetData = {
        disease_name: formData.get('dataset-name'),
        disease_info: {
            name: formData.get('dataset-display-name'),
            description: formData.get('dataset-description'),
            category: formData.get('dataset-category')
        },
        keywords: formData.get('dataset-keywords').split(',').map(k => k.trim()),
        target_column: formData.get('dataset-target') || null
    };
    
    // Handle file upload for CSV
    const fileInput = document.getElementById('dataset-file');
    if (!fileInput.files[0]) {
        utils.showNotification('Missing File', 'Please select a dataset file.', 'error');
        return;
    }
    
    try {
        // For now, show a message that manual file placement is needed
        utils.showNotification(
            'Dataset Configuration',
            `Please place your CSV file at: diseases/${datasetData.disease_name}/data.csv and restart the application.`,
            'info',
            10000
        );
        
        // In a full implementation, you would upload the file and add the dataset
        // const result = await API.addDataset(datasetData);
        
        closeModal('dataset-modal');
        
    } catch (error) {
        console.error('Failed to add dataset:', error);
        utils.showNotification(
            'Add Dataset Failed',
            error.message || 'Please try again.',
            'error'
        );
    }
}

// Global functions for dataset management
window.viewDatasetDetails = async function(datasetName) {
    try {
        const stats = await API.getDiseaseStatistics(datasetName);
        // Show dataset details in a modal or panel
        console.log('Dataset details:', stats);
        utils.showNotification(
            'Dataset Details',
            `Viewing details for ${datasetName}. Check console for full information.`,
            'info'
        );
    } catch (error) {
        utils.showNotification(
            'Load Error',
            'Failed to load dataset details.',
            'error'
        );
    }
};

window.removeDataset = async function(datasetName) {
    if (!confirm(`Are you sure you want to remove the ${datasetName} dataset? This action cannot be undone.`)) {
        return;
    }
    
    try {
        await API.removeDataset(datasetName);
        utils.showNotification(
            'Dataset Removed',
            `${datasetName} dataset has been removed successfully.`,
            'success'
        );
        
        // Reload the datasets
        await loadDatasetManagement();
        await loadDiseases();
        
    } catch (error) {
        console.error('Failed to remove dataset:', error);
        utils.showNotification(
            'Remove Failed',
            error.message || 'Failed to remove dataset.',
            'error'
        );
    }
};

// ===== SECTION LOADING FUNCTIONS =====
async function loadAnalytics() {
    const overviewCard = document.getElementById('overview-analytics');
    if (!overviewCard) return;
    
    try {
        const overview = await API.getSystemOverview();
        
        overviewCard.innerHTML = `
            <div class="overview-stats">
                <div class="overview-stat">
                    <i class="fas fa-database"></i>
                    <div>
                        <h3>${overview.total_diseases}</h3>
                        <p>Disease Modules</p>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-file-medical"></i>
                    <div>
                        <h3>${utils.formatNumber(overview.total_records)}</h3>
                        <p>Medical Records</p>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-chart-bar"></i>
                    <div>
                        <h3>${overview.average_features}</h3>
                        <p>Avg Features</p>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-robot"></i>
                    <div>
                        <h3>${overview.ai_status === 'available' ? 'Online' : 'Offline'}</h3>
                        <p>AI Status</p>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        overviewCard.innerHTML = '<p>Failed to load analytics data.</p>';
    }
}

async function loadDiseasesSection() {
    const diseasesGrid = document.getElementById('diseases-grid');
    if (!diseasesGrid) return;
    
    const diseases = Object.entries(AppState.diseases);
    
    if (diseases.length === 0) {
        diseasesGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--gray-500);">
                <i class="fas fa-virus" style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3>No Disease Modules Available</h3>
                <p>Add medical datasets to enable disease analysis modules.</p>
                <button class="btn-primary" onclick="showModal('dataset-modal')" style="margin-top: 1rem;">
                    <i class="fas fa-plus"></i>
                    Add Dataset
                </button>
            </div>
        `;
        return;
    }
    
    diseasesGrid.innerHTML = diseases.map(([key, disease]) => `
        <div class="disease-card">
            <div class="disease-card-header">
                <div class="disease-card-icon">
                    <i class="fas fa-microscope"></i>
                </div>
                <h3 class="disease-card-title">${disease.name}</h3>
                <p class="disease-card-subtitle">${disease.category || 'Medical Analysis'}</p>
            </div>
            <div class="disease-card-body">
                <div class="disease-stats">
                    <div class="disease-stat">
                        <span class="stat-number">${utils.formatNumber(disease.total_records || 0)}</span>
                        <span class="stat-label">Records</span>
                    </div>
                    <div class="disease-stat">
                        <span class="stat-number">${disease.features?.length || 0}</span>
                        <span class="stat-label">Features</span>
                    </div>
                </div>
                <p class="disease-description">${disease.description || 'Advanced medical analysis module'}</p>
                <div class="disease-actions">
                    <button class="disease-action-btn" onclick="viewDiseaseStats('${key}')">
                        <i class="fas fa-chart-line"></i>
                        Statistics
                    </button>
                    <button class="disease-action-btn" onclick="askAboutDisease('${key}')">
                        <i class="fas fa-comments"></i>
                        Ask AI
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadInsights() {
    const insightsContainer = document.querySelector('.insights-container');
    if (!insightsContainer) return;
    
    insightsContainer.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--gray-500);">
            <i class="fas fa-brain" style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;"></i>
            <h3>AI Insights Coming Soon</h3>
            <p>Advanced medical insights and pattern recognition will be available here.</p>
        </div>
    `;
}

// Global functions for disease management
window.viewDiseaseStats = async function(diseaseKey) {
    try {
        const stats = await API.getDiseaseStatistics(diseaseKey);
        console.log('Disease statistics:', stats);
        utils.showNotification(
            'Statistics Loaded',
            `Statistics for ${diseaseKey} loaded. Check console for details.`,
            'info'
        );
    } catch (error) {
        utils.showNotification(
            'Load Error',
            'Failed to load disease statistics.',
            'error'
        );
    }
};

window.askAboutDisease = function(diseaseKey) {
    // Switch to chat section and set disease filter
    switchSection('chat');
    
    const diseaseFilter = document.getElementById('disease-filter');
    if (diseaseFilter) {
        diseaseFilter.value = diseaseKey;
        AppState.selectedDisease = diseaseKey;
    }
    
    // Set a sample question
    const userInput = document.getElementById('user-input');
    if (userInput) {
        const diseaseName = AppState.diseases[diseaseKey]?.name || diseaseKey;
        userInput.value = `Tell me about ${diseaseName} based on your dataset`;
        userInput.focus();
    }
};

// ===== EXPORT FOR CHAT MODULE =====
window.AppState = AppState;
window.API = API;
window.utils = utils;
window.showModal = showModal;
window.closeModal = closeModal;