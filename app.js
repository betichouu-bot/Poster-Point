/**
 * Poster Point - Main Application
 * 
 * Features:
 * - Product catalog and filtering
 * - Cart management
 * - Category organization
 * - Price management
 * - UI interactions
 */

// Product configuration
const defaultCatalog = {
  // Poster categories with images
  'ANIME': [], 'ASTHETICS': [], 'DC': [], 
  'DEVOTIONAL': [], 'MARVEL': [], 'MOVIE POSTERS': [],
  // Split posters (triptychs) produced into outputs/SPLIT POSTERS
  'SPLIT POSTERS': [],
  // Sticker categories
  'FULLPAGE': [], 'SINGLE STICKERS': []
};

// Debug: Log categories loaded from manifest
console.debug('Default categories:', Object.keys(defaultCatalog));
if (window.imageCatalog) {
  console.debug('Manifest categories:', Object.keys(window.imageCatalog));
}

// Sync imageCatalog categories with actual directories
console.group('Catalog Validation');
try {
    // Ensure imageCatalog exists and is an object
    if (!window.imageCatalog || typeof window.imageCatalog !== 'object') {
        console.debug('No manifest loaded or invalid format, using default catalog');
        window.imageCatalog = { ...defaultCatalog };
    } else {
        console.debug('Checking manifest categories:', Object.keys(window.imageCatalog));
        // Create a safe copy to iterate over while modifying the original
        const categories = [...Object.keys(window.imageCatalog)];
        
        // Delete any empty or invalid categories
        categories.forEach(key => {
            const category = window.imageCatalog[key];
            if (!category || !Array.isArray(category)) {
                console.warn(`Invalid category removed (not an array): ${key}`);
                delete window.imageCatalog[key];
            } else if (category.length === 0) {
                console.warn(`Empty category removed: ${key}`);
                delete window.imageCatalog[key];
            } else {
                console.debug(`Valid category: ${key} (${category.length} items)`);
            }
        });
    }
} catch (error) {
    console.error('Error validating catalog:', error);
    window.imageCatalog = { ...defaultCatalog };
} finally {
    console.groupEnd();
}

// Get imageCatalog from window (set by images-manifest.js and images-manifest-extra.js)
const imageCatalog = window.imageCatalog || defaultCatalog;

// Debug: log catalog keys and counts so we can spot mismatches between folders and manifests
try{
  console.debug('imageCatalog summary:');
  if(imageCatalog && typeof imageCatalog === 'object'){
    console.table(Object.keys(imageCatalog).map(k=>({ category: k, count: (imageCatalog[k]||[]).length })));
    console.debug('Full imageCatalog:', imageCatalog);
  } else {
    console.debug('imageCatalog is not an object', imageCatalog);
  }
}catch(e){ console.debug('Error logging imageCatalog', e); }

// Log posterProducts after filtering
window.addEventListener('load', () => {
  console.debug('Available categories:', Object.keys(imageCatalog));
  console.debug('Filtered posterProducts:', posterProducts);
});

// Handle case normalization for category names if needed
const categoryMap = {
  'fullpage': 'FULLPAGE',
  'full page': 'FULLPAGE',
  'full_page': 'FULLPAGE'
};

// Product configuration
const basePrice = 39;  // Default A4 size price
const STICKER_A4_PRICE = 99;
const STICKER_A3_PRICE = 159;
// Make Split Posters a top-level type and remove Photoframes
const types = ['Posters', 'Split Posters', 'Bookmarks', 'Stickers'];
const fullPageKey = 'FULLPAGE';
const SHOW_INITIAL = 6;

// Application state
let posterProducts = []; // Will hold validated products
let posterCandidates = []; // Will hold all possible products before validation
let selectedType = 'Posters';
let selectedSubcat = null;
let searchTerm = '';
let showingAll = false;
let stickerProducts; // Will be initialized based on FULLPAGE images

// Helper functions
function normalizeKey(k) { 
    return String(k || '').toLowerCase().replace(/\s+/g,''); 
}

// Set initial type from URL if present
const urlParams = new URLSearchParams(window.location.search);
const preType = urlParams.get('type');
if (types.includes(preType)) {
    selectedType = preType;
}

