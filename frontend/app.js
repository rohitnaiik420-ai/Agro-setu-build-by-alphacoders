// AgroSetu AI - Client Application Logic

let allProducts = [];
let forecastChartInstance = null;
let leafletMapInstance = null;
let mapPolyline = null;
let mapMarkers = [];

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
  // Set default dates for product upload
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];
  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 4);
  const nextWeekStr = nextWeek.toISOString().split('T')[0];

  const harvestInput = document.getElementById('prod-harvest-date');
  const availInput = document.getElementById('prod-available-date');
  if (harvestInput) harvestInput.value = todayStr;
  if (availInput) availInput.value = nextWeekStr;

  // Restore preferred language if saved
  const savedLang = localStorage.getItem('agrosetu_lang') || 'en';
  changeLanguage(savedLang);

  // Load initial data
  loadStats();
  loadFarmersDropdown();
  fetchCorridors();
  loadProducts();
  loadShipments();
  loadVehicles();
  runForecast();
});

// ==================== TAB SWITCHING ====================

function switchTab(tabId) {
  // Hide all tab panes
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active-tab'));

  // Show selected tab pane
  const selectedPane = document.getElementById(`tab-content-${tabId}`);
  const selectedBtn = document.getElementById(`tab-btn-${tabId}`);

  if (selectedPane) selectedPane.classList.remove('hidden');
  if (selectedBtn) selectedBtn.classList.add('active-tab');

  // Trigger special initializations when switching
  if (tabId === 'forecast') {
    setTimeout(runForecast, 50);
  } else if (tabId === 'routing') {
    setTimeout(() => {
      initOrUpdateMap();
      runRouteOptimization();
    }, 100);
  } else if (tabId === 'logistics') {
    loadShipments();
    loadVehicles();
  } else if (tabId === 'buyer' || tabId === 'farmer') {
    loadProducts();
  }
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  const bgColor = type === 'success' ? 'bg-emerald-800' : (type === 'error' ? 'bg-rose-800' : 'bg-slate-800');
  const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-info');

  toast.className = `toast-msg flex items-center space-x-2 text-white px-4 py-3 rounded-xl shadow-xl border border-white/20 text-xs font-semibold ${bgColor}`;
  toast.innerHTML = `<i class="fa-solid ${icon} text-sm"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==================== STATS ====================

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    
    document.getElementById('kpi-farmers').innerText = data.total_farmers;
    document.getElementById('kpi-products').innerText = data.total_products;
    document.getElementById('kpi-orders').innerText = data.total_orders;
    document.getElementById('kpi-sales').innerText = `₹${data.total_sales_inr.toLocaleString('en-IN')}`;
    document.getElementById('kpi-vehicles').innerText = data.available_vehicles;
  } catch (err) {
    console.error("Error loading stats:", err);
  }
}

// ==================== MODULE 1 & 2: PRODUCTS & ORDERS ====================

async function loadProducts() {
  try {
    const res = await fetch('/api/products');
    if (!res.ok) return;
    allProducts = await res.json();
    renderFarmerInventory(allProducts);
    renderBuyerProducts(allProducts);
  } catch (err) {
    console.error("Error loading products:", err);
  }
}

function renderFarmerInventory(products) {
  const tbody = document.getElementById('farmer-inventory-table');
  if (!tbody) return;

  if (products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400">No produce listings found. Upload your first crop!</td></tr>`;
    return;
  }

  tbody.innerHTML = products.map(p => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="p-3">
        <div class="font-bold text-slate-800">${p.crop_name}</div>
        <div class="text-[11px] text-slate-500">${p.category}</div>
      </td>
      <td class="p-3">
        <div class="font-medium text-slate-800">${p.farmer_name || 'Farmer'}</div>
        <div class="text-[11px] text-emerald-700 font-semibold"><i class="fa-solid fa-location-dot mr-1"></i>${p.location}</div>
      </td>
      <td class="p-3">
        <span class="font-bold text-slate-900">${p.available_quantity_kg.toLocaleString()} kg</span>
        <span class="text-[11px] text-slate-400 block">of ${p.quantity_kg.toLocaleString()} kg</span>
      </td>
      <td class="p-3 font-bold text-emerald-700">₹${p.price_per_kg}/kg</td>
      <td class="p-3 text-[11px] text-slate-600">
        <div>Harvest: ${p.harvest_date}</div>
        <div>Ready: ${p.available_date}</div>
      </td>
      <td class="p-3">
        <span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold text-[11px]">${p.quality_grade}</span>
      </td>
    </tr>
  `).join('');
}

function renderBuyerProducts(products) {
  const grid = document.getElementById('buyer-product-grid');
  if (!grid) return;

  if (products.length === 0) {
    grid.innerHTML = `<div class="col-span-full text-center py-12 text-slate-400">No matching produce available for the selected filters.</div>`;
    return;
  }

  grid.innerHTML = products.map(p => {
    const isOutOfStock = p.available_quantity_kg <= 0;
    const defaultImg = "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&auto=format&fit=crop&q=60";
    const imgUrl = p.image_url && p.image_url.startsWith('http') ? p.image_url : defaultImg;

    return `
      <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition flex flex-col">
        <div class="h-40 w-full overflow-hidden relative bg-slate-100">
          <img src="${imgUrl}" alt="${p.crop_name}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" onerror="this.src='${defaultImg}'" />
          <span class="absolute top-2.5 left-2.5 bg-slate-900/80 backdrop-blur-sm text-white text-[11px] font-semibold px-2.5 py-0.5 rounded-full">
            ${p.category}
          </span>
          <span class="absolute bottom-2.5 right-2.5 bg-emerald-600 text-white text-xs font-black px-2.5 py-1 rounded-lg shadow">
            ₹${p.price_per_kg}/kg
          </span>
        </div>

        <div class="p-4 flex-1 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-[11px] text-slate-500 mb-1">
              <span><i class="fa-solid fa-location-dot text-emerald-600 mr-1"></i>${p.location}</span>
              <span class="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-semibold">${p.quality_grade}</span>
            </div>
            <h3 class="font-bold text-slate-900 text-sm mb-1">${p.crop_name}</h3>
            <p class="text-xs text-slate-500 line-clamp-2 mb-3">${p.description || 'Farm-fresh harvest direct from producer.'}</p>
          </div>

          <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
            <div class="text-xs">
              <span class="text-slate-500 block text-[10px]">Available Stock</span>
              <strong class="${isOutOfStock ? 'text-rose-600' : 'text-emerald-700'}">${p.available_quantity_kg.toLocaleString()} kg</strong>
            </div>
            <button onclick="openBuyModal(${p.id})" ${isOutOfStock ? 'disabled' : ''} class="${isOutOfStock ? 'bg-slate-200 text-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'} px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1">
              <i class="fa-solid fa-cart-plus"></i>
              <span>${isOutOfStock ? 'Sold Out' : 'Buy Now'}</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function applyFilters() {
  const search = document.getElementById('buyer-search-input').value.toLowerCase().trim();
  const category = document.getElementById('buyer-filter-category').value;
  const location = document.getElementById('buyer-filter-location').value;

  const filtered = allProducts.filter(p => {
    const matchSearch = !search || p.crop_name.toLowerCase().includes(search) || (p.description && p.description.toLowerCase().includes(search));
    const matchCat = category === 'All' || p.category.toLowerCase() === category.toLowerCase();
    const matchLoc = location === 'All' || p.location.toLowerCase().includes(location.toLowerCase());
    return matchSearch && matchCat && matchLoc;
  });

  renderBuyerProducts(filtered);
}

async function handleProductUpload(e) {
  e.preventDefault();
  const effectiveQty = getEffectiveQuantityKg();
  const payload = {
    farmer_id: parseInt(document.getElementById('prod-farmer-id').value),
    crop_name: document.getElementById('prod-crop-name').value.trim(),
    category: document.getElementById('prod-category').value,
    quantity_kg: effectiveQty,
    price_per_kg: parseFloat(document.getElementById('prod-price').value),
    location: document.getElementById('prod-location').value,
    harvest_date: document.getElementById('prod-harvest-date').value,
    available_date: document.getElementById('prod-available-date').value,
    quality_grade: document.getElementById('prod-grade').value,
    description: document.getElementById('prod-desc').value.trim(),
    image_url: document.getElementById('prod-img').value.trim()
  };

  try {
    const res = await fetch('/api/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "Failed to upload product", "error");
      return;
    }

    showToast(`"${payload.crop_name}" listed successfully on marketplace!`, "success");
    document.getElementById('product-upload-form').reset();
    loadProducts();
    loadStats();
  } catch (err) {
    showToast("Network error uploading product", "error");
  }
}

// ==================== BUY / ORDER MODAL ====================

let selectedProductForOrder = null;

function openBuyModal(productId) {
  const prod = allProducts.find(p => p.id === productId);
  if (!prod) return;

  selectedProductForOrder = prod;
  document.getElementById('order-product-id').value = prod.id;
  document.getElementById('modal-crop-name').innerText = prod.crop_name;
  document.getElementById('modal-farmer-info').innerText = `${prod.farmer_name || 'Farmer'} • ${prod.location}`;
  document.getElementById('modal-price-display').innerText = `₹${prod.price_per_kg}/kg`;
  document.getElementById('modal-stock-display').innerText = `${prod.available_quantity_kg.toLocaleString()} kg`;
  
  const qtyInput = document.getElementById('order-qty');
  qtyInput.max = prod.available_quantity_kg;
  qtyInput.value = Math.min(100, prod.available_quantity_kg);
  
  calculateOrderTotal();
  document.getElementById('buy-modal').classList.remove('hidden');
}

function closeBuyModal() {
  document.getElementById('buy-modal').classList.add('hidden');
  selectedProductForOrder = null;
}

function calculateOrderTotal() {
  if (!selectedProductForOrder) return;
  const qty = parseFloat(document.getElementById('order-qty').value) || 0;
  const total = qty * selectedProductForOrder.price_per_kg;
  document.getElementById('modal-total-display').innerText = `₹${total.toLocaleString('en-IN')}`;
}

async function handlePlaceOrder(e) {
  e.preventDefault();
  if (!selectedProductForOrder) return;

  const qty = parseFloat(document.getElementById('order-qty').value);
  const paymentMethod = document.querySelector('input[name="order-payment"]:checked')?.value || 'UPI';

  const payload = {
    product_id: selectedProductForOrder.id,
    buyer_name: document.getElementById('order-buyer-name').value.trim(),
    buyer_phone: document.getElementById('order-buyer-phone').value.trim(),
    delivery_city: document.getElementById('order-buyer-city').value,
    delivery_address: document.getElementById('order-buyer-address').value.trim(),
    quantity_kg: qty,
    payment_method: paymentMethod
  };

  try {
    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "Order failed", "error");
      return;
    }

    const data = await res.json();
    closeBuyModal();

    // Show Confirmation Receipt Modal
    document.getElementById('receipt-order-num').innerText = data.order_number;
    document.getElementById('receipt-tracking-num').innerText = data.tracking_number;
    document.getElementById('receipt-amount').innerText = `₹${data.total_amount.toLocaleString('en-IN')}`;
    document.getElementById('receipt-modal').classList.remove('hidden');

    showToast("Payment processed & shipment scheduled!", "success");
    loadProducts();
    loadStats();
    loadShipments();
  } catch (err) {
    showToast("Network error submitting order", "error");
  }
}

