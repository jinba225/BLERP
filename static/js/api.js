/**
 * API utility functions for BetterLaser ERP
 */

class ApiClient {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('token');
    }

    // Get CSRF token from cookies
    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Get default headers
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken()
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // Generic request method
    async request(url, options = {}) {
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(`${this.baseURL}${url}`, config);
            
            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.handleUnauthorized();
                throw new Error('Unauthorized');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Handle unauthorized access
    handleUnauthorized() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login/';
    }

    // GET request
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, {
            method: 'GET'
        });
    }

    // POST request
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // PATCH request
    async patch(url, data = {}) {
        return this.request(url, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }

    // Authentication methods
    async login(credentials) {
        const response = await fetch(`${this.baseURL}/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify(credentials)
        });

        const data = await response.json();

        if (response.ok) {
            this.token = data.token;
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
        }

        return { response, data };
    }

    async logout() {
        try {
            await this.post('/auth/logout/');
        } finally {
            this.token = null;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login/';
        }
    }

    async getUserInfo() {
        return this.get('/auth/user-info/');
    }

    async changePassword(passwordData) {
        return this.post('/auth/change-password/', passwordData);
    }

    // User management
    async getUsers(params = {}) {
        return this.get('/users/users/', params);
    }

    async createUser(userData) {
        return this.post('/users/users/', userData);
    }

    async updateUser(userId, userData) {
        return this.put(`/users/users/${userId}/`, userData);
    }

    async deleteUser(userId) {
        return this.delete(`/users/users/${userId}/`);
    }

    // Customer management
    async getCustomers(params = {}) {
        return this.get('/customers/customers/', params);
    }

    async createCustomer(customerData) {
        return this.post('/customers/customers/', customerData);
    }

    async updateCustomer(customerId, customerData) {
        return this.put(`/customers/customers/${customerId}/`, customerData);
    }

    async deleteCustomer(customerId) {
        return this.delete(`/customers/customers/${customerId}/`);
    }

    // Supplier management
    async getSuppliers(params = {}) {
        return this.get('/suppliers/suppliers/', params);
    }

    async createSupplier(supplierData) {
        return this.post('/suppliers/suppliers/', supplierData);
    }

    async updateSupplier(supplierId, supplierData) {
        return this.put(`/suppliers/suppliers/${supplierId}/`, supplierData);
    }

    async deleteSupplier(supplierId) {
        return this.delete(`/suppliers/suppliers/${supplierId}/`);
    }

    // Product management
    async getProducts(params = {}) {
        return this.get('/products/products/', params);
    }

    async createProduct(productData) {
        return this.post('/products/products/', productData);
    }

    async updateProduct(productId, productData) {
        return this.put(`/products/products/${productId}/`, productData);
    }

    async deleteProduct(productId) {
        return this.delete(`/products/products/${productId}/`);
    }

    // Sales management
    async getSalesOrders(params = {}) {
        return this.get('/sales/orders/', params);
    }

    async createSalesOrder(orderData) {
        return this.post('/sales/orders/', orderData);
    }

    async updateSalesOrder(orderId, orderData) {
        return this.put(`/sales/orders/${orderId}/`, orderData);
    }

    async deleteSalesOrder(orderId) {
        return this.delete(`/sales/orders/${orderId}/`);
    }

    // Purchase management
    async getPurchaseOrders(params = {}) {
        return this.get('/purchase/orders/', params);
    }

    async createPurchaseOrder(orderData) {
        return this.post('/purchase/orders/', orderData);
    }

    async updatePurchaseOrder(orderId, orderData) {
        return this.put(`/purchase/orders/${orderId}/`, orderData);
    }

    async deletePurchaseOrder(orderId) {
        return this.delete(`/purchase/orders/${orderId}/`);
    }

    // Inventory management
    async getInventoryStock(params = {}) {
        return this.get('/inventory/stock/', params);
    }

    async getWarehouses(params = {}) {
        return this.get('/inventory/warehouses/', params);
    }

    // Finance management
    async getAccounts(params = {}) {
        return this.get('/finance/accounts/', params);
    }

    async getJournals(params = {}) {
        return this.get('/finance/journals/', params);
    }

    async createJournal(journalData) {
        return this.post('/finance/journals/', journalData);
    }
}

// Create global API client instance
const api = new ApiClient();

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, api };
}