// Initialize image catalog with default categories
if (!window.imageCatalog || typeof window.imageCatalog !== 'object') {
    window.imageCatalog = { ...defaultCatalog };
}

// Ensure all required categories exist and are valid arrays
Object.entries(defaultCatalog).forEach(([cat, _]) => {
    if (!window.imageCatalog[cat] || !Array.isArray(window.imageCatalog[cat])) {
        console.warn(`Initializing missing/invalid category: ${cat}`);
        window.imageCatalog[cat] = [];
    }
});

// Remove any categories that don't belong
Object.keys(window.imageCatalog).forEach(cat => {
    if (!defaultCatalog.hasOwnProperty(cat)) {
        console.warn(`Removing unexpected category: ${cat}`);
        delete window.imageCatalog[cat];
    }
});
// Helper to preload an image and resolve true if it loads, false on error/timeout
function preloadImage(url, timeout = 3000){
  return new Promise(resolve => {
    if(!url) return resolve(false);
    const img = new Image();
    let settled = false;
    const t = setTimeout(()=>{ if(!settled){ settled = true; img.onload = img.onerror = null; resolve(false); } }, timeout);
    img.onload = ()=>{ if(!settled){ settled = true; clearTimeout(t); resolve(true); } };
    img.onerror = ()=>{ if(!settled){ settled = true; clearTimeout(t); resolve(false); } };
    img.src = url;
    // In case the image is cached and complete already
    if(img.complete && !settled){ settled = true; clearTimeout(t); resolve(true); }
  });
}

// Generate placeholder products for other types
function createPlaceholderProducts(type, count, basePrice) {
  const items = [];
  // Use sticker pricing for sticker products
  if(type === 'Sticker') basePrice = 99;
  
  for(let i = 0; i < count; i++) {
    const paddedIndex = String(i+1).padStart(3, '0');
    items.push({
      id: `${type.toLowerCase()}-${paddedIndex}`,
      name: `${type} #${paddedIndex}`,
      price: basePrice,
      category: type,
      isPlaceholder: true,
      file: 'images/placeholder.jpg'
    });
  }
  return items;
}

// Helper to safely encode file paths
function encodeFilePath(path) {
  return path.split('/').map(part => encodeURIComponent(part)).join('/');
}

// Initialize sticker products array
stickerProducts = [];

// Add single stickers if they exist in the manifest
if (imageCatalog['SINGLE STICKERS'] && Array.isArray(imageCatalog['SINGLE STICKERS'])) {
  const singleStickers = imageCatalog['SINGLE STICKERS'].map((fname, idx) => {
    const paddedIndex = String(idx + 1).padStart(3, '0');
    const id = `single-sticker-${paddedIndex}`;
    const name = `Sticker #${paddedIndex}`;
    const encodedFilePath = encodeFilePath(`images/PINTEREST IMAGES/SINGLE STICKERS/${fname}`);
    return { 
      id, 
      name, 
      price: 9,  // Fixed price for single stickers
      category: 'Single Stickers',
      file: encodedFilePath 
    };
  });
  stickerProducts.push(...singleStickers);
} else {
  // Fallback to placeholders if no images found
  const singleStickers = Array.from({ length: 30 }, (_, idx) => {
    const paddedIndex = String(idx + 1).padStart(3, '0');
    return {
      id: `single-sticker-${paddedIndex}`,
      name: `Sticker #${paddedIndex}`,
      price: 9,
      category: 'Single Stickers',
      isPlaceholder: true,
      file: 'images/placeholder.jpg'
    };
  });
  stickerProducts.push(...singleStickers);
}

// Add FULLPAGE stickers if available
if (imageCatalog[fullPageKey] && Array.isArray(imageCatalog[fullPageKey])) {
  const fullpageStickers = imageCatalog[fullPageKey].map((fname, idx) => {
    const paddedIndex = String(idx + 1).padStart(3, '0');
    const id = `fullpage-sticker-${paddedIndex}`;
    const name = `FULLPAGE #${paddedIndex}`;
    const encodedFilePath = encodeFilePath(`images/PINTEREST IMAGES/FULLPAGE/${fname}`);
    return { 
      id, 
      name, 
      price: STICKER_A4_PRICE, 
      category: 'FULLPAGE', 
      file: encodedFilePath 
    };
  });
  stickerProducts.push(...fullpageStickers);
} else {
  // If no FULLPAGE images, add placeholders
  const fullpagePlaceholders = Array.from({ length: 10 }, (_, idx) => {
    const paddedIndex = String(idx + 1).padStart(3, '0');
    return {
      id: `fullpage-sticker-${paddedIndex}`,
      name: `FULLPAGE #${paddedIndex}`,
      price: STICKER_A4_PRICE,
      category: 'FULLPAGE',
      isPlaceholder: true,
      file: 'images/placeholder.jpg'
    };
  });
  stickerProducts.push(...fullpagePlaceholders);
}

