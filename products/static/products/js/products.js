let currentPage = 1;
let currentFilters = {};
let currentProductUuid = null;
let deleteProductUuid = null;

const productsTableBody = document.getElementById('productsTableBody');
const productsCount = document.getElementById('productsCount');
const paginationSection = document.getElementById('paginationSection');
const paginationInfo = document.getElementById('paginationInfo');
const pageNumbers = document.getElementById('pageNumbers');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');

const productModal = document.getElementById('productModal');
const productForm = document.getElementById('productForm');
const modalTitle = document.getElementById('modalTitle');
const productUuid = document.getElementById('productUuid');
const productSku = document.getElementById('productSku');
const productName = document.getElementById('productName');
const productDescription = document.getElementById('productDescription');
const productActive = document.getElementById('productActive');

const deleteModal = document.getElementById('deleteModal');
const bulkDeleteModal = document.getElementById('bulkDeleteModal');

document.getElementById('createProductBtn').addEventListener('click', () => {
    openCreateModal();
});

document.getElementById('applyFiltersBtn').addEventListener('click', () => {
    applyFilters();
});

document.getElementById('clearFiltersBtn').addEventListener('click', () => {
    clearFilters();
});

document.getElementById('bulkDeleteBtn').addEventListener('click', () => {
    openBulkDeleteModal();
});

document.getElementById('closeModalBtn').addEventListener('click', closeProductModal);
document.getElementById('cancelBtn').addEventListener('click', closeProductModal);
document.getElementById('saveProductBtn').addEventListener('click', saveProduct);

document.getElementById('closeDeleteModalBtn').addEventListener('click', closeDeleteModal);
document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal);
document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

document.getElementById('closeBulkDeleteModalBtn').addEventListener('click', closeBulkDeleteModal);
document.getElementById('cancelBulkDeleteBtn').addEventListener('click', closeBulkDeleteModal);
document.getElementById('confirmBulkDeleteBtn').addEventListener('click', confirmBulkDelete);

document.getElementById('closeNotificationBtn').addEventListener('click', closeNotification);

prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadProducts();
    }
});

nextPageBtn.addEventListener('click', () => {
    currentPage++;
    loadProducts();
});

