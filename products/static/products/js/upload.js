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
let isUploading = false;

selectFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

uploadArea.addEventListener('click', (e) => {
    if (e.target !== selectFileBtn && !selectFileBtn.contains(e.target)) {
        fileInput.click();
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0 && !isUploading) {
        const file = e.target.files[0];
        e.target.value = '';
        handleFileSelect(file);
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
    if (isUploading) {
        console.log('Upload already in progress, ignoring file selection');
        return;
    }
    
    fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadFile(formData);
}

function uploadFile(formData) {
    if (isUploading) {
        console.log('Upload already in progress');
        return;
    }
    
    isUploading = true;
    progressSection.style.display = 'block';
    errorSection.style.display = 'none';
    successSection.style.display = 'none';
    updateProgress(0, 'pending', 0, 0, 0, 0);
    
    const csrfToken = getCsrfToken();
    
    fetch('/api/upload/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            return response.text().then(text => {
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error('Server returned non-JSON response. Check console for details.');
            });
        }
        return response.json().then(data => {
            if (!response.ok) {
                throw new Error(data.error || `Upload failed with status ${response.status}`);
            }
            return data;
        });
    })
    .then(data => {
        if (data.error) {
            isUploading = false;
            showError(data.error);
            return;
        }
        
        if (!data.job_id) {
            isUploading = false;
            console.error('Response data:', data);
            showError('No job ID received from server. Check console for response details.');
            return;
        }
        
        currentJobId = data.job_id;
        statusValue.textContent = data.status || 'pending';
        isUploading = false;
        startPolling(currentJobId);
    })
    .catch(error => {
        isUploading = false;
        console.error('Upload error:', error);
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
    isUploading = false;
    stopPolling();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

