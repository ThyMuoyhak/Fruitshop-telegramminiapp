import { API_BASE_URL, KHR_EXCHANGE_RATE } from './config.js';

// Telegram WebApp Object
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.enableClosingConfirmation) tg.enableClosingConfirmation();
}

let products = [];
let categories = [];
let selectedCategoryId = 'all';
let searchQuery = '';
let cart = {}; // { productId: { product, quantity } }
let currentTxId = null;
let pollInterval = null;

// DOM Elements
const productGrid = document.getElementById('productGrid');
const categoryScroller = document.getElementById('categoryScroller');
const searchInput = document.getElementById('searchInput');
const cartFloatingBar = document.getElementById('cartFloatingBar');
const cartBadge = document.getElementById('cartBadge');
const cartTotalUSD = document.getElementById('cartTotalUSD');
const cartTotalKHR = document.getElementById('cartTotalKHR');

const drawerOverlay = document.getElementById('drawerOverlay');
const cartDrawer = document.getElementById('cartDrawer');
const paymentDrawer = document.getElementById('paymentDrawer');
const cartItemsList = document.getElementById('cartItemsList');
const drawerTotalUSD = document.getElementById('drawerTotalUSD');
const drawerTotalKHR = document.getElementById('drawerTotalKHR');

const custName = document.getElementById('custName');
const custPhone = document.getElementById('custPhone');
const custAddress = document.getElementById('custAddress');
const custNote = document.getElementById('custNote');
const checkoutBtn = document.getElementById('checkoutBtn');

const khqrImage = document.getElementById('khqrImage');
const payAmountUSD = document.getElementById('payAmountUSD');
const payAmountKHR = document.getElementById('payAmountKHR');
const abaDeepLink = document.getElementById('abaDeepLink');
const pollingBox = document.getElementById('pollingBox');
const paymentSuccessView = document.getElementById('paymentSuccessView');

// Populate user info from Telegram if available
if (tg?.initDataUnsafe?.user) {
  const u = tg.initDataUnsafe.user;
  custName.value = [u.first_name, u.last_name].filter(Boolean).join(' ') || u.username || '';
}

// 1. Fetch Store Data
async function loadData() {
  try {
    const [catRes, prodRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/categories`),
      fetch(`${API_BASE_URL}/api/products`)
    ]);

    categories = await catRes.json();
    products = await prodRes.json();

    renderCategories();
    renderProducts();
  } catch (err) {
    console.error('Failed to load store data:', err);
    productGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #ef4444;">
        <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 8px;"></i>
        <p style="font-weight: 700;">មិនអាចទាញយកទិន្នន័យបានទេ</p>
        <p style="font-size: 12px; color: #94a3b8; margin-top: 4px;">សូមពិនិត្យមើលការតភ្ជាប់អ៊ីនធឺណិត ឬ API Server</p>
      </div>
    `;
  }
}

// 2. Render Categories
function renderCategories() {
  categoryScroller.innerHTML = `
    <button class="category-pill ${selectedCategoryId === 'all' ? 'active' : ''}" data-id="all">
      <span>✨ ទាំងអស់</span>
    </button>
  ` + categories.map(c => `
    <button class="category-pill ${selectedCategoryId === c.id.toString() ? 'active' : ''}" data-id="${c.id}">
      <span>${c.icon || '📁'} ${c.name_kh || c.name}</span>
    </button>
  `).join('');

  categoryScroller.querySelectorAll('.category-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedCategoryId = btn.getAttribute('data-id');
      renderCategories();
      renderProducts();
    });
  });
}