function loadProducts() {
    productsTableBody.innerHTML = '<tr><td colspan="6" class="loading">Loading products...</td></tr>';
    
    const params = new URLSearchParams({
        page: currentPage,
        ...currentFilters
    });
    
    fetch(`/api/products/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            
            displayProducts(data.results);
            updatePagination(data);
            productsCount.textContent = `Total: ${data.total_count} products`;
        })
        .catch(error => {
            productsTableBody.innerHTML = '<tr><td colspan="6" class="loading">Error loading products</td></tr>';
            console.error('Error:', error);
        });
}

function displayProducts(products) {
    if (products.length === 0) {
        productsTableBody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        return;
    }
    
    productsTableBody.innerHTML = products.map(product => `
        <tr>
            <td>${escapeHtml(product.sku)}</td>
            <td>${escapeHtml(product.name)}</td>
            <td>${escapeHtml(product.description || '')}</td>
            <td><span class="active-badge ${product.active ? 'active' : 'inactive'}">${product.active ? 'Active' : 'Inactive'}</span></td>
            <td>${formatDate(product.created_at)}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn action-btn-edit" onclick="editProduct('${product.uuid}')">Edit</button>
                    <button class="action-btn action-btn-delete" onclick="deleteProduct('${product.uuid}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updatePagination(data) {
    if (data.total_count === 0) {
        paginationSection.style.display = 'none';
        return;
    }
    
    paginationSection.style.display = 'flex';
    paginationInfo.textContent = `Page ${data.page} of ${data.total_pages} (${data.total_count} total)`;
    
    prevPageBtn.disabled = !data.has_previous;
    nextPageBtn.disabled = !data.has_next;
    
    const pages = [];
    const totalPages = data.total_pages;
    const current = data.page;
    
    let startPage = Math.max(1, current - 2);
    let endPage = Math.min(totalPages, current + 2);
    
    if (startPage > 1) {
        pages.push(`<span class="page-number" onclick="goToPage(1)">1</span>`);
        if (startPage > 2) {
            pages.push('<span>...</span>');
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pages.push(`<span class="page-number ${i === current ? 'active' : ''}" onclick="goToPage(${i})">${i}</span>`);
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            pages.push('<span>...</span>');
        }
        pages.push(`<span class="page-number" onclick="goToPage(${totalPages})">${totalPages}</span>`);
    }
    
    pageNumbers.innerHTML = pages.join('');
}

function goToPage(page) {
    currentPage = page;
    loadProducts();
}

function applyFilters() {
    currentFilters = {};
    currentPage = 1;
    
    const sku = document.getElementById('filterSku').value.trim();
    if (sku) currentFilters.sku = sku;
    
    const name = document.getElementById('filterName').value.trim();
    if (name) currentFilters.name = name;
    
    const description = document.getElementById('filterDescription').value.trim();
    if (description) currentFilters.description = description;
    
    const active = document.getElementById('filterActive').value;
    if (active) currentFilters.active = active;
    
    loadProducts();
}

function clearFilters() {
    document.getElementById('filterSku').value = '';
    document.getElementById('filterName').value = '';
    document.getElementById('filterDescription').value = '';
    document.getElementById('filterActive').value = '';
    currentFilters = {};
    currentPage = 1;
    loadProducts();
}

function openCreateModal() {
    currentProductUuid = null;
    modalTitle.textContent = 'Create Product';
    productForm.reset();
    productUuid.value = '';
    productActive.checked = true;
    clearFormErrors();
    productModal.style.display = 'flex';
}

function editProduct(uuid) {
    currentProductUuid = uuid;
    modalTitle.textContent = 'Edit Product';
    
    fetch(`/api/products/${uuid}/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error loading product: ' + data.error);
                return;
            }
            
            productUuid.value = data.uuid;
            productSku.value = data.sku;
            productName.value = data.name;
            productDescription.value = data.description || '';
            productActive.checked = data.active;
            clearFormErrors();
            productModal.style.display = 'flex';
        })
        .catch(error => {
            alert('Error loading product: ' + error.message);
        });
}

function saveProduct() {
    clearFormErrors();
    
    const data = {
        sku: productSku.value.trim(),
        name: productName.value.trim(),
        description: productDescription.value.trim() || null,
    };
    
    if (productActive.checked) {
        data.active = true;
    }
    
    const url = currentProductUuid 
        ? `/api/products/${currentProductUuid}/`
        : '/api/products/';
    
    const method = currentProductUuid ? 'PUT' : 'POST';
    
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
        
        closeProductModal();
        const message = currentProductUuid ? 'Product updated successfully' : 'Product created successfully';
        showNotification(message, 'success');
        loadProducts();
    })
    .catch(error => {
        showNotification('Error saving product: ' + error.message, 'error');
    });
}

function deleteProduct(uuid) {
    deleteProductUuid = uuid;
    deleteModal.style.display = 'flex';
}

function confirmDelete() {
    fetch(`/api/products/${deleteProductUuid}/`, {
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
        showNotification(data.message || 'Product deleted successfully', 'success');
        loadProducts();
    })
    .catch(error => {
        showNotification('Error deleting product: ' + error.message, 'error');
    });
}

function openBulkDeleteModal() {
    bulkDeleteModal.style.display = 'flex';
}

function confirmBulkDelete() {
    fetch('/api/products/bulk-delete/', {
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
        
        closeBulkDeleteModal();
        showNotification(data.message || 'All products deleted successfully', 'success');
        loadProducts();
    })
    .catch(error => {
        showNotification('Error deleting products: ' + error.message, 'error');
    });
}

function closeProductModal() {
    productModal.style.display = 'none';
    productForm.reset();
    currentProductUuid = null;
}

function closeDeleteModal() {
    deleteModal.style.display = 'none';
    deleteProductUuid = null;
}

function closeBulkDeleteModal() {
    bulkDeleteModal.style.display = 'none';
}

function clearFormErrors() {
    document.getElementById('skuError').textContent = '';
    document.getElementById('nameError').textContent = '';
    document.getElementById('descriptionError').textContent = '';
}

function displayFormErrors(errors) {
    if (errors.sku) {
        document.getElementById('skuError').textContent = errors.sku;
    }
    if (errors.name) {
        document.getElementById('nameError').textContent = errors.name;
    }
    if (errors.description) {
        document.getElementById('descriptionError').textContent = errors.description;
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

function showError(message) {
    showNotification('Error: ' + message, 'error');
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

window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.goToPage = goToPage;

loadProducts();