function closeReceiptModal() {
  document.getElementById('receipt-modal').classList.add('hidden');
}

// ==================== MODULE 3: LOGISTICS SUPPORT ====================

async function loadShipments() {
  try {
    const res = await fetch('/api/shipments');
    if (!res.ok) return;
    const shipments = await res.json();
    renderShipments(shipments);
  } catch (err) {
    console.error("Error loading shipments:", err);
  }
}

function renderShipments(shipments) {
  const container = document.getElementById('shipments-list');
  if (!container) return;

  if (shipments.length === 0) {
    container.innerHTML = `<div class="text-center py-6 text-slate-400 text-xs">No active shipments in transit.</div>`;
    return;
  }

  const statusProgress = {
    'Scheduled': 20,
    'Picked Up': 40,
    'At Collection Center': 60,
    'In Transit': 80,
    'Delivered': 100
  };

  container.innerHTML = shipments.map(s => {
    const pct = statusProgress[s.status] || 50;
    const isDelivered = s.status === 'Delivered';

    return `
      <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/50 hover:bg-slate-50 transition shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center space-x-2">
            <span class="font-bold text-slate-900 text-xs">${s.tracking_no}</span>
            <span class="text-[10px] bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">${s.cargo_description} (${s.weight_kg} kg)</span>
          </div>
          <span class="text-xs font-bold ${isDelivered ? 'text-emerald-700 bg-emerald-100' : 'text-blue-700 bg-blue-100'} px-2.5 py-0.5 rounded-full">
            ${s.status}
          </span>
        </div>

        <!-- Pipeline Route Display: Nashik -> Collection Center -> Pune Buyer -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-2 my-2.5 text-[11px] bg-white p-2.5 rounded-lg border border-slate-200/80">
          <div>
            <span class="text-slate-400 block text-[10px] font-semibold uppercase">1. Pickup (Farmer Farm)</span>
            <strong class="text-slate-800">${s.pickup_location}</strong>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] font-semibold uppercase">2. Agro Collection Center</span>
            <strong class="text-indigo-700">${s.collection_center}</strong>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] font-semibold uppercase">3. Delivery Destination</span>
            <strong class="text-emerald-800">${s.delivery_location}</strong>
          </div>
        </div>

        <!-- Progress bar -->
        <div class="w-full bg-slate-200 rounded-full h-2 my-3 overflow-hidden">
          <div class="bg-gradient-to-r from-blue-500 to-emerald-500 h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
        </div>

        <!-- Meta Details: Vehicle, ETA, Cost, Action -->
        <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-600 pt-2 border-t border-slate-200/60 gap-2">
          <div class="flex items-center space-x-3">
            <span><i class="fa-solid fa-truck text-slate-400 mr-1"></i>${s.vehicle_no || 'Assigned Van'}</span>
            <span><i class="fa-solid fa-user text-slate-400 mr-1"></i>${s.driver_name || 'Santosh'}</span>
            <span><i class="fa-solid fa-clock text-slate-400 mr-1"></i>ETA: <strong class="text-slate-800">${s.eta_timestamp || '4 Hours'}</strong></span>
            <span><i class="fa-solid fa-indian-rupee-sign text-slate-400 mr-1"></i>Cost: <strong class="text-emerald-700">₹${s.transport_cost}</strong></span>
          </div>

          ${!isDelivered ? `
            <div class="flex items-center space-x-1.5">
              <button onclick="advanceShipmentStatus(${s.id}, '${s.status}')" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-2.5 py-1 rounded text-[11px] transition">
                Advance Status ➔
              </button>
            </div>
          ` : '<span class="text-emerald-700 font-bold"><i class="fa-solid fa-check-double mr-1"></i>Completed</span>'}
        </div>
      </div>
    `;
  }).join('');
}