// Bookmarks are ₹20 each
const bookmarkProducts = createPlaceholderProducts('Bookmark', 12, 20);
// Photoframes removed — no frameProducts needed

// Basic in-memory cart (no backend)
const cart = {};

function formatINR(n){ return '₹' + n.toFixed(0); }

// Size options and prices
const sizeOptions = [
  { id: 'A4', label: 'A4', price: 39 },  // Standard A4 price
  { id: 'A3', label: 'A3', price: 69 },
  { id: 'A5', label: 'A5', price: 25 },
  { id: 'Pocket', label: 'Pocket', price: 10 },
  { id: '4x6', label: '4*6 inch', price: 19 }
];

// Wire sidebar: populate types and subcategories
function initSidebar() {
    console.group('Initializing sidebar');
    try {
        const typeList = document.getElementById('type-list');
        const subcatList = document.getElementById('subcats');
        
        if (!typeList || !subcatList) {
            throw new Error('Could not find required elements: type-list and subcats');
        }
        
        console.debug('Found UI elements, initializing type list');
        typeList.innerHTML = '';
        
        // Add type options
        types.forEach(t => {
            const li = document.createElement('li');
            li.textContent = t;
            li.dataset.type = t;
            if (t === selectedType) {
                li.classList.add('active');
            }
            
            li.addEventListener('click', () => {
                console.debug('Type selected:', t);
                selectedType = t;
                selectedSubcat = null;
                Array.from(typeList.children).forEach(ch => ch.classList.remove('active'));
                li.classList.add('active');
                populateSubcats();
                applyFilters();
            });
            
            typeList.appendChild(li);
        });
        
        console.debug('Type list initialized with', types.length, 'options');
        populateSubcats();
        
    } catch (err) {
        console.error('Error initializing sidebar:', err);
    } finally {
        console.groupEnd();
    }
}

function populateSubcats(){
  const subcatList = document.getElementById('subcats');
  if(!subcatList) {
    console.error('Could not find subcats element');
    return;
  }
  
  // Clear previous categories
  subcatList.innerHTML = '';
  
  // Debug info
  console.debug('Populating subcats:');
  console.debug('- Selected type:', selectedType);
  console.debug('- Image catalog keys:', Object.keys(imageCatalog));
  console.debug('- Image catalog entries:', Object.entries(imageCatalog).map(([k,v]) => `${k}: ${v?.length || 0} images`));
  
  if(selectedType === 'Posters') {
    console.debug('Populating poster categories from:', Object.keys(imageCatalog));
    
    // Show all valid categories except FULLPAGE
    const categories = Object.keys(imageCatalog)
      .filter(cat => {
        // Skip sticker-only categories
        if (cat === fullPageKey || cat === 'SINGLE STICKERS') {
          console.debug(`Skipping sticker category: ${cat}`);
          return false;
        }
        // Skip split posters since they are a separate top-level type
        if (cat === 'SPLIT POSTERS') {
          console.debug('Skipping split posters (separate type):', cat);
          return false;
        }
        // Skip invalid categories
        if (!imageCatalog[cat] || !Array.isArray(imageCatalog[cat])) {
          console.debug(`Skipping invalid category: ${cat}`);
          return false;
        }
        // Skip empty categories
        if (imageCatalog[cat].length === 0) {
          console.debug(`Skipping empty category: ${cat}`);
          return false;
        }
        return true;
      })
      .sort();
    
    console.debug('Valid categories:', categories);
    
    // Only show categories that actually have images
    categories.forEach(catKey => {
      if (!imageCatalog[catKey]) {
        console.debug('Skipping category (not in catalog):', catKey);
        return;
      }
      if (!Array.isArray(imageCatalog[catKey]) || !imageCatalog[catKey].length) {
        console.debug('Skipping empty category:', catKey);
        return;
      }
      
      console.debug('Adding category:', catKey, 'with', imageCatalog[catKey].length, 'images');

      const li = document.createElement('li');
      li.textContent = catKey; // Display original category name
      li.dataset.cat = catKey;
      if(catKey === selectedSubcat) li.classList.add('active');
      li.addEventListener('click', ()=>{
        if(selectedSubcat === catKey){ 
          selectedSubcat = null; 
          li.classList.remove('active'); 
        } else { 
          selectedSubcat = catKey; 
          Array.from(subcatList.children).forEach(ch => ch.classList.remove('active')); 
          li.classList.add('active'); 
        }
        applyFilters();
      });
      subcatList.appendChild(li);
    });
  } else if(selectedType === 'Stickers') {
    // Show sticker options
    ['Single Stickers', 'FULLPAGE'].forEach(option => {
      const li = document.createElement('li');
      li.textContent = option;
      li.dataset.cat = option;
      if(option === selectedSubcat) li.classList.add('active');
      li.addEventListener('click', ()=>{
        if(selectedSubcat === option){ selectedSubcat = null; li.classList.remove('active'); }
        else{ selectedSubcat = option; Array.from(subcatList.children).forEach(ch=>ch.classList.remove('active')); li.classList.add('active'); }
        applyFilters();
      });
      subcatList.appendChild(li);
    });
  } else {
    // No subcategories for other types
    const li = document.createElement('li'); 
    li.textContent = 'No subcategories'; 
    li.style.color = 'var(--muted)'; 
    subcatList.appendChild(li);
  }
}

