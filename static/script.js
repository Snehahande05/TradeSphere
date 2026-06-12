const AppState = {
    users: [],
    stocks: [],
    orders: [],
    trades: [],
    auditLogs: [],
    dashboard: null,
    portfolio: null,
    profile: null,
    activeUserId: 1,
    portfolioChart: null
};

const dom = {
    loginPage: document.getElementById('login-page'),
    appContainer: document.getElementById('app-container'),
    loginForm: document.getElementById('login-form'),
    loginUserSelect: document.getElementById('login-user-select'),
    headerUserSelect: document.getElementById('header-user-select'),
    pageTitle: document.getElementById('page-title'),
    navCashBal: document.getElementById('nav-cash-bal'),
    navNetWorth: document.getElementById('nav-net-worth'),
    userDisplayName: document.getElementById('user-display-name'),
    userAvatarInitial: document.getElementById('user-avatar-initial'),
    menuItems: Array.from(document.querySelectorAll('.menu-item')),
    orderModal: document.getElementById('order-modal'),
    orderPlacementForm: document.getElementById('order-placement-form'),
    orderUserSelect: document.getElementById('order-user-select'),
    orderStockSelect: document.getElementById('order-stock-select'),
    orderQty: document.getElementById('order-qty'),
    orderPrice: document.getElementById('order-price'),
    toggleBuy: document.getElementById('toggle-buy'),
    toggleSell: document.getElementById('toggle-sell'),
    submitOrderBtn: document.getElementById('submit-order-btn'),
    estAvailCash: document.getElementById('est-avail-cash'),
    estAvailShares: document.getElementById('est-avail-shares'),
    estTotalCost: document.getElementById('est-total-cost'),
    estErrorMsg: document.getElementById('est-error-msg'),
    closeOrderModalBtn: document.getElementById('close-order-modal-btn'),
    cancelOrderModalBtn: document.getElementById('cancel-order-modal-btn'),
    marketGridContainer: document.getElementById('market-grid-container'),
    orderbookTableBody: document.getElementById('orderbook-table-body'),
    tradesTableBody: document.getElementById('trades-table-body'),
    dashActiveOrdersBody: document.getElementById('dash-active-orders-body'),
    portfolioTableBody: document.getElementById('portfolio-table-body'),
    portTotalCost: document.getElementById('port-total-cost'),
    portTotalValue: document.getElementById('port-total-value'),
    portTotalPnl: document.getElementById('port-total-pnl'),
    auditlogsTableBody: document.getElementById('auditlogs-table-body'),
    dashCashBalance: document.getElementById('dash-cash-balance'),
    dashPortfolioValue: document.getElementById('dash-portfolio-value'),
    dashUnrealizedPnl: document.getElementById('dash-unrealized-pnl'),
    dashUnrealizedPnlPct: document.getElementById('dash-unrealized-pnl-pct'),
    pendingBadge: document.getElementById('pending-badge'),
    themeToggleBtn: document.getElementById('theme-toggle-btn'),
    profileUsername: document.getElementById('profile-username'),
    profileEmailDisplay: document.getElementById('profile-email-display'),
    profileAvatarLg: document.getElementById('profile-avatar-lg'),
    profileUserId: document.getElementById('profile-user-id'),
    profileBalance: document.getElementById('profile-balance'),
    profileLastLogin: document.getElementById('profile-last-login'),
    profileEmail: document.getElementById('profile-email'),
    profileSettingsForm: document.getElementById('profile-settings-form'),
    prefTradeAlerts: document.getElementById('pref-trade-alerts'),
    prefPortfolioUpdates: document.getElementById('pref-portfolio-updates'),
    profileMessage: document.getElementById('profile-message'),
    changePasswordForm: document.getElementById('change-password-form'),
    currentPassword: document.getElementById('current-password'),
    newPassword: document.getElementById('new-password'),
    confirmPassword: document.getElementById('confirm-password'),
    passwordMessage: document.getElementById('password-message'),
    profileLogoutBtn: document.getElementById('profile-logout-btn'),
    architectureBtn: document.getElementById('btn-show-architecture'),
    architectureModal: document.getElementById('architecture-modal'),
    closeArchModalBtn: document.getElementById('close-arch-modal-btn'),
    closeArchBtn: document.getElementById('close-arch-btn'),
    notificationTrigger: document.getElementById('notification-trigger'),
    notificationBox: document.getElementById('notification-box'),
    notificationsList: document.getElementById('notifications-list'),
    bellDot: document.querySelector('.bell-dot'),
    clearNotifications: document.getElementById('clear-notifications')
};