async function advanceShipmentStatus(shipmentId, currentStatus) {
  const steps = ['Scheduled', 'Picked Up', 'At Collection Center', 'In Transit', 'Delivered'];
  const nextIdx = steps.indexOf(currentStatus) + 1;
  if (nextIdx >= steps.length) return;

  const nextStatus = steps[nextIdx];

  try {
    const res = await fetch(`/api/shipments/${shipmentId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus })
    });

    if (res.ok) {
      showToast(`Shipment updated to: ${nextStatus}`);
      loadShipments();
      loadVehicles();
    }
  } catch (err) {
    showToast("Failed to update status", "error");
  }
}

async function loadVehicles() {
  try {
    const res = await fetch('/api/vehicles');
    if (!res.ok) return;
    const vehicles = await res.json();
    renderVehicles(vehicles);
  } catch (err) {
    console.error("Error loading vehicles:", err);
  }
}

function renderVehicles(vehicles) {
  const container = document.getElementById('vehicles-list');
  if (!container) return;

  container.innerHTML = vehicles.map(v => {
    const isAvail = v.status === 'Available';
    return `
      <div class="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between text-xs">
        <div>
          <div class="font-bold text-slate-800">${v.vehicle_type}</div>
          <div class="text-[11px] text-slate-500">${v.vehicle_no} • ${v.capacity_kg} kg cap • ₹${v.per_km_rate}/km</div>
          <div class="text-[11px] text-slate-400 mt-0.5"><i class="fa-solid fa-id-badge mr-1"></i>${v.driver_name} (${v.driver_phone})</div>
        </div>
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${isAvail ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
          ${v.status}
        </span>
      </div>
    `;
  }).join('');
}

function openNewShipmentModal() {
  document.getElementById('shipment-modal').classList.remove('hidden');
}

function closeShipmentModal() {
  document.getElementById('shipment-modal').classList.add('hidden');
}

async function handleCreateShipment(e) {
  e.preventDefault();
  const payload = {
    cargo_description: document.getElementById('ship-desc').value.trim(),
    weight_kg: parseFloat(document.getElementById('ship-weight').value),
    pickup_location: document.getElementById('ship-pickup').value.trim(),
    collection_center: document.getElementById('ship-collection').value.trim(),
    delivery_location: document.getElementById('ship-delivery').value.trim(),
    vehicle_id: parseInt(document.getElementById('ship-vehicle').value)
  };

  try {
    const res = await fetch('/api/shipments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Dispatch scheduled! Tracking: ${data.tracking_no}`, "success");
      closeShipmentModal();
      document.getElementById('shipment-form').reset();
      loadShipments();
      loadVehicles();
    }
  } catch (err) {
    showToast("Error scheduling dispatch", "error");
  }
}

// ==================== MODULE 4: AI DEMAND FORECASTING ====================

async function runForecast() {
  const crop = document.getElementById('fc-crop').value;
  const city = document.getElementById('fc-city').value;
  const season = document.getElementById('fc-season').value;
  const weather = document.getElementById('fc-weather').value;
  const festival = document.getElementById('fc-festival').value;
  const baseDemand = parseFloat(document.getElementById('fc-base').value) || 1000;

  const url = `/api/forecast?crop=${encodeURIComponent(crop)}&city=${encodeURIComponent(city)}&season=${encodeURIComponent(season)}&weather=${encodeURIComponent(weather)}&festival=${encodeURIComponent(festival)}&base_demand=${baseDemand}&horizon=7`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    renderForecastOutput(data);
  } catch (err) {
    console.error("Forecast fetch error:", err);
  }
}