// Wire search input
const searchInput = document.getElementById('search-input');
if(searchInput){
  searchInput.addEventListener('input', (e)=>{ 
    searchTerm = e.target.value.trim().toLowerCase(); 
    applyFilters(); 
  });
}

// Compute filteredProducts from current state
function getFilteredProducts(){
  let res = [];
  
  // Select products based on type
  if(selectedType === 'Posters') {
    // Filter out sticker categories from poster products
    // Exclude FULLPAGE, SINGLE STICKERS and SPLIT POSTERS from the main Posters view
    res = posterProducts.filter(p => p.category !== fullPageKey && p.category !== 'SINGLE STICKERS' && String(p.category || '').toUpperCase() !== 'SPLIT POSTERS');
    if(selectedSubcat) {
      // Case-insensitive category matching
      res = res.filter(p => p.category && p.category.toUpperCase() === selectedSubcat.toUpperCase());
    }
  } else if(selectedType === 'Split Posters') {
    // Only show split poster products (triptychs)
    res = posterProducts.filter(p => p.category && p.category.toUpperCase() === 'SPLIT POSTERS');
  } else if(selectedType === 'Stickers') {
    // If a subcategory is selected, filter by it
    if(selectedSubcat) {
      res = stickerProducts.filter(p => p.category === selectedSubcat);
    } else {
      // No subcategory selected - show all stickers
      res = stickerProducts.slice();
    }
  } else if(selectedType === 'Bookmarks') {
    res = bookmarkProducts.slice();
  }
  }
  
  // Apply search filter if any
  if(searchTerm) {
    res = res.filter(p => p.name.toLowerCase().includes(searchTerm) || 
                         p.category.toLowerCase().includes(searchTerm));
  }
  
  return res;
}

// Render product cards with initial limit and a toggle to show more
const grid = document.getElementById('product-grid');

function applyFilters(){
  // Only reset showingAll when changing categories or search
  if (document.activeElement !== document.getElementById('toggle-btn')) {
    showingAll = false;
  }
  renderProducts();
  updateUI();
}