function showElement(el) {
    if (!el) return;
    el.classList.remove('hidden');
}

function hideElement(el) {
    if (!el) return;
    el.classList.add('hidden');
}

function setActiveTab(tabId) {
    AppState.activeTab = tabId;
    dom.menuItems.forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.toggle('hidden', section.id !== `tab-${tabId}`);
    });
    dom.pageTitle.textContent = {
        dashboard: 'Dashboard',
        marketwatch: 'Market Watch',
        orderbook: 'Order Book',
        trades: 'Executed Trades',
        portfolio: 'Portfolio',
        auditlogs: 'Audit Logs',
        profile: 'Profile Settings'
    }[tabId] || 'TradeSphere';
    if (tabId === 'dashboard') renderDashboard();
    if (tabId === 'marketwatch') renderMarketWatch();
    if (tabId === 'orderbook') renderOrderBook();
    if (tabId === 'trades') renderTrades();
    if (tabId === 'portfolio') renderPortfolio();
    if (tabId === 'auditlogs') renderAuditLogs();
    if (tabId === 'profile') renderProfile();
}

function formatRupee(value) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value);
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
}

function showOrderError(message) {
    if (!dom.estErrorMsg) return;
    dom.estErrorMsg.querySelector('span').textContent = message;
    dom.estErrorMsg.classList.remove('hidden');
}

function clearOrderError() {
    if (!dom.estErrorMsg) return;
    dom.estErrorMsg.classList.add('hidden');
}

function fetchJson(path) {
    return fetch(path).then(res => {
        if (!res.ok) throw res;
        return res.json();
    });
}


async function loadUsers() {
    AppState.users = await fetchJson('/api/users');
}

async function loadStocks() {
    AppState.stocks = await fetchJson('/api/stocks');
}

async function loadOrders() {
    AppState.orders = await fetchJson('/api/orders');
}

async function loadTrades() {
    AppState.trades = await fetchJson('/api/trades');
}

async function loadAuditLogs() {
    AppState.auditLogs = await fetchJson('/api/audit-logs');
}

async function loadDashboard() {
    AppState.dashboard = await fetchJson('/api/dashboard');
}

async function loadPortfolio() {
    AppState.portfolio = await fetchJson(`/api/portfolio/${AppState.activeUserId}`);
}

async function loadProfile() {
    AppState.profile = await fetchJson(`/api/profile/${AppState.activeUserId}`);
}

async function refreshData() {
    try {
        await Promise.all([loadUsers(), loadStocks(), loadOrders(), loadTrades(), loadAuditLogs(), loadDashboard(), loadPortfolio(), loadProfile()]);
        renderHeader();
        renderDashboard();
        renderMarketWatch();
        renderOrderBook();
        renderTrades();
        renderPortfolio();
        renderAuditLogs();
        renderOrderFormOptions();
        renderNotifications();
    } catch (err) {
        console.error('Failed to load app data', err);
    }
}

function renderNotifications() {
    if (!dom.notificationsList) return;

    const latestLogs = AppState.auditLogs.slice(0, 5);

    if (!latestLogs.length) {
        dom.notificationsList.innerHTML =
            '<div class="empty-noti">No new notifications.</div>';

        if (dom.bellDot) dom.bellDot.classList.add('hidden');
        return;
    }

    dom.notificationsList.innerHTML = latestLogs.map(log => `
        <div class="noti-item">
            <strong>${log.action}</strong><br>
            ${log.details}
            <span class="time">${log.timestamp}</span>
        </div>
    `).join('');

    if (dom.bellDot) dom.bellDot.classList.remove('hidden');
}

function renderHeader() {
    const user = AppState.users.find(u => u.id === AppState.activeUserId) || { username: 'Guest', balance: 0 };
    dom.userDisplayName.textContent = user.username;
    dom.userAvatarInitial.textContent = user.username.charAt(0).toUpperCase();
    dom.navCashBal.textContent = formatRupee(user.balance || 0);
    const portfolioValue = AppState.portfolio && AppState.portfolio.total_value ? AppState.portfolio.total_value : 0;
    dom.navNetWorth.textContent = formatRupee((user.balance || 0) + portfolioValue);

    if (dom.loginUserSelect && dom.headerUserSelect) {
        renderUserSelectors();
    }
}