function renderForecastOutput(data) {
  // Update Big Callout Banner
  document.getElementById('callout-current').innerText = `${data.current_demand_kg.toLocaleString()} kg`;
  document.getElementById('callout-forecast').innerText = `~${data.predicted_demand_kg.toLocaleString()} kg`;
  
  const badge = document.getElementById('callout-badge');
  badge.innerText = `${data.pct_change >= 0 ? '+' : ''}${data.pct_change}%`;
  badge.className = `text-xs px-2.5 py-1 rounded-lg font-bold border ${data.pct_change >= 0 ? 'bg-emerald-500/30 text-emerald-200 border-emerald-400/30' : 'bg-rose-500/30 text-rose-200 border-rose-400/30'}`;

  // Update Advisory Texts
  document.getElementById('advisory-hi').innerText = data.advisory.hindi;
  document.getElementById('advisory-window').innerText = data.advisory.recommended_dispatch_window;
  document.getElementById('advisory-price').innerText = `₹${data.advisory.recommended_target_price_per_kg}/kg`;

  // Factor Attribution
  const factorList = document.getElementById('factor-list');
  factorList.innerHTML = `
    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border border-slate-100">
      <span class="text-slate-600"><i class="fa-solid fa-cake-candles text-purple-500 mr-1"></i>Festival (${data.factors.festival.name}):</span>
      <strong class="text-emerald-700 font-bold">+${data.factors.festival.impact_kg} kg</strong>
    </div>
    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border border-slate-100">
      <span class="text-slate-600"><i class="fa-solid fa-cloud-sun-rain text-blue-500 mr-1"></i>Weather (${data.factors.weather.name}):</span>
      <strong class="text-emerald-700 font-bold">+${data.factors.weather.impact_kg} kg</strong>
    </div>
    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border border-slate-100">
      <span class="text-slate-600"><i class="fa-solid fa-calendar-day text-amber-500 mr-1"></i>Season (${data.factors.season.name}):</span>
      <strong class="text-emerald-700 font-bold">+${data.factors.season.impact_kg} kg</strong>
    </div>
    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border border-slate-100">
      <span class="text-slate-600"><i class="fa-solid fa-chart-line-up text-slate-500 mr-1"></i>Historical Baseline:</span>
      <strong class="text-slate-800 font-bold">${data.current_demand_kg} kg</strong>
    </div>
  `;

  // Chart Rendering
  renderForecastChart(data.chart_data, data.crop, data.city);
}

function renderForecastChart(chartData, crop, city) {
  const ctx = document.getElementById('forecastChart');
  if (!ctx) return;

  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  document.getElementById('chart-title').innerText = `${crop} Demand in ${city}: Historical vs AI Projected`;

  forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Historical Sales (Past 7 Days)',
          data: chartData.historical,
          borderColor: '#64748b',
          backgroundColor: 'rgba(100, 116, 139, 0.1)',
          borderWidth: 2,
          pointRadius: 4,
          tension: 0.3,
          spanGaps: false
        },
        {
          label: 'AI Forecast Trajectory (Next 7 Days)',
          data: chartData.forecast,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          borderWidth: 3,
          borderDash: [4, 4],
          pointRadius: 5,
          pointBackgroundColor: '#10b981',
          tension: 0.3,
          spanGaps: false,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 11, family: 'Inter' } }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${context.parsed.y} kg`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: '#f1f5f9' },
          ticks: { font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 } }
        }
      }
    }
  });
}

// ==================== MODULE 5: AI ROUTE OPTIMIZATION ====================

function initOrUpdateMap() {
  const mapDiv = document.getElementById('leaflet-map');
  if (!mapDiv) return;

  if (!leafletMapInstance) {
    // Centered over Western Maharashtra
    leafletMapInstance = L.map('leaflet-map').setView([18.9, 74.2], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(leafletMapInstance);
  } else {
    leafletMapInstance.invalidateSize();
  }
}

async function runRouteOptimization() {
  initOrUpdateMap();

  try {
    const payload = {};
    if (currentCustomWaypoints && currentCustomWaypoints.length > 0) {
      payload.waypoints = currentCustomWaypoints;
      if (currentCustomHub) payload.hub = currentCustomHub;
    }

    const res = await fetch('/api/route/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) return;
    const data = await res.json();
    renderRouteOptimization(data);
  } catch (err) {
    console.error("Routing error:", err);
  }
}

function renderRouteOptimization(data) {
  const s = data.summary;

  // Update Savings KPI cards
  document.getElementById('route-dist-saved').innerText = `${s.distance_saved_km} km`;
  document.getElementById('route-fuel-saved').innerText = `${s.fuel_saved_liters} L`;
  document.getElementById('route-cost-saved').innerText = `₹${s.cost_saved_inr.toLocaleString('en-IN')}`;
  document.getElementById('route-co2-saved').innerText = `${s.co2_saved_kg} kg`;

  // Update Comparison Table
  document.getElementById('table-unopt-dist').innerText = `${s.unoptimized_distance_km} km`;
  document.getElementById('table-unopt-fuel').innerText = `${s.unoptimized_fuel_liters} L`;
  document.getElementById('table-unopt-cost').innerText = `₹${s.unoptimized_cost_inr.toLocaleString('en-IN')}`;

  document.getElementById('table-opt-dist').innerText = `${s.optimized_distance_km} km`;
  document.getElementById('table-opt-fuel').innerText = `${s.optimized_fuel_liters} L`;
  document.getElementById('table-opt-cost').innerText = `₹${s.optimized_cost_inr.toLocaleString('en-IN')}`;
  document.getElementById('table-opt-eta').innerText = `~${s.estimated_total_hours} Hours total`;

  // Render Stop Sequence List
  const list = document.getElementById('route-stops-list');
  list.innerHTML = data.optimized_route.map(stop => `
    <div class="p-2.5 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start space-x-2">
      <div class="w-6 h-6 rounded-full ${stop.pickup_kg > 0 ? 'bg-emerald-700' : 'bg-blue-700'} text-white font-bold flex items-center justify-center text-xs flex-shrink-0">
        ${stop.step}
      </div>
      <div class="flex-1">
        <div class="flex items-center justify-between">
          <strong class="text-slate-800">${stop.location_name}</strong>
          <span class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-semibold">${stop.leg_km} km</span>
        </div>
        <div class="text-[11px] text-slate-500">${stop.farmer_label}: ${stop.farmer_name}</div>
        <div class="text-[10px] text-emerald-700 font-semibold mt-0.5">
          ${stop.pickup_kg > 0 ? `+${stop.pickup_kg} kg (${stop.produce}) • Cumulative: ${stop.cumulative_cargo_kg} kg` : `Final Hub Delivery • Total Cargo: ${stop.cumulative_cargo_kg} kg`}
        </div>
      </div>
    </div>
  `).join('');

  // Update Map Markers & Polyline
  if (leafletMapInstance) {
    // Clear old markers and polyline
    mapMarkers.forEach(m => leafletMapInstance.removeLayer(m));
    mapMarkers = [];
    if (mapPolyline) leafletMapInstance.removeLayer(mapPolyline);

    const latlngs = [];

    data.optimized_route.forEach(stop => {
      const isHub = stop.pickup_kg === 0;
      const markerHtml = `
        <div class="custom-leaflet-marker ${isHub ? 'marker-hub' : 'marker-pickup'}">
          ${stop.step}
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-pin',
        html: markerHtml,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([stop.lat, stop.lon], { icon: customIcon }).addTo(leafletMapInstance);
      marker.bindPopup(`
        <div class="text-xs">
          <strong>Stop ${stop.step}: ${stop.location_name}</strong><br/>
          <span>${stop.farmer_label} (${stop.farmer_name})</span><br/>
          <span class="text-emerald-700 font-bold">${stop.pickup_kg > 0 ? `Pickup: ${stop.pickup_kg} kg` : 'Drop: All Cargo'}</span>
        </div>
      `);
      mapMarkers.push(marker);
      latlngs.push([stop.lat, stop.lon]);
    });

    // Draw routing polyline
    mapPolyline = L.polyline(latlngs, {
      color: '#059669',
      weight: 5,
      opacity: 0.85,
      dashArray: '8, 8'
    }).addTo(leafletMapInstance);

    leafletMapInstance.fitBounds(mapPolyline.getBounds(), { padding: [40, 40] });
  }
}