function renderProducts(){
  grid.innerHTML = '';
  const all = getFilteredProducts();
  if(all.length === 0){
    grid.innerHTML = '<div class="empty">No items found for this selection.</div>';
    const existingToggle = document.getElementById('show-toggle'); 
    if(existingToggle) existingToggle.remove();
    return;
  }
  
  const list = showingAll ? all : all.slice(0, SHOW_INITIAL);
  list.forEach(p=>{
    const card = document.createElement('div');
    card.className = 'card';
    
    // Size options: posters use global sizeOptions. Stickers have their own sizes/prices.
    let sizeHtml = '';
    if(selectedType === 'Posters') {
      // Show size options for posters with clear pricing
      sizeHtml = `
        <option value="A4" data-price="39" selected>A4 - ₹39</option>
        <option value="A3" data-price="69">A3 - ₹69</option>
        <option value="A5" data-price="25">A5 - ₹25</option>
        <option value="Pocket" data-price="10">Pocket - ₹10</option>
        <option value="4x6" data-price="19">4*6 inch - ₹19</option>
      `;
    }
    
    // Custom display based on product type
    // Determine if this is a full-page sticker to adjust layout
    const isFullPageSticker = (selectedType === 'Stickers' && selectedSubcat === 'FULLPAGE');
    let badge = '';
    if(selectedType === 'Posters') badge = `<div class="badge-a4">${sizeOptions[0].label}</div>`;
    if(isFullPageSticker) badge = `<div class="badge-a4">A4</div>`;
  let itemType = selectedType === 'Stickers' ? (selectedSubcat || 'Sticker')
        : selectedType === 'Bookmarks' ? 'Laminated bookmark'
        : selectedType === 'Split Posters' ? 'Split Poster'
        : 'Limited edition print';
    
    // For FULLPAGE stickers we want the image to 'zoom out' (contain) so the entire sheet is visible
    const thumbClass = isFullPageSticker || (p.category && p.category.toLowerCase().replace(/\s+/g,'')==='fullpage') ? 'thumb contain' : 'thumb';

    card.innerHTML = 
      '<div class="' + thumbClass + '" style="background:#f0f0f0;aspect-ratio:1;display:flex;align-items:center;justify-content:center">' +
        (p.isPlaceholder 
          ? '<div style="color:var(--muted);font-size:18px">' + selectedType + '</div>'
          : '<img src="' + encodeURI(p.file) + '" alt="' + escapeHtml(p.name) + '" loading="lazy">') +
      '</div>' +
      badge +
      '<div class="card-body">' +
        '<div class="product-name">' + escapeHtml(p.name) + '</div>' +
        '<div class="product-price">' + formatINR(p.price) + '</div>' +
        '<div class="muted">' + itemType + 
          (selectedType === 'Posters' ? ' • <span class="size-label">A4</span>' : '') +
        '</div>' +
        '<div class="controls">' +
          (selectedType === 'Posters'
            ? '<div class="size-select-wrapper">' +
                '<label class="size-select-label">Select Size</label>' +
                '<select class="size-select" data-id="' + p.id + '">' + sizeHtml + '</select>' +
              '</div>'
            : '') +
          '<div class="controls-row">' +
            '<div class="qty">Qty: <span style="font-weight:900;margin-left:8px" id="' + p.id + '-display">0</span></div>' +
            '<button class="add" data-id="' + p.id + '">Buy now</button>' +
          '</div>' +
        '</div>' +
      '</div>';

    // Wire size change handler (posters and all stickers)
    if(selectedType === 'Posters' || selectedType === 'Stickers') {
      const sel = card.querySelector('.size-select');
      sel.addEventListener('change', (ev)=>{
        const opt = sel.selectedOptions[0];
        const price = Number(opt.dataset.price || 0);
        const priceEl = card.querySelector('.product-price');
        const sizeLabel = card.querySelector('.size-label');
        const badge = card.querySelector('.badge-a4');
        const newLabel = opt.textContent.split(' - ')[0];
        if(priceEl) priceEl.textContent = formatINR(price);
        if(sizeLabel) sizeLabel.textContent = newLabel;
        if(badge) badge.textContent = newLabel;
      });
    }

    grid.appendChild(card);
  });

  // Handle show more/less toggle
  const existingToggle = document.getElementById('show-toggle');
  if (existingToggle) {
    existingToggle.remove();
  }
  
  // Only show toggle if we have more items than initial limit
  if (all.length > SHOW_INITIAL) {
    const toggle = document.createElement('div');
    toggle.id = 'show-toggle';
    toggle.style.textAlign = 'center';
    toggle.style.marginTop = '24px';
    toggle.style.marginBottom = '24px';
    
    const btn = document.createElement('button');
    btn.className = 'checkout';
    btn.id = 'toggle-btn';
    btn.textContent = showingAll ? 'Show less' : 'Show more';
    btn.style.padding = '10px 20px';
    btn.style.fontSize = '14px';
    btn.style.fontWeight = '600';
    btn.style.background = '#333';
    btn.style.color = 'white';
    btn.style.border = 'none';
    btn.style.borderRadius = '8px';
    btn.style.cursor = 'pointer';
    
    btn.addEventListener('click', () => {
      showingAll = !showingAll;
      renderProducts();
      updateUI();
    });
    
    toggle.appendChild(btn);
    grid.parentNode.insertBefore(toggle, grid.nextSibling);
  }
}