function renderUserSelectors() {
    const options = AppState.users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
    dom.loginUserSelect.innerHTML = options;
    dom.headerUserSelect.innerHTML = options;
    dom.loginUserSelect.value = AppState.activeUserId;
    dom.headerUserSelect.value = AppState.activeUserId;
}

function renderOrderFormOptions() {
    if (!dom.orderStockSelect || !dom.orderUserSelect) return;
    dom.orderStockSelect.innerHTML = AppState.stocks.map(stock => `<option value="${stock.symbol}">${stock.symbol} — ${stock.name}</option>`).join('');
    dom.orderUserSelect.innerHTML = AppState.users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
    dom.orderUserSelect.value = AppState.activeUserId;
    updateOrderEstimator();
}

function renderDashboard() {
    if (!AppState.dashboard) return;
    const balance = AppState.portfolio ? AppState.portfolio.balance : 0;
    const totalValue = AppState.portfolio ? AppState.portfolio.total_value : 0;
    const netWorth = balance + totalValue;
    const unrealized = totalValue - (AppState.portfolio ? AppState.portfolio.holdings.reduce((sum, item) => sum + item.total_cost, 0) : 0);
    const pnlPct = AppState.portfolio && AppState.portfolio.holdings.length ? ((unrealized / AppState.portfolio.holdings.reduce((sum, item) => sum + item.total_cost, 0)) * 100).toFixed(2) : '0.00';

    dom.dashCashBalance.textContent = formatRupee(balance);
    dom.dashPortfolioValue.textContent = formatRupee(totalValue);
    dom.dashUnrealizedPnl.textContent = formatRupee(unrealized);
    dom.dashUnrealizedPnlPct.textContent = `${pnlPct}% Overall Profit/Loss`;
    renderPendingBadge();
    renderPortfolioChart();
    renderDashboardActiveOrders();
}

function renderPendingBadge() {
    const count = AppState.orders.filter(order => ['PENDING', 'PARTIALLY_EXECUTED'].includes(order.status)).length;
    if (count > 0) {
        dom.pendingBadge.textContent = count;
        dom.pendingBadge.classList.remove('hidden');
    } else {
        dom.pendingBadge.classList.add('hidden');
    }
}

function renderMarketWatch() {
    if (!dom.marketGridContainer) return;
    dom.marketGridContainer.innerHTML = AppState.stocks.map(stock => {
        const change = stock.change ?? 0;
        const changeClass = change >= 0 ? 'gain' : 'loss';
        return `
            <div class="stock-card ${changeClass}">
                <div class="stock-card-top">
                    <div>
                        <div class="stock-symbol">${stock.symbol}</div>
                        <div class="stock-name" title="${stock.name}">${stock.name}</div>
                    </div>
                    <div class="stock-change-badge ${changeClass}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</div>
                </div>
                <div class="stock-card-price">
                    <span>₹${stock.currentPrice.toLocaleString('en-IN', {maximumFractionDigits: 2})}</span>
                </div>
                <div class="stock-card-actions">
                    <button class="btn btn-buy btn-sm" data-symbol="${stock.symbol}" data-action="BUY">BUY</button>
                    <button class="btn btn-sell btn-sm" data-symbol="${stock.symbol}" data-action="SELL">SELL</button>
                </div>
            </div>
        `;
    }).join('');
    dom.marketGridContainer.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', event => {
            const symbol = event.currentTarget.dataset.symbol;
            const action = event.currentTarget.dataset.action;
            openOrderModal(symbol, action);
        });
    });
}

function getStatusBadgeClass(status) {
    if (status === 'EXECUTED') return 'badge-success';
    if (status === 'PARTIALLY_EXECUTED') return 'badge-info';
    if (status === 'PENDING') return 'badge-warning';
    if (status === 'CANCELLED') return 'badge-secondary';
    return 'badge-secondary';
}