// ==================== RESET DEMO DATA ====================

async function resetData() {
  if (!confirm("Reset database to clean initial sample state?")) return;
  try {
    const res = await fetch('/api/reset-data', { method: 'POST' });
    if (res.ok) {
      showToast("Database reset to initial demo state!");
      loadStats();
      loadFarmersDropdown();
      loadProducts();
      loadShipments();
      loadVehicles();
      runForecast();
      runRouteOptimization();
    }
  } catch (err) {
    showToast("Error resetting data", "error");
  }
}

// ==================== QUANTITY UNIT CONVERTER & QUICK CROPS ====================

function getEffectiveQuantityKg() {
  const qtyInput = document.getElementById('prod-qty');
  const rawQty = parseFloat(qtyInput ? qtyInput.value : 0) || 0;
  const unitSelect = document.getElementById('prod-unit-select');
  const unit = unitSelect ? unitSelect.value : 'kg';

  if (unit === 'quintal') return rawQty * 100;
  if (unit === 'tonne') return rawQty * 1000;
  if (unit === 'crate') return rawQty * 25;
  return rawQty;
}

function convertQtyUnit() {
  const kg = getEffectiveQuantityKg();
  const preview = document.getElementById('qty-in-kg-preview');
  if (preview) {
    preview.innerText = `Calculated: ${kg.toLocaleString()} kg`;
  }
}

function setQuickCrop(name, category) {
  const cropInput = document.getElementById('prod-crop-name');
  const catSelect = document.getElementById('prod-category');
  if (cropInput) cropInput.value = name;
  if (catSelect) catSelect.value = category;

  const priceInput = document.getElementById('prod-price');
  if (priceInput) {
    if (name === 'Tomato') priceInput.value = '38';
    else if (name === 'Onion') priceInput.value = '28';
    else if (name === 'Potato') priceInput.value = '24';
    else if (name === 'Wheat') priceInput.value = '26';
    else if (name === 'Soybean') priceInput.value = '46';
    else if (name === 'Cotton') priceInput.value = '68';
  }
}

// ==================== MULTI-LANGUAGE TRANSLATIONS (EN, HI, MR, PA) ====================