// Add to cart / Buy now handler
document.addEventListener('click', (e)=>{
  const btn = e.target.closest('button.add');
  if(!btn) return;
  const id = btn.getAttribute('data-id');
  const card = btn.closest('.card');
  let size = 'A4', price = 39;
  const isFullPageSticker = selectedType === 'Stickers' && selectedSubcat === 'FULLPAGE';

  if(selectedType === 'Posters' && card){
    const sel = card.querySelector('.size-select');
    if(sel){ 
      size = sel.value; 
      price = Number(sel.selectedOptions[0].dataset.price || price); 
    }
  } else if(selectedType === 'Stickers') {
    // Fixed prices for stickers
    if(selectedSubcat === 'FULLPAGE') {
      price = STICKER_A4_PRICE;  // Default to A4 price for full page stickers
    } else {
      price = 9;  // Fixed price for single stickers
    }
  } else if (selectedType === 'Bookmarks') {
    // For bookmarks use the product's configured price
    const bp = bookmarkProducts.find(p => p.id === id);
    if (bp) price = Number(bp.price || price);
    size = '';
  }
  
  addToCart(id, 1, size, price);
  createToast('Added to cart', 600);
});

// Cart operations
function addToCart(id, qty=1, size='A4', priceOverride=null){
  let prod;
  if(selectedType === 'Posters') {
    prod = posterProducts.find(p => p.id === id);
  } else if(selectedType === 'Split Posters') {
    prod = posterProducts.find(p => p.id === id);
  } else if(selectedType === 'Stickers') {
    prod = stickerProducts.find(p => p.id === id);
  } else if(selectedType === 'Bookmarks') {
    prod = bookmarkProducts.find(p => p.id === id);
  }
  
  
  if(!prod) return;
  
  const key = id + '::' + size;
  if(!cart[key]){
    cart[key] = { 
      ...prod, 
      qty: 0, 
      size, 
      price: priceOverride !== null ? priceOverride : prod.price,
      id: key 
    };
  }
  cart[key].qty += qty;
  updateUI();
}

function removeFromCart(id){
  delete cart[id];
  updateUI();
}

function changeQty(id, newQty){
  if(newQty <= 0) { removeFromCart(id); return; }
  if(cart[id]) cart[id].qty = newQty;
  updateUI();
}

function clearCart(){
  for(const k in cart) delete cart[k];
  updateUI();
}

// Render cart UI
const cartBody = document.getElementById('cart-body');
const cartCount = document.getElementById('cart-count');
const cartTotal = document.getElementById('cart-total');