function renderOrderBook() {
    if (!dom.orderbookTableBody) return;
    if (!AppState.orders.length) {
        dom.orderbookTableBody.innerHTML = '<tr><td colspan="9" class="text-muted" style="text-align: center; padding: 40px 0;">No orders found.</td></tr>';
        return;
    }
    dom.orderbookTableBody.innerHTML = AppState.orders.map(order => `
        <tr>
            <td>${order.id}</td>
            <td>${order.user}</td>
            <td>${order.symbol}</td>
            <td><span class="badge ${order.type === 'BUY' ? 'badge-success' : 'badge-danger'}">${order.type}</span></td>
            <td>${order.remainingQty} / ${order.quantity}</td>
            <td>${formatRupee(order.price)}</td>
            <td><span class="badge ${getStatusBadgeClass(order.status)}">${order.status}</span></td>
            <td>${order.createdAt}</td>
            <td>-</td>
        </tr>
    `).join('');
}

function renderTrades() {
    if (!dom.tradesTableBody) return;
    if (!AppState.trades.length) {
        dom.tradesTableBody.innerHTML = '<tr><td colspan="8" class="text-muted" style="text-align: center; padding: 40px 0;">No trades executed yet.</td></tr>';
        return;
    }
    dom.tradesTableBody.innerHTML = AppState.trades.map(trade => `
        <tr>
            <td>${trade.id}</td>
            <td>${trade.buyerName}</td>
            <td>${trade.sellerName}</td>
            <td>${trade.symbol}</td>
            <td>${trade.quantity}</td>
            <td>${formatRupee(trade.price)}</td>
            <td>${formatRupee(trade.tradeValue)}</td>
            <td>${trade.executedAt}</td>
        </tr>
    `).join('');
}

function renderPortfolio() {
    if (!dom.portfolioTableBody) return;

    if (!AppState.portfolio || !AppState.portfolio.holdings.length) {
        dom.portfolioTableBody.innerHTML = '<tr><td colspan="10" class="text-muted" style="text-align: center; padding: 40px 0;">No active portfolio holdings.</td></tr>';

        dom.portTotalCost.textContent = formatRupee(0);
        dom.portTotalValue.textContent = formatRupee(0);
        dom.portTotalPnl.textContent = `${formatRupee(0)} (0.00%)`;

        return;
    }

    // Calculate portfolio summary values
    const totalCost = AppState.portfolio.holdings.reduce(
        (sum, row) => sum + Number(row.total_cost || 0),
        0
    );

    const totalValue = AppState.portfolio.holdings.reduce(
        (sum, row) => sum + Number(row.current_value || 0),
        0
    );

    const totalPnl = totalValue - totalCost;

    const pnlPct = totalCost > 0
        ? ((totalPnl / totalCost) * 100).toFixed(2)
        : "0.00";

    // Update portfolio summary cards
    dom.portTotalCost.textContent = formatRupee(totalCost);
    dom.portTotalValue.textContent = formatRupee(totalValue);
    dom.portTotalPnl.textContent = `${formatRupee(totalPnl)} (${pnlPct}%)`;

    // Update portfolio table
    dom.portfolioTableBody.innerHTML = AppState.portfolio.holdings.map(row => `
        <tr>
            <td>${AppState.portfolio.username}</td>
            <td>${row.symbol}</td>
            <td>${row.name}</td>
            <td>${row.quantity}</td>
            <td>${formatRupee(row.average_price)}</td>
            <td>${formatRupee(row.current_price)}</td>
            <td>${formatRupee(row.total_cost)}</td>
            <td>${formatRupee(row.current_value)}</td>
            <td>${formatRupee(row.pnl)}</td>
            <td>${row.pnl_pct.toFixed(2)}%</td>
        </tr>
    `).join('');
}

function renderAuditLogs() {
    if (!dom.auditlogsTableBody) return;
    if (!AppState.auditLogs.length) {
        dom.auditlogsTableBody.innerHTML = '<tr><td colspan="4" class="text-muted" style="text-align: center; padding: 40px 0;">No audit logs recorded.</td></tr>';
        return;
    }
    dom.auditlogsTableBody.innerHTML = AppState.auditLogs.map(log => `
        <tr>
            <td>${log.id}</td>
            <td>${log.action}</td>
            <td>${log.details}</td>
            <td>${log.timestamp}</td>
        </tr>
    `).join('');
}

function setFormMessage(element, message, type = 'success') {
    if (!element) return;
    element.textContent = message;
    element.classList.remove('hidden', 'success', 'error');
    element.classList.add(type);
}