const TRANSLATIONS = {
  en: {
    dashboard_title: "AgroSetu AI • Problem Statement 26033",
    tagline: "Empowering Every Indian Farmer with Direct Markets & AI Routing",
    nav_overview: "System Overview",
    nav_farmer: "Farmer Portal",
    nav_buyer: "Direct Marketplace",
    nav_forecast: "AI Demand Forecast",
    nav_routing: "Route Optimizer",
    nav_logistics: "Fleet & Tracking",
    mobile_connect: "Mobile Access",
    farmer_select_label: "Farmer / FPO Name (किसान / उत्पादक संस्था)",
    register_farmer_btn: "+ Register New Farmer",
    crop_name_label: "Crop Name (फसल का नाम)",
    category_label: "Category (श्रेणी)",
    quantity_label: "Quantity (मात्रा)",
    price_label: "Price per kg (कीमत ₹/किग्रा)",
    location_label: "Location / Mandi (स्थान / मंडी)",
    quality_label: "Quality Grade (गुणवत्ता)",
    add_farm_stop_btn: "+ Add My Farm / Pickup Stop",
    select_corridor_label: "Agricultural Corridor (कृषि कॉरिडोर):",
    forecast_crop_label: "Crop (फसल)",
    forecast_city_label: "Location / City (स्थान / मंडी)",
    forecast_fest_label: "Festival (त्योहार)",
    forecast_season_label: "Season (मौसम)",
    farmer_reg_title: "Nationwide Farmer Registration",
    farmer_reg_sub: "Every Indian farmer / FPO can list produce directly",
    farmer_name: "Farmer Full Name (किसान का पूरा नाम) *",
    fpo_name: "FPO / Organization Name (संस्था का नाम)",
    state: "State (राज्य) *",
    district_city: "District / City (ज़िला / शहर) *",
    farmer_phone: "Mobile Number (फ़ोन नंबर) *",
    farmer_address: "Village / Farm Address (गाँव का पता)",
    submit_register: "Register Farmer Profile (किसान पंजीकृत करें)",
    add_stop_title: "Add Farm / Pickup Stop",
    add_stop_sub: "Include any farm in the AI route optimization",
    farm_name: "Farmer / Farm Label",
    city_name: "City / Mandi (शहर)",
    crop_produce: "Produce / Crop (फसल)",
    quantity_kg: "Pickup Weight (kg)",
    add_stop_btn: "Add to AI Optimization Route",
    mobile_title: "Connect Mobile / Any Device",
    mobile_sub: "Access AgroSetu live on your phone via local Wi-Fi",
    mobile_scan: "Scan QR Code on your Mobile Camera",
    mobile_copy: "Copy Link",
    mobile_tip: "Ensure your phone is connected to the same Wi-Fi or Mobile Hotspot."
  },
  hi: {
    dashboard_title: "एग्रोसेतु AI • समस्या विवरण 26033",
    tagline: "हर भारतीय किसान को सीधे बाज़ार और AI रूटिंग से जोड़ना",
    nav_overview: "सिस्टम सारांश",
    nav_farmer: "किसान पोर्टल",
    nav_buyer: "सीधा बाज़ार",
    nav_forecast: "AI मांग पूर्वानुमान",
    nav_routing: "रूट ऑप्टिमाइज़र",
    nav_logistics: "फ्लीट ट्रैकिंग",
    mobile_connect: "मोबाइल कनेक्ट",
    farmer_select_label: "किसान / FPO का नाम",
    register_farmer_btn: "+ नया किसान जोड़ें",
    crop_name_label: "फसल का नाम",
    category_label: "श्रेणी",
    quantity_label: "मात्रा",
    price_label: "कीमत ₹/किग्रा",
    location_label: "स्थान / मंडी",
    quality_label: "गुणवत्ता ग्रेड",
    add_farm_stop_btn: "+ मेरा खेत / स्टॉप जोड़ें",
    select_corridor_label: "कृषि कॉरिडोर:",
    forecast_crop_label: "फसल",
    forecast_city_label: "स्थान / मंडी",
    forecast_fest_label: "त्योहार",
    forecast_season_label: "मौसम",
    farmer_reg_title: "अखिल भारतीय किसान पंजीकरण",
    farmer_reg_sub: "भारत का कोई भी किसान या FPO अपनी उपज बेच सकता है",
    farmer_name: "किसान का पूरा नाम *",
    fpo_name: "FPO / समूह का नाम",
    state: "राज्य *",
    district_city: "ज़िला / शहर *",
    farmer_phone: "मोबाइल नंबर *",
    farmer_address: "गाँव / खेत का पता",
    submit_register: "किसान प्रोफाइल पंजीकृत करें",
    add_stop_title: "खेत / पिकअप स्टॉप जोड़ें",
    add_stop_sub: "AI मार्ग योजना में किसी भी खेत को शामिल करें",
    farm_name: "किसान / खेत का नाम",
    city_name: "शहर / मंडी",
    crop_produce: "उपज / फसल",
    quantity_kg: "वजन (किग्रा)",
    add_stop_btn: "AI मार्ग में जोड़ें",
    mobile_title: "मोबाइल / अन्य डिवाइस से कनेक्ट करें",
    mobile_sub: "अपने फोन पर लोकल वाई-फाई से एग्रोसेतु चलाएं",
    mobile_scan: "मोबाइल कैमरे से QR कोड स्कैन करें",
    mobile_copy: "लिंक कॉपी करें",
    mobile_tip: "सुनिश्चित करें कि फोन उसी वाई-फाई या हॉटस्पॉट से जुड़ा है।"
  },
  mr: {
    dashboard_title: "ऍग्रोसेतू AI • समस्या विवरण 26033",
    tagline: "प्रत्येक भारतीय शेतकऱ्याला थेट बाजारपेठ आणि AI मार्गाने जोडणे",
    nav_overview: "प्रणाली माहिती",
    nav_farmer: "शेतकरी पोर्टल",
    nav_buyer: "थेट खरेदी-विक्री",
    nav_forecast: "AI मागणी अंदाज",
    nav_routing: "मार्ग ऑप्टिमायझर",
    nav_logistics: "वाहतूक ट्रॅकिंग",
    mobile_connect: "मोबाईल प्रवेश",
    farmer_select_label: "शेतकरी / FPO चे नाव",
    register_farmer_btn: "+ नवीन शेतकरी जोडा",
    crop_name_label: "पिकाचे नाव",
    category_label: "प्रवर्ग",
    quantity_label: "प्रमाण",
    price_label: "दर ₹/किलो",
    location_label: "ठिकाण / बाजार समिती",
    quality_label: "गुणवत्ता श्रेणी",
    add_farm_stop_btn: "+ माझे शेत / थांबा जोडा",
    select_corridor_label: "कृषी कॉरिडॉर:",
    forecast_crop_label: "पीक",
    forecast_city_label: "स्थान / शहर",
    forecast_fest_label: "सण-उत्सव",
    forecast_season_label: "हंगाम",
    farmer_reg_title: "अखिल भारतीय शेतकरी नोंदणी",
    farmer_reg_sub: "महाराष्ट्रातील व भारतातील कोणताही शेतकरी थेट माल विकू शकतो",
    farmer_name: "शेतकऱ्याचे पूर्ण नाव *",
    fpo_name: "FPO / कंपनीचे नाव",
    state: "राज्य *",
    district_city: "जिल्हा / शहर *",
    farmer_phone: "मोबाईल नंबर *",
    farmer_address: "गाव / पत्ता",
    submit_register: "नोंदणी पूर्ण करा",
    add_stop_title: "शेत / संकलन थांबा जोडा",
    add_stop_sub: "AI मार्ग नियोजनात नवीन थांबा समाविष्ट करा",
    farm_name: "शेतकरी नाव",
    city_name: "शहर / गाव",
    crop_produce: "पीक",
    quantity_kg: "वजन (किलो)",
    add_stop_btn: "AI मार्गात समाविष्ट करा",
    mobile_title: "मोबाईलवर कनेक्ट करा",
    mobile_sub: "स्थानिक वाय-फाय द्वारे मोबाईलवर ऍग्रोसेतू वापरा",
    mobile_scan: "मोबाईल कॅमेऱ्याने QR कोड स्कॅन करा",
    mobile_copy: "लिंक कॉपी करा",
    mobile_tip: "आपला मोबाईल एकाच वाय-फाय किंवा हॉटस्पॉटशी जोडलेला असावा."
  },
  pa: {
    dashboard_title: "ਐਗਰੋਸੇਤੂ AI • ਸਮੱਸਿਆ ਬਿਆਨ 26033",
    tagline: "ਹਰ ਭਾਰਤੀ ਕਿਸਾਨ ਨੂੰ ਸਿੱਧੀਆਂ ਮੰਡੀਆਂ ਅਤੇ AI ਰੂਟਿੰਗ ਨਾਲ ਜੋੜਨਾ",
    nav_overview: "ਸਿਸਟਮ ਸੰਖੇਪ",
    nav_farmer: "ਕਿਸਾਨ ਪੋਰਟਲ",
    nav_buyer: "ਸਿੱਧੀ ਮੰਡੀ",
    nav_forecast: "AI ਮੰਗ ਪੂਰਵ ਅਨੁਮਾਨ",
    nav_routing: "ਰੂਟ ਓਪਟੀਮਾਈਜ਼ਰ",
    nav_logistics: "ਫਲੀਟ ਟਰੈਕਿੰਗ",
    mobile_connect: "ਮੋਬਾਈਲ ਕਨੈਕਟ",
    farmer_select_label: "ਕਿਸਾਨ / FPO ਦਾ ਨਾਂ",
    register_farmer_btn: "+ ਨਵਾਂ ਕਿਸਾਨ ਸ਼ਾਮਲ ਕਰੋ",
    crop_name_label: "ਫ਼ਸਲ ਦਾ ਨਾਂ",
    category_label: "ਸ਼੍ਰੇਣੀ",
    quantity_label: "ਮਾਤਰਾ",
    price_label: "ਰੇਟ ₹/ਕਿਲੋ",
    location_label: "ਟਿਕਾਣਾ / ਮੰਡੀ",
    quality_label: "ਗੁਣਵੱਤਾ ਗ੍ਰੇਡ",
    add_farm_stop_btn: "+ ਮੇਰਾ ਖੇਤ / ਸਟਾਪ ਸ਼ਾਮਲ ਕਰੋ",
    select_corridor_label: "ਖੇਤੀਬਾੜੀ ਕੋਰੀਡੋਰ:",
    forecast_crop_label: "ਫ਼ਸਲ",
    forecast_city_label: "ਸ਼ਹਿਰ / ਮੰਡੀ",
    forecast_fest_label: "ਤਿਉਹਾਰ",
    forecast_season_label: "ਮੌਸਮ / ਸੀਜ਼ਨ",
    farmer_reg_title: "ਕਿਸਾਨ ਰਜਿਸਟ੍ਰੇਸ਼ਨ",
    farmer_reg_sub: "ਪੰਜਾਬ ਅਤੇ ਪੂਰੇ ਭਾਰਤ ਦਾ ਕੋਈ ਵੀ ਕਿਸਾਨ ਆਪਣੀ ਫ਼ਸਲ ਵੇਚ ਸਕਦਾ ਹੈ",
    farmer_name: "ਕਿਸਾਨ ਦਾ ਪੂਰਾ ਨਾਂ *",
    fpo_name: "FPO / ਸੁਸਾਇਟੀ ਦਾ ਨਾਂ",
    state: "ਰਾਜ *",
    district_city: "ਜ਼ਿਲ੍ਹਾ / ਸ਼ਹਿਰ *",
    farmer_phone: "ਮੋਬਾਈਲ ਨੰਬਰ *",
    farmer_address: "ਪਿੰਡ ਦਾ ਪਤਾ",
    submit_register: "ਕਿਸਾਨ ਪ੍ਰੋਫਾਈਲ ਦਰਜ ਕਰੋ",
    add_stop_title: "ਖੇਤ / ਪਿਕਅੱਪ ਸਟਾਪ ਸ਼ਾਮਲ ਕਰੋ",
    add_stop_sub: "AI ਰੂਟ ਯੋਜਨਾ ਵਿੱਚ ਕੋਈ ਵੀ ਖੇਤ ਸ਼ਾਮਲ ਕਰੋ",
    farm_name: "ਕਿਸਾਨ / ਖੇਤ ਦਾ ਨਾਂ",
    city_name: "ਸ਼ਹਿਰ / ਮੰਡੀ",
    crop_produce: "ਫ਼ਸਲ",
    quantity_kg: "ਭਾਰ (ਕਿਲੋ)",
    add_stop_btn: "AI ਰੂਟ ਵਿੱਚ ਜੋੜੋ",
    mobile_title: "ਮੋਬਾਈਲ ਨਾਲ ਕਨੈਕਟ ਕਰੋ",
    mobile_sub: "ਵਾਈ-ਫਾਈ ਰਾਹੀਂ ਆਪਣੇ ਫ਼ੋਨ 'ਤੇ ਐਗਰੋਸੇਤੂ ਚਲਾਓ",
    mobile_scan: "QR ਕੋਡ ਸਕੈਨ ਕਰੋ",
    mobile_copy: "ਲਿੰਕ ਕਾਪੀ ਕਰੋ",
    mobile_tip: "ਯਕੀਨੀ ਬਣਾਓ ਕਿ ਫ਼ੋਨ ਉਸੇ ਵਾਈ-ਫਾਈ ਨਾਲ ਜੁੜਿਆ ਹੈ।"
  }
};