function updateUI(){
  // update product qty displays
  const displayEls = document.querySelectorAll('[id$="-display"]');
  displayEls.forEach(el => {
    const id = el.id.replace('-display', '');
    const sum = Object.values(cart)
      .filter(ci => String(ci.id).startsWith(id + '::') || String(ci.id) === id)
      .reduce((s,i) => s + (i.qty||0), 0);
    el.textContent = sum;
  });

  // render cart items
  const entries = Object.values(cart);
  if(entries.length === 0){
    cartBody.innerHTML = '<div class="empty">Your cart is empty — add some items!</div>';
    cartCount.textContent = '0 items';
    cartTotal.textContent = '₹0';
    return;
  }

  cartBody.innerHTML = '';
  let total = 0;
  
  entries.forEach(item => {
    total += item.price * item.qty;
    const row = document.createElement('div');
    row.className = 'cart-item';
    
    const itemContent = item.isPlaceholder
      ? '<div style="width:60px;height:60px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:var(--muted)">' + 
          item.category + 
        '</div>'
      : '<img src="' + encodeURI(item.file) + '" alt="' + escapeHtml(item.name) + '">';
    
    row.innerHTML = 
      itemContent +
      '<div class="meta">' +
        '<div class="name">' + escapeHtml(item.name) + 
          (item.size ? ' <span style="font-weight:600;color:var(--muted)">(' + item.size + ')</span>' : '') +
        '</div>' +
        '<div class="line">₹' + item.price + ' × ' + item.qty + ' = ₹' + (item.price * item.qty) + '</div>' +
      '</div>' +
      '<div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end">' +
        '<div style="display:flex;gap:6px">' +
          '<button class="decrease" data-id="' + item.id + '" title="Decrease">−</button>' +
          '<button class="increase" data-id="' + item.id + '" title="Increase">+</button>' +
        '</div>' +
        '<button style="background:transparent;border:none;color:var(--muted);font-size:12px;cursor:pointer" ' +
                'class="remove" data-id="' + item.id + '">Remove</button>' +
      '</div>';
    
    cartBody.appendChild(row);
  });
  
  const itemCount = entries.reduce((s,i) => s + i.qty, 0);
  cartCount.textContent = itemCount + ' items';
  cartTotal.textContent = '₹' + total;
  
  // update header cart count
  const navCount = document.getElementById('nav-cart-count');
  if(navCount) navCount.textContent = itemCount + ' items';
}

// Cart increase / decrease / remove handlers
cartBody.addEventListener('click', (e)=>{
  const inc = e.target.closest('button.increase');
  const dec = e.target.closest('button.decrease');
  const rem = e.target.closest('button.remove');
  if(inc){ const id = inc.dataset.id; changeQty(id, (cart[id]?.qty || 1) + 1); }
  if(dec){ const id = dec.dataset.id; changeQty(id, (cart[id]?.qty || 1) - 1); }
  if(rem){ const id = rem.dataset.id; removeFromCart(id); }
});

// Clear cart button
document.getElementById('clear-cart').addEventListener('click', clearCart);

// Send cart to WhatsApp
const sendBtn = document.getElementById('send-whatsapp');
if(sendBtn){
  sendBtn.addEventListener('click', ()=>{
    const entries = Object.values(cart);
    if(entries.length === 0){ 
      alert('Your cart is empty. Add items before sending.'); 
      return; 
    }
    
    const orderRef = 'PP-' + new Date().toISOString().replace(/[:.]/g, '').slice(0,15);
    let msg = 'Order Ref: ' + orderRef + '\nOrder from Poster Point:\n\n';
    
    entries.forEach(it => {
      msg += it.name + (it.size ? ' (' + it.size + ')' : '') + ' × ' + it.qty + '\n';
    });
    msg += '\nTotal: ' + cartTotal.textContent;
    
    const phone = '919395508081';
    const url = 'https://wa.me/' + phone + '?text=' + encodeURIComponent(msg);
    window.open(url, '_blank');
  });
}

// Cart drawer open/close
const navCartBtn = document.getElementById('nav-cart-btn');
if(navCartBtn){
  navCartBtn.addEventListener('click', ()=>{
    const drawer = document.getElementById('cart');
    if(!drawer) return;
    const isOpen = drawer.classList.contains('open');
    if(isOpen) closeCart(); else openCart();
  });
}

function openCart(){
  const drawer = document.getElementById('cart');
  if(!drawer) return;
  drawer.classList.add('open');
  updateNavIcon(true);
  updateUI();
}

function closeCart(){
  const drawer = document.getElementById('cart');
  if(!drawer) return;
  drawer.classList.remove('open');
  updateNavIcon(false);
}

function updateNavIcon(open){
  const nav = document.getElementById('nav-cart-btn');
  if(!nav) return;
  if(open){
    nav.innerHTML = '✕ <span style="margin-left:6px">Close</span>';
  } else {
    nav.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">' +
      '<path d="M3 3h2l.4 2M7 13h10l3-8H6.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />' +
      '</svg><span id="nav-cart-count" style="margin-left:6px">' + 
      (document.getElementById('cart-count')?.textContent || '0 items') + '</span>';
  }
}

// Cart close button in drawer
const cartClose = document.getElementById('cart-close-btn');
if(cartClose) cartClose.addEventListener('click', closeCart);

