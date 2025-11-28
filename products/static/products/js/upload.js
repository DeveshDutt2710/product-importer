const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const uploadArea = document.getElementById('uploadArea');
const fileInfo = document.getElementById('fileInfo');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusValue = document.getElementById('statusValue');
const processedValue = document.getElementById('processedValue');
const successfulValue = document.getElementById('successfulValue');
const failedValue = document.getElementById('failedValue');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const successSection = document.getElementById('successSection');
const uploadAnotherBtn = document.getElementById('uploadAnotherBtn');

let currentJobId = null;
let pollInterval = null;

selectFileBtn.addEventListener('click', () => {
    fileInput.click();
});

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.endsWith('.csv')) {
            handleFileSelect(file);
        } else {
            showError('Please select a CSV file');
        }
    }
});

retryBtn.addEventListener('click', () => {
    resetUI();
});

uploadAnotherBtn.addEventListener('click', () => {
    resetUI();
});

function handleFileSelect(file) {
    fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadFile(formData);
}

function uploadFile(formData) {
    progressSection.style.display = 'block';
    errorSection.style.display = 'none';
    successSection.style.display = 'none';
    updateProgress(0, 'pending', 0, 0, 0, 0);
    
    fetch('/api/upload/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        currentJobId = data.job_id;
        statusValue.textContent = data.status;
        startPolling(currentJobId);
    })
    .catch(error => {
        showError(`Upload failed: ${error.message}`);
    });
}

function startPolling(jobId) {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    
    pollInterval = setInterval(() => {
        fetch(`/api/import/${jobId}/status/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    stopPolling();
                    return;
                }
                
                updateProgress(
                    data.progress,
                    data.status,
                    data.total_records,
                    data.processed_records,
                    data.successful_records,
                    data.failed_records
                );
                
                if (data.status === 'completed') {
                    stopPolling();
                    showSuccess();
                } else if (data.status === 'failed') {
                    stopPolling();
                    showError(data.error_message || 'Import failed');
                }
            })
            .catch(error => {
                showError(`Failed to get status: ${error.message}`);
                stopPolling();
            });
    }, 2000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function updateProgress(progress, status, total, processed, successful, failed) {
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    statusValue.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    processedValue.textContent = `${processed} / ${total}`;
    successfulValue.textContent = successful;
    failedValue.textContent = failed;
}

function showError(message) {
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    progressSection.style.display = 'none';
    stopPolling();
}

function showSuccess() {
    successSection.style.display = 'block';
    progressSection.style.display = 'none';
}

function resetUI() {
    fileInput.value = '';
    fileInfo.textContent = '';
    progressSection.style.display = 'none';
    errorSection.style.display = 'none';
    successSection.style.display = 'none';
    currentJobId = null;
    stopPolling();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