function changeLanguage(lang) {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.innerText = dict[key];
    }
  });
  const langSelect = document.getElementById('lang-select');
  if (langSelect) langSelect.value = lang;
  localStorage.setItem('agrosetu_lang', lang);
}

// ==================== CORRIDOR MANAGEMENT ====================

let currentCorridorKey = 'maharashtra';
let regionalCorridorsData = null;
let currentCustomWaypoints = null;
let currentCustomHub = null;

async function fetchCorridors() {
  try {
    const res = await fetch('/api/corridors');
    if (res.ok) {
      regionalCorridorsData = await res.json();
    }
  } catch (err) {
    console.error("Error fetching corridors:", err);
  }
}

async function changeCorridor(corridorKey) {
  currentCorridorKey = corridorKey;
  if (!regionalCorridorsData) {
    await fetchCorridors();
  }
  if (regionalCorridorsData && regionalCorridorsData.corridors && regionalCorridorsData.corridors[corridorKey]) {
    const c = regionalCorridorsData.corridors[corridorKey];
    currentCustomWaypoints = JSON.parse(JSON.stringify(c.waypoints));
    currentCustomHub = JSON.parse(JSON.stringify(c.hub));
  } else {
    currentCustomWaypoints = null;
    currentCustomHub = null;
  }
  runRouteOptimization();
}

