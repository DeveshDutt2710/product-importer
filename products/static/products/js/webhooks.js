let currentFilters = {};
let currentWebhookUuid = null;
let deleteWebhookUuid = null;

const webhooksTableBody = document.getElementById('webhooksTableBody');
const webhooksCount = document.getElementById('webhooksCount');
const webhookModal = document.getElementById('webhookModal');
const webhookForm = document.getElementById('webhookForm');
const modalTitle = document.getElementById('modalTitle');
const webhookUuid = document.getElementById('webhookUuid');
const webhookUrl = document.getElementById('webhookUrl');
const webhookEventType = document.getElementById('webhookEventType');
const webhookSecret = document.getElementById('webhookSecret');
const webhookEnabled = document.getElementById('webhookEnabled');
const deleteModal = document.getElementById('deleteModal');
const testResultModal = document.getElementById('testResultModal');
const testResultContent = document.getElementById('testResultContent');

document.getElementById('createWebhookBtn').addEventListener('click', () => {
    openCreateModal();
});

document.getElementById('applyFiltersBtn').addEventListener('click', () => {
    applyFilters();
});

document.getElementById('clearFiltersBtn').addEventListener('click', () => {
    clearFilters();
});

document.getElementById('closeModalBtn').addEventListener('click', closeWebhookModal);
document.getElementById('cancelBtn').addEventListener('click', closeWebhookModal);
document.getElementById('saveWebhookBtn').addEventListener('click', saveWebhook);

document.getElementById('closeDeleteModalBtn').addEventListener('click', closeDeleteModal);
document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal);
document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

document.getElementById('closeTestResultModalBtn').addEventListener('click', closeTestResultModal);
document.getElementById('closeTestResultBtn').addEventListener('click', closeTestResultModal);

document.getElementById('closeNotificationBtn').addEventListener('click', closeNotification);

function loadWebhooks() {
    webhooksTableBody.innerHTML = '<tr><td colspan="5" class="loading">Loading webhooks...</td></tr>';
    
    const params = new URLSearchParams(currentFilters);
    
    fetch(`/api/webhooks/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification('Error: ' + data.error, 'error');
                return;
            }
            
            displayWebhooks(data.results);
            webhooksCount.textContent = `Total: ${data.total_count} webhooks`;
        })
        .catch(error => {
            webhooksTableBody.innerHTML = '<tr><td colspan="5" class="loading">Error loading webhooks</td></tr>';
            showNotification('Error loading webhooks: ' + error.message, 'error');
        });
}

function displayWebhooks(webhooks) {
    if (webhooks.length === 0) {
        webhooksTableBody.innerHTML = '<tr><td colspan="5" class="loading">No webhooks found</td></tr>';
        return;
    }
    
    webhooksTableBody.innerHTML = webhooks.map(webhook => `
        <tr>
            <td>${escapeHtml(webhook.url)}</td>
            <td>${escapeHtml(webhook.event_type)}</td>
            <td><span class="active-badge ${webhook.enabled ? 'active' : 'inactive'}">${webhook.enabled ? 'Enabled' : 'Disabled'}</span></td>
            <td>${formatDate(webhook.created_at)}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn action-btn-edit" onclick="editWebhook('${webhook.uuid}')">Edit</button>
                    <button class="action-btn action-btn-primary" onclick="testWebhook('${webhook.uuid}')">Test</button>
                    <button class="action-btn action-btn-delete" onclick="deleteWebhook('${webhook.uuid}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function applyFilters() {
    currentFilters = {};
    
    const eventType = document.getElementById('filterEventType').value;
    if (eventType) currentFilters.event_type = eventType;
    
    const enabled = document.getElementById('filterEnabled').value;
    if (enabled) currentFilters.enabled = enabled;
    
    loadWebhooks();
}

function clearFilters() {
    document.getElementById('filterEventType').value = '';
    document.getElementById('filterEnabled').value = '';
    currentFilters = {};
    loadWebhooks();
}

function openCreateModal() {
    currentWebhookUuid = null;
    modalTitle.textContent = 'Create Webhook';
    webhookForm.reset();
    webhookUuid.value = '';
    webhookEnabled.checked = true;
    clearFormErrors();
    webhookModal.style.display = 'flex';
}

function editWebhook(uuid) {
    currentWebhookUuid = uuid;
    modalTitle.textContent = 'Edit Webhook';
    
    fetch(`/api/webhooks/${uuid}/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification('Error loading webhook: ' + data.error, 'error');
                return;
            }
            
            webhookUuid.value = data.uuid;
            webhookUrl.value = data.url;
            webhookEventType.value = data.event_type;
            webhookEnabled.checked = data.enabled;
            clearFormErrors();
            webhookModal.style.display = 'flex';
        })
        .catch(error => {
            showNotification('Error loading webhook: ' + error.message, 'error');
        });
}

function saveWebhook() {
    clearFormErrors();
    
    const data = {
        url: webhookUrl.value.trim(),
        event_type: webhookEventType.value,
        secret: webhookSecret.value.trim() || null,
    };
    
    if (webhookEnabled.checked) {
        data.enabled = true;
    }
    
    const url = currentWebhookUuid 
        ? `/api/webhooks/${currentWebhookUuid}/`
        : '/api/webhooks/';
    
    const method = currentWebhookUuid ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            if (typeof data.error === 'object') {
                displayFormErrors(data.error);
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
            return;
        }
        
        closeWebhookModal();
        const message = currentWebhookUuid ? 'Webhook updated successfully' : 'Webhook created successfully';
        showNotification(message, 'success');
        loadWebhooks();
    })
    .catch(error => {
        showNotification('Error saving webhook: ' + error.message, 'error');
    });
}

function testWebhook(uuid) {
    fetch(`/api/webhooks/${uuid}/test/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification('Error: ' + data.error, 'error');
            return;
        }
        
        displayTestResult(data);
        testResultModal.style.display = 'flex';
    })
    .catch(error => {
        showNotification('Error testing webhook: ' + error.message, 'error');
    });
}