function renderProfile() {
    const profile = AppState.profile || AppState.users.find(user => user.id === AppState.activeUserId);
    if (!profile) return;

    const username = profile.username || 'User';
    if (dom.profileUsername) dom.profileUsername.textContent = username;
    if (dom.profileEmailDisplay) dom.profileEmailDisplay.textContent = profile.email || `${username.toLowerCase()}@tradesphere.com`;
    if (dom.profileAvatarLg) dom.profileAvatarLg.textContent = username.charAt(0).toUpperCase();
    if (dom.profileUserId) dom.profileUserId.textContent = profile.id;
    if (dom.profileBalance) dom.profileBalance.textContent = formatRupee(profile.balance || 0);
    if (dom.profileLastLogin) dom.profileLastLogin.textContent = profile.last_login || 'Current Session';
    if (dom.profileEmail) dom.profileEmail.value = profile.email || '';
    if (dom.prefTradeAlerts) dom.prefTradeAlerts.checked = Boolean(profile.trade_alerts);
    if (dom.prefPortfolioUpdates) dom.prefPortfolioUpdates.checked = Boolean(profile.portfolio_updates);

    const preferredTheme = profile.theme_preference || (document.body.classList.contains('light-theme') ? 'light' : 'dark');
    document.querySelectorAll('input[name="profile-theme"]').forEach(input => {
        input.checked = input.value === preferredTheme;
    });
}