function resetCorridorWaypoints() {
  const select = document.getElementById('route-corridor-select');
  const val = select ? select.value : 'maharashtra';
  changeCorridor(val);
  showToast("Corridor waypoints reset!");
}

// ==================== FARMER REGISTRATION MODAL ====================

function openFarmerRegisterModal() {
  const modal = document.getElementById('farmer-register-modal');
  if (modal) modal.classList.remove('hidden');
}

function closeFarmerRegisterModal() {
  const modal = document.getElementById('farmer-register-modal');
  if (modal) modal.classList.add('hidden');
}

async function loadFarmersDropdown() {
  try {
    const res = await fetch('/api/farmers');
    if (!res.ok) return;
    const farmers = await res.json();
    const select = document.getElementById('prod-farmer-id');
    if (!select) return;

    select.innerHTML = farmers.map(f => `
      <option value="${f.id}">${f.name} (${f.fpo_name || 'Independent'}) - ${f.city}, ${f.state}</option>
    `).join('');
  } catch (err) {
    console.error("Error loading farmers:", err);
  }
}

async function handleFarmerRegister(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('reg-farmer-name').value.trim(),
    fpo_name: document.getElementById('reg-farmer-fpo').value.trim() || 'Independent Farmer',
    state: document.getElementById('reg-farmer-state').value,
    city: document.getElementById('reg-farmer-city').value.trim(),
    phone: document.getElementById('reg-farmer-phone').value.trim(),
    address: document.getElementById('reg-farmer-address').value.trim()
  };

  try {
    const res = await fetch('/api/farmers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "Registration failed", "error");
      return;
    }

    const result = await res.json();
    showToast(`Farmer ${result.name} registered successfully!`, "success");
    closeFarmerRegisterModal();
    document.getElementById('farmer-register-form').reset();
    await loadFarmersDropdown();
    if (result.id) {
      document.getElementById('prod-farmer-id').value = result.id;
    }
    loadStats();
  } catch (err) {
    showToast("Network error registering farmer", "error");
  }
}

// ==================== MOBILE CONNECT MODAL ====================

async function openMobileConnectModal() {
  const modal = document.getElementById('mobile-connect-modal');
  if (modal) modal.classList.remove('hidden');

  try {
    const res = await fetch('/api/network-info');
    if (res.ok) {
      const info = await res.json();
      const mobileUrl = info.mobile_url;
      const input = document.getElementById('mobile-url-input');
      if (input) input.value = mobileUrl;
      const qrImg = document.getElementById('mobile-qr-img');
      if (qrImg) {
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(mobileUrl)}`;
      }
    }
  } catch (err) {
    console.error("Error loading network info:", err);
  }
}

function closeMobileConnectModal() {
  const modal = document.getElementById('mobile-connect-modal');
  if (modal) modal.classList.add('hidden');
}

function copyMobileUrl() {
  const input = document.getElementById('mobile-url-input');
  if (!input) return;
  input.select();
  navigator.clipboard.writeText(input.value).then(() => {
    showToast("Mobile link copied to clipboard!");
  }).catch(() => {
    document.execCommand('copy');
    showToast("Link copied!");
  });
}

// ==================== ADD WAYPOINT MODAL (CUSTOM FARM STOP) ====================

function openAddWaypointModal() {
  const modal = document.getElementById('add-waypoint-modal');
  if (modal) modal.classList.remove('hidden');
}

function closeAddWaypointModal() {
  const modal = document.getElementById('add-waypoint-modal');
  if (modal) modal.classList.add('hidden');
}

function handleAddWaypoint(e) {
  e.preventDefault();
  const farmerName = document.getElementById('wp-farmer-name').value.trim();
  const location = document.getElementById('wp-location').value.trim();
  const state = document.getElementById('wp-state').value.trim();
  const produce = document.getElementById('wp-produce').value.trim();
  const qty = parseFloat(document.getElementById('wp-qty').value) || 500;

  if (!currentCustomWaypoints) {
    if (regionalCorridorsData && regionalCorridorsData.corridors && regionalCorridorsData.corridors[currentCorridorKey]) {
      currentCustomWaypoints = JSON.parse(JSON.stringify(regionalCorridorsData.corridors[currentCorridorKey].waypoints));
      currentCustomHub = JSON.parse(JSON.stringify(regionalCorridorsData.corridors[currentCorridorKey].hub));
    } else {
      currentCustomWaypoints = [
        { label: "Farmer A", name: "Ramesh Patil", location: "Nashik", produce: "Pomegranates", pickup_kg: 1200 },
        { label: "Farmer B", name: "Sunita Shinde", location: "Sangamner", produce: "Tomatoes", pickup_kg: 800 },
        { label: "Farmer C", name: "Balasaheb Gadakh", location: "Ahmednagar", produce: "Onions", pickup_kg: 1500 },
        { label: "Farmer D", name: "Vitthalrao Kadam", location: "Pune", produce: "Green Chillies", pickup_kg: 600 },
        { label: "Farmer E", name: "Anand Bhosale", location: "Satara", produce: "Strawberries", pickup_kg: 500 }
      ];
    }
  }

  const newLabel = `Farmer ${String.fromCharCode(65 + currentCustomWaypoints.length)}`;
  currentCustomWaypoints.push({
    label: newLabel,
    name: farmerName,
    location: location,
    state: state,
    produce: produce,
    pickup_kg: qty
  });

  closeAddWaypointModal();
  document.getElementById('add-waypoint-form').reset();
  showToast(`Added ${farmerName} (${location}) to AI route!`, "success");
  runRouteOptimization();
}