// 3. Render Products
function renderProducts() {
  const filtered = products.filter(p => {
    const matchesCat = selectedCategoryId === 'all' || p.category_id?.toString() === selectedCategoryId;
    const matchesQuery = !searchQuery || 
      (p.name_kh && p.name_kh.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (p.name_en && p.name_en.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (p.name && p.name.toLowerCase().includes(searchQuery.toLowerCase()));
    const isAvail = p.is_available !== false && p.is_active !== false;
    return matchesCat && matchesQuery && isAvail;
  });

  if (filtered.length === 0) {
    productGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px 16px; color: var(--text-muted);">
        <div style="font-size: 40px; margin-bottom: 8px;">🔍</div>
        <p style="font-weight: 700; color: #fff;">រកមិនឃើញទំនិញទេ</p>
        <p style="font-size: 12px; margin-top: 4px;">សូមសាកល្បងពាក្យគន្លឹះ ឬជ្រើសរើសប្រភេទផ្សេង</p>
      </div>
    `;
    return;
  }

  productGrid.innerHTML = filtered.map(p => {
    const inCart = cart[p.id]?.quantity || 0;
    const imgUrl = getFullImageUrl(p.image_url);
    const khrPrice = p.price_khr || Math.round((p.price_usd || p.price) * KHR_EXCHANGE_RATE);
    const usdPrice = (p.price_usd || p.price || 0).toFixed(2);

    return `
      <div class="product-card">
        <div class="product-image-box">
          <img src="${imgUrl}" alt="${p.name_en || p.name}" class="product-img" loading="lazy" />
        </div>
        <div class="product-info">
          <h4 class="product-name-kh">${p.name_kh || p.name}</h4>
          <p class="product-name-en">${p.name_en || p.name}</p>
          <div class="product-footer">
            <div class="price-box">
              <span class="price-usd">$${usdPrice}</span>
              <span class="price-khr">~ ${khrPrice.toLocaleString()} ៛</span>
            </div>
            ${inCart === 0 ? `
              <button class="add-btn" onclick="window.addToCart(${p.id})">
                <i class="fa-solid fa-plus"></i>
              </button>
            ` : `
              <div class="qty-pill">
                <button class="qty-btn" onclick="window.changeQty(${p.id}, -1)">-</button>
                <span class="qty-val">${inCart}</span>
                <button class="qty-btn" onclick="window.changeQty(${p.id}, 1)">+</button>
              </div>
            `}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function getFullImageUrl(url) {
  if (!url) return 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;
}

// 4. Cart Logic
window.addToCart = function(productId) {
  const prod = products.find(p => p.id === productId);
  if (!prod) return;
  if (!cart[productId]) {
    cart[productId] = { product: prod, quantity: 1 };
  } else {
    cart[productId].quantity += 1;
  }
  updateCartUI();
  renderProducts();
  if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
};

window.changeQty = function(productId, delta) {
  if (!cart[productId]) return;
  cart[productId].quantity += delta;
  if (cart[productId].quantity <= 0) {
    delete cart[productId];
  }
  updateCartUI();
  renderProducts();
  renderCartDrawerItems();
  if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
};

function updateCartUI() {
  const items = Object.values(cart);
  let totalCount = 0;
  let totalUSD = 0;

  items.forEach(i => {
    totalCount += i.quantity;
    totalUSD += i.quantity * (i.product.price_usd || i.product.price || 0);
  });

  const totalKHR = Math.round(totalUSD * KHR_EXCHANGE_RATE);

  cartBadge.innerText = totalCount;
  cartTotalUSD.innerText = `$${totalUSD.toFixed(2)}`;
  cartTotalKHR.innerText = `~ ${totalKHR.toLocaleString()} ៛`;

  drawerTotalUSD.innerText = `$${totalUSD.toFixed(2)}`;
  drawerTotalKHR.innerText = `~ ${totalKHR.toLocaleString()} ៛`;

  if (totalCount > 0) {
    cartFloatingBar.classList.add('show');
  } else {
    cartFloatingBar.classList.remove('show');
    closeAllDrawers();
  }
}

// 5. Drawer Controls
window.openCartDrawer = function() {
  renderCartDrawerItems();
  drawerOverlay.classList.add('active');
  cartDrawer.classList.add('active');
};

window.closeAllDrawers = function() {
  drawerOverlay.classList.remove('active');
  cartDrawer.classList.remove('active');
  paymentDrawer.classList.remove('active');
  if (pollInterval) clearInterval(pollInterval);
};

function renderCartDrawerItems() {
  const items = Object.values(cart);
  if (items.length === 0) {
    cartItemsList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">កន្ត្រកទទេ</div>`;
    return;
  }

  cartItemsList.innerHTML = items.map(i => {
    const p = i.product;
    const price = p.price_usd || p.price || 0;
    const sub = (i.quantity * price).toFixed(2);
    return `
      <div class="cart-item">
        <div class="cart-item-info">
          <div class="cart-item-title">${p.name_kh || p.name}</div>
          <div class="cart-item-sub">${i.quantity} &times; $${price.toFixed(2)} = $${sub}</div>
        </div>
        <div class="qty-pill">
          <button class="qty-btn" onclick="window.changeQty(${p.id}, -1)">-</button>
          <span class="qty-val">${i.quantity}</span>
          <button class="qty-btn" onclick="window.changeQty(${p.id}, 1)">+</button>
        </div>
      </div>
    `;
  }).join('');
}

// 6. Checkout & KHQR Payment
window.submitCheckout = async function() {
  const name = custName.value.trim();
  const phone = custPhone.value.trim();
  const address = custAddress.value.trim();
  const note = custNote.value.trim();

  if (!name || !phone || !address) {
    alert('សូមបំពេញឈ្មោះ លេខទូរស័ព្ទ និងអាសយដ្ឋានដឹកជញ្ជូន!');
    return;
  }

  const items = Object.values(cart).map(i => ({
    product_id: i.product.id,
    quantity: i.quantity
  }));

  const payload = {
    user_id: tg?.initDataUnsafe?.user?.id || 0,
    username: tg?.initDataUnsafe?.user?.username || '',
    name: name,
    phone: phone,
    address: address,
    note: note,
    items: items
  };

  try {
    checkoutBtn.disabled = true;
    checkoutBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>កំពុងបង្កើត KHQR...</span>`;

    const res = await fetch(`${API_BASE_URL}/api/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    checkoutBtn.disabled = false;
    checkoutBtn.innerHTML = `<i class="fa-solid fa-qrcode"></i> <span>បន្តទូទាត់ប្រាក់ KHQR / ABA Pay</span>`;

    if (!res.ok || !data.success) {
      alert('កំហុសក្នុងការបង្កើត QR Code: ' + (data.detail || data.error || 'Server Error'));
      return;
    }

    currentTxId = data.transaction_id;
    khqrImage.src = data.qr_url || `${API_BASE_URL}/api/qr-image?qr=${encodeURIComponent(data.qr)}`;
    payAmountUSD.innerText = `$${parseFloat(data.amount).toFixed(2)}`;
    payAmountKHR.innerText = `~ ${(Math.round(data.amount * KHR_EXCHANGE_RATE)).toLocaleString()} ៛`;

    abaDeepLink.href = data.checkout_url || '#';

    cartDrawer.classList.remove('active');
    paymentDrawer.classList.add('active');
    pollingBox.style.display = 'flex';
    paymentSuccessView.style.display = 'none';

    startPolling(currentTxId);
  } catch (err) {
    checkoutBtn.disabled = false;
    checkoutBtn.innerHTML = `<i class="fa-solid fa-qrcode"></i> <span>បន្តទូទាត់ប្រាក់ KHQR / ABA Pay</span>`;
    alert('មានបញ្ហាក្នុងការតភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេ។ សូមព្យាយាមម្ដងទៀត!');
  }
};

function startPolling(txId) {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/order/${txId}/status`);
      const data = await res.json();
      if (data.status === 'success' || data.order_status === 'PAID') {
        clearInterval(pollInterval);
        showPaymentSuccess();
      }
    } catch (e) {
      console.warn('Polling error:', e);
    }
  }, 3000);
}

function showPaymentSuccess() {
  pollingBox.style.display = 'none';
  paymentSuccessView.style.display = 'block';
  if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  cart = {};
  updateCartUI();
  renderProducts();
}

window.finishOrder = function() {
  closeAllDrawers();
  if (tg) tg.close();
};

// Search listener
searchInput.addEventListener('input', (e) => {
  searchQuery = e.target.value.trim();
  renderProducts();
});

// Load on start
loadData();