function displayTestResult(result) {
    const successClass = result.success ? 'success' : 'error';
    const statusText = result.success ? 'Success' : 'Failed';
    
    testResultContent.innerHTML = `
        <div class="test-result ${successClass}">
            <h3>Status: ${statusText}</h3>
            ${result.status_code ? `<p><strong>Status Code:</strong> ${result.status_code}</p>` : ''}
            ${result.response_time ? `<p><strong>Response Time:</strong> ${result.response_time}s</p>` : ''}
            ${result.error ? `<p><strong>Error:</strong> ${escapeHtml(result.error)}</p>` : ''}
            ${result.response_body ? `<p><strong>Response Body:</strong> <pre>${escapeHtml(result.response_body)}</pre></p>` : ''}
        </div>
    `;
}

function deleteWebhook(uuid) {
    deleteWebhookUuid = uuid;
    deleteModal.style.display = 'flex';
}

function confirmDelete() {
    fetch(`/api/webhooks/${deleteWebhookUuid}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification('Error: ' + data.error, 'error');
            return;
        }
        
        closeDeleteModal();
        showNotification(data.message || 'Webhook deleted successfully', 'success');
        loadWebhooks();
    })
    .catch(error => {
        showNotification('Error deleting webhook: ' + error.message, 'error');
    });
}

function closeWebhookModal() {
    webhookModal.style.display = 'none';
    webhookForm.reset();
    currentWebhookUuid = null;
}

function closeDeleteModal() {
    deleteModal.style.display = 'none';
    deleteWebhookUuid = null;
}

function closeTestResultModal() {
    testResultModal.style.display = 'none';
}

function clearFormErrors() {
    document.getElementById('urlError').textContent = '';
    document.getElementById('eventTypeError').textContent = '';
    document.getElementById('secretError').textContent = '';
}

function displayFormErrors(errors) {
    if (errors.url) {
        document.getElementById('urlError').textContent = errors.url;
    }
    if (errors.event_type) {
        document.getElementById('eventTypeError').textContent = errors.event_type;
    }
    if (errors.secret) {
        document.getElementById('secretError').textContent = errors.secret;
    }
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notificationMessage');
    
    notification.className = `notification ${type}`;
    notificationMessage.textContent = message;
    notification.style.display = 'block';
    
    setTimeout(() => {
        closeNotification();
    }, 5000);
}

function closeNotification() {
    const notification = document.getElementById('notification');
    notification.style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getCsrfToken() {
    if (typeof window.getCsrfTokenFromCookie === 'function') {
        return window.getCsrfTokenFromCookie();
    }
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

window.editWebhook = editWebhook;
window.testWebhook = testWebhook;
window.deleteWebhook = deleteWebhook;

loadWebhooks();