// Toast helper
function createToast(msg, ms = 700){
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed',
    right: '18px',
    bottom: '18px',
    background: 'rgba(0,0,0,0.8)',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '8px',
    zIndex: 9999,
    fontWeight: 700,
    opacity: '0',
    transition: 'opacity 160ms ease'
  });
  document.body.appendChild(t);
  void t.offsetWidth;
  t.style.opacity = '1';
  setTimeout(()=>{
    t.style.opacity = '0';
    setTimeout(()=> t.remove(), 180);
  }, ms);
}

// Utilities
function escapeHtml(s){ 
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); 
}

// Initialize the app when document is ready
const initializeApp = async () => {
    console.group('Application Initialization');
    try {
        console.debug('Starting app initialization');
        console.debug('Available categories:', Object.keys(imageCatalog));

        // Build poster candidates first
        console.group('Building Poster Candidates');
        try {
            Object.keys(imageCatalog).forEach(cat => {
                const images = imageCatalog[cat] || [];
                console.debug(`Processing category ${cat} with ${images.length} images`);
                
                images.forEach((fname, idx) => {
                    const id = `${cat.toLowerCase().replace(/\s+/g,'-')}-${idx+1}`;
                    const paddedIndex = String(idx+1).padStart(3, '0');
                    const title = cat === 'MOVIE POSTERS' ? 
                        'MP-' + paddedIndex : 
                        cat + ' #' + paddedIndex;
                    
                    const folderName = cat.toUpperCase();
                    const encodedCat = encodeURIComponent(folderName);
                    const encodedFname = encodeURIComponent(fname);
                    const filePath = `images/PINTEREST IMAGES/${encodedCat}/${encodedFname}`;
                    
                    posterCandidates.push({ 
                        id, 
                        file: filePath, 
                        name: title, 
                        price: basePrice, 
                        category: cat 
                    });
                });
            });
            console.debug('Built', posterCandidates.length, 'poster candidates');
        } finally {
            console.groupEnd();
        }

        // Validate and filter images
        console.group('Image Validation');
        try {
            console.debug('Total poster candidates:', posterCandidates.length);
            if (posterCandidates.length > 0) {
                console.debug('Sample candidate:', posterCandidates[0]);
            }
            
            // Load poster images
            const ok = await Promise.all(
                posterCandidates.map(c => preloadImage(c.file, 5000))
            );
            const before = posterCandidates.length;
            
            // Sort products by load success
            posterProducts = posterCandidates
                .map((product, index) => ({ ...product, didLoad: ok[index] }))
                .sort((a, b) => Number(b.didLoad) - Number(a.didLoad));
            
            const loadedCount = ok.filter(Boolean).length;
            console.info(
                `Poster products: ${loadedCount} loaded successfully, ` +
                `${before - loadedCount} failed to load`
            );

            // Handle sticker products
            if (Array.isArray(stickerProducts) && stickerProducts.length) {
                const firstFile = String(stickerProducts[0].file || '');
                if (firstFile.startsWith('images/PINTEREST IMAGES/')) {
                    console.debug('Validating sticker product images...');
                    
                    const okS = await Promise.all(
                        stickerProducts.map(s => preloadImage(s.file, 5000))
                    );
                    const beforeS = stickerProducts.length;
                    
                    // Sort stickers by load success
                    stickerProducts = stickerProducts
                        .map((product, index) => ({ ...product, didLoad: okS[index] }))
                        .sort((a, b) => Number(b.didLoad) - Number(a.didLoad));
                    
                    const loadedCount = okS.filter(Boolean).length;
                    console.info(
                        `Sticker products: ${loadedCount} loaded successfully, ` +
                        `${beforeS - loadedCount} failed to load`
                    );
                }
            }
        } finally {
            console.groupEnd();
        }

        // Initialize UI
        console.group('UI Initialization');
        try {
            await Promise.all([
                initSidebar(),
                renderProducts(),
                updateUI()
            ]);
            console.info('UI initialization complete');
        } finally {
            console.groupEnd();
        }

    } catch (err) {
        console.error('Critical error during app initialization:', err);
    } finally {
        console.groupEnd();
    }
};

// Start initialization when DOM is ready
window.addEventListener('DOMContentLoaded', initializeApp);