async function handleProfileUpdate(event) {
    event.preventDefault();
    const selectedTheme = document.querySelector('input[name="profile-theme"]:checked')?.value || 'dark';

    try {
        const response = await fetch(`/api/profile/${AppState.activeUserId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: dom.profileEmail.value,
                trade_alerts: dom.prefTradeAlerts.checked,
                portfolio_updates: dom.prefPortfolioUpdates.checked,
                theme_preference: selectedTheme
            })
        });
        const result = await response.json();
        if (!response.ok) {
            setFormMessage(dom.profileMessage, result.message || 'Could not update profile.', 'error');
            return;
        }
        localStorage.setItem('tradesphere-theme', selectedTheme);
        applyTheme(selectedTheme);
        await refreshData();
        renderProfile();
        setFormMessage(dom.profileMessage, result.message || 'Profile updated successfully.', 'success');
    } catch (err) {
        setFormMessage(dom.profileMessage, 'Profile update failed. Make sure Flask is running.', 'error');
    }
}

async function handlePasswordChange(event) {
    event.preventDefault();
    try {
        const response = await fetch('/api/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: AppState.activeUserId,
                current_password: dom.currentPassword.value,
                new_password: dom.newPassword.value,
                confirm_password: dom.confirmPassword.value
            })
        });
        const result = await response.json();
        if (!response.ok) {
            setFormMessage(dom.passwordMessage, result.message || 'Password change failed.', 'error');
            return;
        }
        dom.changePasswordForm.reset();
        await refreshData();
        setFormMessage(dom.passwordMessage, result.message || 'Password changed successfully.', 'success');
    } catch (err) {
        setFormMessage(dom.passwordMessage, 'Password request failed. Make sure Flask is running.', 'error');
    }
}

function logoutToLogin() {
    dom.appContainer.classList.add('hidden');
    dom.loginPage.classList.remove('hidden');
    AppState.activeUserId = 1;
    if (dom.loginUserSelect) dom.loginUserSelect.value = '1';
    setActiveTab('dashboard');
}

function renderPortfolioChart() {
    const labels = ['Cash'];
    const data = [AppState.portfolio ? AppState.portfolio.balance : 0];
    const colors = ['#10b981'];

    if (AppState.portfolio && AppState.portfolio.holdings) {
        AppState.portfolio.holdings.forEach((holding, index) => {
            labels.push(holding.symbol);
            data.push(holding.current_value);
            colors.push(['#06b6d4', '#8b5cf6', '#f59e0b', '#ec4899', '#14b8a6', '#fb7185'][index % 6]);
        });
    }

    const ctx = document.getElementById('portfolioDistributionChart');
    if (!ctx) return;

    if (AppState.portfolioChart) {
        AppState.portfolioChart.data.labels = labels;
        AppState.portfolioChart.data.datasets[0].data = data;
        AppState.portfolioChart.data.datasets[0].backgroundColor = colors;
        AppState.portfolioChart.update();
        return;
    }

    AppState.portfolioChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data, backgroundColor: colors, borderWidth: 0 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#e2e8f0' } }
            }
        }
    });
}

function openOrderModal(symbol = '', action = 'BUY') {
    if (!dom.orderModal) return;
    dom.orderStockSelect.value = symbol || (AppState.stocks[0] && AppState.stocks[0].symbol) || '';
    dom.orderUserSelect.value = AppState.activeUserId;
    dom.orderQty.value = 1;
    const stock = AppState.stocks.find(s => s.symbol === dom.orderStockSelect.value);
    dom.orderPrice.value = stock ? stock.currentPrice.toFixed(2) : '0.01';
    dom.toggleBuy.checked = action === 'BUY';
    dom.toggleSell.checked = action === 'SELL';
    setOrderButtonText();
    updateOrderEstimator();
    showElement(dom.orderModal);
}

function closeOrderModal() {
    hideElement(dom.orderModal);
    clearOrderError();
}

function setOrderButtonText() {
    const action = dom.toggleSell.checked ? 'SELL' : 'BUY';
    dom.submitOrderBtn.textContent = `Place ${action} Order`;
    dom.submitOrderBtn.classList.toggle('btn-buy', action === 'BUY');
    dom.submitOrderBtn.classList.toggle('btn-sell', action === 'SELL');
}

function getSelectedUserBalance() {
    const userId = parseInt(dom.orderUserSelect.value, 10);
    const user = AppState.users.find(u => u.id === userId);
    return user ? user.balance : 0;
}

function getSelectedUserHoldings(symbol) {
    if (!AppState.portfolio || !AppState.portfolio.holdings) return 0;
    const holding = AppState.portfolio.holdings.find(item => item.symbol === symbol && item.symbol);
    return holding ? holding.quantity : 0;
}

function updateOrderEstimator() {
    clearOrderError();
    const symbol = dom.orderStockSelect.value;
    const qty = Number(dom.orderQty.value) || 0;
    const price = Number(dom.orderPrice.value) || 0;
    const action = dom.toggleSell.checked ? 'SELL' : 'BUY';
    const totalCost = qty * price;
    const availCash = getSelectedUserBalance();
    const availShares = getSelectedUserHoldings(symbol);

    dom.estAvailCash.textContent = formatRupee(availCash);
    dom.estAvailShares.textContent = `${availShares} shares`;
    dom.estTotalCost.textContent = formatRupee(totalCost);

    if (qty <= 0) {
        showOrderError('Quantity must be greater than 0.');
        return;
    }
    if (price <= 0) {
        showOrderError('Price must be greater than 0.');
        return;
    }
    if (action === 'BUY' && totalCost > availCash) {
        showOrderError('Insufficient balance for this buy order.');
    }
    if (action === 'SELL' && qty > availShares) {
        showOrderError('Insufficient stock holdings for this sell order.');
    }
}

async function handleOrderPlacement(event) {
    event.preventDefault();
    clearOrderError();
    const order = {
        user_id: Number(dom.orderUserSelect.value),
        symbol: dom.orderStockSelect.value,
        order_type: dom.toggleSell.checked ? 'SELL' : 'BUY',
        quantity: Number(dom.orderQty.value),
        price: Number(dom.orderPrice.value)
    };

    try {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });
        const result = await response.json();
        if (!response.ok) {
            const message = result.message || 'Failed to place order.';
            showOrderError(message);
            return;
        }
        showNotification(result.message, 'success');
        closeOrderModal();
        await refreshData();
        setActiveTab('orderbook');
    } catch (err) {
        showOrderError('Order request failed. Make sure Flask is running and refresh the page.');
        console.error(err);
    }
}


function applyTheme(theme) {
    const isLight = theme === 'light';
    document.body.classList.toggle('light-theme', isLight);
    document.body.classList.toggle('dark-theme', !isLight);
    if (dom.themeToggleBtn) {
        const icon = dom.themeToggleBtn.querySelector('i');
        if (icon) {
            icon.className = isLight ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
        dom.themeToggleBtn.title = isLight ? 'Switch to dark mode' : 'Switch to light mode';
    }
    if (AppState.portfolioChart) {
        AppState.portfolioChart.options.plugins.legend.labels.color = isLight ? '#0f172a' : '#e2e8f0';
        AppState.portfolioChart.update();
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem('tradesphere-theme') || 'dark';
    applyTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
    const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('tradesphere-theme', nextTheme);
    applyTheme(nextTheme);
}


function openArchitectureModal() {
    showElement(dom.architectureModal);
}

function closeArchitectureModal() {
    hideElement(dom.architectureModal);
}

function attachEvents() {
    dom.themeToggleBtn?.addEventListener('click', toggleTheme);
    document.getElementById('logout-btn')?.addEventListener('click', logoutToLogin);
    dom.profileLogoutBtn?.addEventListener('click', logoutToLogin);
    dom.profileSettingsForm?.addEventListener('submit', handleProfileUpdate);
    dom.changePasswordForm?.addEventListener('submit', handlePasswordChange);
    dom.architectureBtn?.addEventListener('click', openArchitectureModal);
    dom.closeArchModalBtn?.addEventListener('click', closeArchitectureModal);
    dom.closeArchBtn?.addEventListener('click', closeArchitectureModal);
    dom.architectureModal?.addEventListener('click', event => {
        if (event.target === dom.architectureModal) {
            closeArchitectureModal();
        }
    });
    document.querySelectorAll('.btn-tab-switch').forEach(btn => {
        btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
    });
    dom.loginForm.addEventListener('submit', event => {
        event.preventDefault();
        AppState.activeUserId = Number(dom.loginUserSelect.value);
        dom.loginPage.classList.add('hidden');
        dom.appContainer.classList.remove('hidden');
        refreshData();
    });

    dom.headerUserSelect.addEventListener('change', event => {
        AppState.activeUserId = Number(event.target.value);
        refreshData();
    });

    dom.menuItems.forEach(item => {
        item.addEventListener('click', event => {
            event.preventDefault();
            setActiveTab(item.dataset.tab);
        });
    });

    dom.notificationTrigger?.addEventListener('click', (event) => {
    event.stopPropagation();
    dom.notificationBox.classList.toggle('hidden');
    });

dom.clearNotifications?.addEventListener('click', (event) => {
    event.stopPropagation();
    dom.notificationsList.innerHTML =
        '<div class="empty-noti">No new notifications.</div>';
    dom.bellDot?.classList.add('hidden');
    });

document.addEventListener('click', () => {
    dom.notificationBox?.classList.add('hidden');
   });

    document.getElementById('action-buy-stock')?.addEventListener('click', () => openOrderModal(AppState.stocks[0]?.symbol, 'BUY'));
    document.getElementById('action-sell-stock')?.addEventListener('click', () => openOrderModal(AppState.stocks[0]?.symbol, 'SELL'));
    document.getElementById('action-view-holdings')?.addEventListener('click', () => setActiveTab('portfolio'));
    dom.closeOrderModalBtn.addEventListener('click', closeOrderModal);
    dom.cancelOrderModalBtn.addEventListener('click', closeOrderModal);
    dom.orderPlacementForm.addEventListener('submit', handleOrderPlacement);
    dom.orderStockSelect.addEventListener('change', updateOrderEstimator);
    dom.orderQty.addEventListener('input', updateOrderEstimator);
    dom.orderPrice.addEventListener('input', updateOrderEstimator);
    dom.orderUserSelect.addEventListener('change', updateOrderEstimator);
    dom.toggleBuy.addEventListener('change', () => { setOrderButtonText(); updateOrderEstimator(); });
    dom.toggleSell.addEventListener('change', () => { setOrderButtonText(); updateOrderEstimator(); });
}

function renderDashboardActiveOrders() {
    if (!dom.dashActiveOrdersBody) return;

    const activeOrders = AppState.orders.filter(order =>
        ['PENDING', 'PARTIALLY_EXECUTED'].includes(order.status)
    );

    if (!activeOrders.length) {
        dom.dashActiveOrdersBody.innerHTML =
            '<tr><td colspan="6" class="text-muted" style="text-align:center; padding:30px 0;">No active orders.</td></tr>';
        return;
    }

    dom.dashActiveOrdersBody.innerHTML = activeOrders.slice(0, 5).map(order => `
        <tr>
            <td>${order.symbol}</td>
            <td>
                <span class="badge ${order.type === 'BUY' ? 'badge-success' : 'badge-danger'}">
                    ${order.type}
                </span>
            </td>
            <td>${order.remainingQty || order.quantity}</td>
            <td>${formatRupee(order.price)}</td>
            <td>
                <span class="badge ${order.status === 'PENDING' ? 'badge-warning' : 'badge-info'}">
                    ${order.status}
                </span>
            </td>
            <td>-</td>
        </tr>
    `).join('');
}

function initApp() {
    initTheme();
    attachEvents();
    setActiveTab('dashboard');
    refreshData();
}

document.addEventListener('DOMContentLoaded', initApp);
