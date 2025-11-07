/**
 * Poster Point - Main Application
 */

// Initialize and validate catalog
console.group('Catalog Initialization');
try {
    // Initialize with default if needed
    if (!window.imageCatalog || typeof window.imageCatalog !== 'object') {
        window.imageCatalog = {};
    }
    
    // Validate and add missing categories
    const requiredCategories = [
        'ANIME',
        'AESTHETICS',
        'CARS',
        'DC',
        'DEVOTIONAL',
        'MARVEL',
        'MOVIE POSTERS',
        'SPORTS',
        'SINGLE STICKERS',
        'FULLPAGE'
    ];

    requiredCategories.forEach(cat => {
        if (!window.imageCatalog[cat] || !Array.isArray(window.imageCatalog[cat])) {
            console.warn(`Adding missing category: ${cat}`);
            window.imageCatalog[cat] = [];
        }
    });

    console.info('Categories initialized:', Object.keys(window.imageCatalog));
} catch (error) {
    console.error('Catalog initialization error:', error);
} finally {
    console.groupEnd();
}

const imageCatalog = window.imageCatalog;

// Configuration
const basePrice = 39;  // Default A4 size price
const STICKER_A4_PRICE = 99;
const STICKER_A3_PRICE = 159;
// Added 'Split Posters' as a separate top-level type so split posters can be browsed independently
const types = ['Posters', 'Split Posters', 'Bookmarks', 'Stickers'];
const fullPageKey = 'FULLPAGE';
const SHOW_INITIAL = 6;
// Control bookmark thumbnail max-height (px) used in the product grid
const BOOKMARK_THUMB_MAX_HEIGHT = 220;

// Application state
let posterProducts = [];
let posterCandidates = [];
let selectedType = 'Posters';
let selectedSubcat = null;
let searchTerm = '';
let showingAll = false;
let stickerProducts = [];
let bookmarkProducts = [];

// Set initial type from URL if present
const urlParams = new URLSearchParams(window.location.search);
const preType = urlParams.get('type');
if (types.includes(preType)) {
    selectedType = preType;
}

// Size options and prices
const sizeOptions = [
    { id: 'A4', label: 'A4', price: 39 },      // Standard A4 size
    { id: 'A3', label: 'A3', price: 69 },      // Large A3 size
    { id: 'A5', label: 'A5', price: 25 },      // Small A5 size
    { id: 'Pocket', label: 'Pocket', price: 10 },// Pocket size
    { id: '4x6', label: '4*6 inch', price: 19 } // Photo size
];

// Helper functions
function normalizeKey(k) { 
    return String(k || '').toLowerCase().replace(/\s+/g,''); 
}

function escapeHtml(s){ 
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); 
}

// Try to derive a useful display title from a filename or path.
// Looks for a prefix+number pattern in the filename (e.g. MP-053, SP_012, MOT012)
function deriveTitleFromFilename(fname, cat, idx) {
    if (!fname || typeof fname !== 'string') return null;
    try {
        // get basename
        const parts = fname.replace(/\\/g, '/').split('/');
        let base = parts[parts.length - 1] || fname;
        try { base = decodeURIComponent(base); } catch(e) { /* ignore */ }
        // remove extension
        let stem = base.replace(/\.[^.]+$/, '');
        // strip common tokens we append (triptych, full, columns, rows, c, a)
        stem = stem.replace(/(_c?_?triptych|_?triptych|_?full|_?columns|_?rows|_c|_a)/i, '');
        // match prefix-number like ABC-001 or ABC001 or ABC_001
        const m = stem.match(/^([A-Za-z]{1,4})[-_ ]?0*([0-9]{1,4})/);
        if (m) {
            return m[1].toUpperCase() + '-' + String(m[2]).padStart(3, '0');
        }
        // fallback: try trailing number
        const m2 = stem.match(/([0-9]{1,4})$/);
        if (m2) {
            return cat === 'MOVIE POSTERS' ? ('MP-' + String(idx+1).padStart(3,'0')) : (cat + ' #' + String(idx+1).padStart(3,'0'));
        }
    } catch (e) {
        console.debug('deriveTitleFromFilename failed for', fname, e);
    }
    return null;
}

function formatINR(n){ 
    return '₹' + n.toFixed(0); 
}

// Initialize posters
function initializePosters() {
    // Build poster candidates (skip duplicates by file path)
    const seenFiles = new Set();
    Object.keys(imageCatalog).forEach(cat => {
        const images = imageCatalog[cat] || [];
        // Exclude bookmark and sticker/fullpage categories from posters
        if (cat !== 'FULLPAGE' && cat !== 'SINGLE STICKERS' && cat !== 'BOOKMARK') {
            images.forEach((fname, idx) => {
                // Accept a few manifest shapes: string, {file:...}, {src:...}
                if (fname && typeof fname === 'object') {
                    if (typeof fname.file === 'string') fname = fname.file;
                    else if (typeof fname.src === 'string') fname = fname.src;
                }
                if (typeof fname !== 'string') {
                    console.warn('Skipping poster manifest entry with unexpected type (not a string):', { category: cat, index: idx, entry: fname });
                    return;
                }
                const id = `${cat.toLowerCase().replace(/\s+/g,'-')}-${idx+1}`;
                const paddedIndex = String(idx+1).padStart(3, '0');
                // try to derive a title from the filename (gives MP-001, SP-001, MOT-001 etc)
                let title = deriveTitleFromFilename(fname, cat, idx);
                if (!title) {
                    title = cat === 'MOVIE POSTERS' ? 'MP-' + paddedIndex : cat + ' #' + paddedIndex;
                }
                
                // Manifest entries may be just filenames (old format) or full relative paths
                // (e.g. "outputs/CATEGORY/..._triptych.jpg"). If the entry contains a
                // path separator use it as-is; otherwise build the legacy images path.
                let filePath;
                if (typeof fname === 'string' && fname.indexOf('/') !== -1) {
                    filePath = fname; // already a relative path
                } else {
                    const encodedCat = encodeURIComponent(cat);
                    const encodedFname = encodeURIComponent(fname);
                    filePath = `images/PINTEREST IMAGES/${encodedCat}/${encodedFname}`;
                }

                // Normalize file path for duplicate detection (forward slashes, decode, lower)
                let canonical = String(filePath).replace(/\\/g, '/');
                try { canonical = decodeURIComponent(canonical); } catch(e) { /* ignore */ }
                canonical = canonical.toLowerCase();
                // Avoid adding the same file more than once — log when skipping
                if (seenFiles.has(canonical)) {
                    console.warn('Skipping duplicate poster (runtime):', { canonical, filePath, category: cat, source: fname });
                    return;
                }
                // log adding
                console.debug('Adding poster (runtime):', { id, filePath, canonical, category: cat });
                seenFiles.add(canonical);

                // store original file path for display but keep canonical for dedupe
                posterProducts.push({
                    id,
                    file: filePath,
                    name: title,
                    price: basePrice,
                    category: cat
                });
            });
        }
    });
}

// Initialize bookmarks (separate from posters)
function initializeBookmarks() {
    const images = imageCatalog['BOOKMARK'] || [];
    images.forEach((fname, idx) => {
        // Support object-shaped manifest entries
        if (fname && typeof fname === 'object') {
            if (typeof fname.file === 'string') fname = fname.file;
            else if (typeof fname.src === 'string') fname = fname.src;
        }
        if (typeof fname !== 'string') {
            console.warn('Skipping bookmark manifest entry with unexpected type (not a string):', { index: idx, entry: fname });
            return;
        }
        const paddedIndex = String(idx + 1).padStart(3, '0');
        const id = `bookmark-${paddedIndex}`;
        // derive a name from filename if possible
        const derived = deriveTitleFromFilename(fname, 'BOOKMARK', idx);
        const name = derived || `Bookmark #${paddedIndex}`;

        // Support manifest entries that may be full relative paths (outputs/...) or bare filenames
        let filePath;
        if (typeof fname === 'string' && fname.indexOf('/') !== -1) {
            filePath = fname;
        } else {
            const encodedFname = encodeURIComponent(fname);
            filePath = `images/PINTEREST IMAGES/BOOKMARK/${encodedFname}`;
        }

        bookmarkProducts.push({
            id,
            file: filePath,
            name,
            price: 20,
            category: 'BOOKMARK'
        });
    });
}

// Initialize stickers
function initializeStickers() {
    // Add single stickers
    if (imageCatalog['SINGLE STICKERS']?.length) {
        imageCatalog['SINGLE STICKERS'].forEach((fname, idx) => {
            if (fname && typeof fname === 'object') {
                if (typeof fname.file === 'string') fname = fname.file;
                else if (typeof fname.src === 'string') fname = fname.src;
            }
            if (typeof fname !== 'string') {
                console.warn('Skipping single-sticker manifest entry with unexpected type (not a string):', { index: idx, entry: fname });
                return;
            }
            const paddedIndex = String(idx + 1).padStart(3, '0');
            const id = `single-sticker-${paddedIndex}`;
            const derived = deriveTitleFromFilename(fname, 'SINGLE STICKERS', idx);
            const name = derived || `Sticker #${paddedIndex}`;
            let filePath;
            if (typeof fname === 'string' && fname.indexOf('/') !== -1) {
                filePath = fname;
            } else {
                const encodedFname = encodeURIComponent(fname);
                filePath = `images/PINTEREST IMAGES/SINGLE STICKERS/${encodedFname}`;
            }
            // Use the manifest key for category so runtime filtering (which compares
            // against the manifest keys like 'SINGLE STICKERS') matches correctly.
            stickerProducts.push({ 
                id, 
                name, 
                price: 9,
                category: 'SINGLE STICKERS',
                file: filePath 
            });
        });
    }

    // Add fullpage stickers
    if (imageCatalog['FULLPAGE']?.length) {
        imageCatalog['FULLPAGE'].forEach((fname, idx) => {
            if (fname && typeof fname === 'object') {
                if (typeof fname.file === 'string') fname = fname.file;
                else if (typeof fname.src === 'string') fname = fname.src;
            }
            if (typeof fname !== 'string') {
                console.warn('Skipping fullpage manifest entry with unexpected type (not a string):', { index: idx, entry: fname });
                return;
            }
            const paddedIndex = String(idx + 1).padStart(3, '0');
            const id = `fullpage-sticker-${paddedIndex}`;
            const derived = deriveTitleFromFilename(fname, 'FULLPAGE', idx);
            const name = derived || `FULLPAGE #${paddedIndex}`;
            let filePath;
            if (typeof fname === 'string' && fname.indexOf('/') !== -1) {
                filePath = fname;
            } else {
                const encodedFname = encodeURIComponent(fname);
                filePath = `images/PINTEREST IMAGES/FULLPAGE/${encodedFname}`;
            }
            stickerProducts.push({ 
                id, 
                name, 
                price: STICKER_A4_PRICE,
                category: 'FULLPAGE',
                file: filePath 
            });
        });
    }
}

// Wire sidebar: populate types and subcategories
function initSidebar() {
    const typeList = document.getElementById('type-list');
    const subcatList = document.getElementById('subcats');
    
    if (!typeList || !subcatList) {
        console.error('Could not find required elements: type-list and subcats');
        return;
    }
    
    // Clear type list
    typeList.innerHTML = '';
    
    // Add type options with item counts
    types.forEach(t => {
        const li = document.createElement('li');
        // compute counts for each type
        let count = 0;
        try {
            if (t === 'Posters') {
                count = Object.keys(imageCatalog || {}).reduce((s, cat) => {
                    if (cat === 'FULLPAGE' || cat === 'SINGLE STICKERS' || cat === 'BOOKMARK' || cat === 'SPLIT POSTERS') return s;
                    return s + ((imageCatalog[cat] && imageCatalog[cat].length) || 0);
                }, 0);
            } else if (t === 'Split Posters') {
                // count only the specific SPLIT POSTERS category
                count = (imageCatalog['SPLIT POSTERS'] && imageCatalog['SPLIT POSTERS'].length) || 0;
            } else if (t === 'Bookmarks') {
                count = (imageCatalog['BOOKMARK'] && imageCatalog['BOOKMARK'].length) || 0;
            } else if (t === 'Stickers') {
                count = ((imageCatalog['SINGLE STICKERS'] && imageCatalog['SINGLE STICKERS'].length) || 0) + ((imageCatalog['FULLPAGE'] && imageCatalog['FULLPAGE'].length) || 0);
            } else {
                // Photoframes / other
                count = 0;
            }
        } catch (e) { /* ignore */ }

        li.textContent = `${t} (${count})`;
        li.dataset.type = t;
        if (t === selectedType) {
            li.classList.add('active');
        }

        li.addEventListener('click', () => {
            selectedType = t;
            selectedSubcat = null;
            Array.from(typeList.children).forEach(ch => ch.classList.remove('active'));
            li.classList.add('active');
            populateSubcats();
            applyFilters();
        });

        typeList.appendChild(li);
    });
    
    populateSubcats();
}

function populateSubcats(){
    const subcatList = document.getElementById('subcats');
    if(!subcatList) return;
    
    // Clear previous categories
    subcatList.innerHTML = '';
    
    if(selectedType === 'Posters') {
        // Show all valid categories except stickers
        const categories = Object.keys(imageCatalog)
            .filter(cat => {
                if (cat === 'FULLPAGE' || cat === 'SINGLE STICKERS' || cat === 'BOOKMARK' || cat === 'SPLIT POSTERS') return false;
                return imageCatalog[cat]?.length > 0;
            })
            .sort();
            
        console.log('Available categories:', categories);
        
        // Add category options (show per-category counts)
        categories.forEach(cat => {
            const li = document.createElement('li');
            const count = (imageCatalog[cat] && imageCatalog[cat].length) || 0;
            li.textContent = `${cat} (${count})`;
            li.dataset.cat = cat;
            if(cat === selectedSubcat) li.classList.add('active');
            
            li.addEventListener('click', () => {
                if(selectedSubcat === cat) {
                    selectedSubcat = null;
                    li.classList.remove('active');
                } else {
                    selectedSubcat = cat;
                    Array.from(subcatList.children).forEach(ch => ch.classList.remove('active'));
                    li.classList.add('active');
                }
                applyFilters();
            });
            
            subcatList.appendChild(li);
        });
        
    } else if(selectedType === 'Bookmarks') {
    // Show bookmark category only (with count)
    const li = document.createElement('li');
    const bmCount = (imageCatalog['BOOKMARK'] && imageCatalog['BOOKMARK'].length) || 0;
    li.textContent = `BOOKMARK (${bmCount})`;
    li.dataset.cat = 'BOOKMARK';
        if('BOOKMARK' === selectedSubcat) li.classList.add('active');
        li.addEventListener('click', () => {
            if(selectedSubcat === 'BOOKMARK') {
                selectedSubcat = null;
                li.classList.remove('active');
            } else {
                selectedSubcat = 'BOOKMARK';
                Array.from(subcatList.children).forEach(ch => ch.classList.remove('active'));
                li.classList.add('active');
            }
            applyFilters();
        });
        subcatList.appendChild(li);
    } else if(selectedType === 'Stickers') {
        // Show sticker options with counts
        ['SINGLE STICKERS', 'FULLPAGE'].forEach(option => {
            const li = document.createElement('li');
            // display label in user-friendly form but use the manifest key for counts
            const label = option === 'SINGLE STICKERS' ? 'Single Stickers' : option;
            const count = (imageCatalog[option] && imageCatalog[option].length) || 0;
            li.textContent = `${label} (${count})`;
            li.dataset.cat = option;
            if(option === selectedSubcat) li.classList.add('active');
            
            li.addEventListener('click', () => {
                if(selectedSubcat === option) {
                    selectedSubcat = null;
                    li.classList.remove('active');
                } else {
                    selectedSubcat = option;
                    Array.from(subcatList.children).forEach(ch => ch.classList.remove('active'));
                    li.classList.add('active');
                }
                applyFilters();
            });
            
            subcatList.appendChild(li);
        });
    }
}

// Wire search input
const searchInput = document.getElementById('search-input');
if(searchInput) {
    searchInput.addEventListener('input', (e) => { 
        searchTerm = e.target.value.trim().toLowerCase(); 
        applyFilters(); 
    });
}

// Filter and render products
function getFilteredProducts() {
    let res = [];
    
    if (selectedType === 'Split Posters') {
        // Only show items in the SPLIT POSTERS category
        res = posterProducts.filter(p => (p.category || '').toUpperCase() === 'SPLIT POSTERS');
        // ignore selectedSubcat for this special type
    } else if(selectedType === 'Posters') {
        // Exclude SPLIT POSTERS from the main Posters view
        res = posterProducts.filter(p => (String(p.category || '').toUpperCase()) !== 'SPLIT POSTERS');
        if(selectedSubcat) {
            res = res.filter(p => p.category === selectedSubcat);
        }
    } else if(selectedType === 'Bookmarks') {
        res = bookmarkProducts;
        if(selectedSubcat) {
            res = res.filter(p => p.category === selectedSubcat);
        }
    } else if(selectedType === 'Stickers') {
        if(selectedSubcat) {
            res = stickerProducts.filter(p => p.category === selectedSubcat);
        } else {
            res = stickerProducts;
        }
    }
    
    if(searchTerm) {
        res = res.filter(p => 
            p.name.toLowerCase().includes(searchTerm) || 
            p.category.toLowerCase().includes(searchTerm)
        );
    }
    
    return res;
}

// Render product grid
const grid = document.getElementById('product-grid');

function applyFilters() {
    if (document.activeElement !== document.getElementById('toggle-btn')) {
        showingAll = false;
    }
    renderProducts();
    updateUI();
}

function renderProducts() {
    if(!grid) return;
    
    grid.innerHTML = '';
    const all = getFilteredProducts();
    
    if(all.length === 0) {
        grid.innerHTML = '<div class="empty">No items found for this selection.</div>';
        const existingToggle = document.getElementById('show-toggle'); 
        if(existingToggle) existingToggle.remove();
        return;
    }
    
    const list = showingAll ? all : all.slice(0, SHOW_INITIAL);
    list.forEach(p => {
        const card = document.createElement('div');
        card.className = 'card';

        // Determine thumbnail styles per item type
        let thumbStyle = 'background:#f0f0f0;aspect-ratio:1;display:flex;align-items:center;justify-content:center';
        let imgStyle = '';
        // p.category may be 'BOOKMARK', 'Single Stickers' or 'FULLPAGE' etc.
        const catUpper = String(p.category || '').toUpperCase();
        if (catUpper === 'BOOKMARK') {
            // Bookmarks are tall & narrow — preserve natural aspect and size to match template
            // Use the template paste-box height as the thumbnail max-height so the
            // artwork visually replaces the white bookmark area on the template.
            // The value is controlled by `BOOKMARK_THUMB_MAX_HEIGHT` above.
            thumbStyle = 'background:transparent;display:flex;align-items:center;justify-content:center;padding:4px';
            imgStyle = `max-height:${BOOKMARK_THUMB_MAX_HEIGHT}px;width:auto;display:block`;
        } else if (catUpper === 'SINGLE STICKERS' || catUpper === 'FULLPAGE' || selectedType === 'Stickers') {
            // Stickers should show transparent background — don't use gray backdrop
            thumbStyle = 'background:transparent;aspect-ratio:1;display:flex;align-items:center;justify-content:center';
            imgStyle = 'width:80%;height:auto;display:block';
        }

        // Size options for posters (also apply to Split Posters)
        let sizeHtml = '';
        // Default display price for the card (used when size-select exists)
        let defaultSizePrice = p.price;
        if(selectedType === 'Posters' || selectedType === 'Split Posters') {
            if (selectedType === 'Split Posters') {
                // Split Posters have higher base prices per request
                sizeHtml = `
                    <option value="A4" data-price="159" selected>A4 - ₹159</option>
                    <option value="A3" data-price="259">A3 - ₹259</option>
                    <option value="A5" data-price="25">A5 - ₹25</option>
                    <option value="Pocket" data-price="10">Pocket - ₹10</option>
                    <option value="4x6" data-price="19">4*6 inch - ₹19</option>
                `;
                defaultSizePrice = 159;
            } else {
                sizeHtml = `
                    <option value="A4" data-price="39" selected>A4 - ₹39</option>
                    <option value="A3" data-price="69">A3 - ₹69</option>
                    <option value="A5" data-price="25">A5 - ₹25</option>
                    <option value="Pocket" data-price="10">Pocket - ₹10</option>
                    <option value="4x6" data-price="19">4*6 inch - ₹19</option>
                `;
                defaultSizePrice = 39;
            }
        }
        
    // Product badge and type (show badge for Posters and Split Posters)
    let badge = (selectedType === 'Posters' || selectedType === 'Split Posters') ? `<div class="badge-a4">A4</div>` : '';
    let itemType = selectedType === 'Stickers' ? (selectedSubcat || 'Sticker')
            : selectedType === 'Bookmarks' ? 'Laminated bookmark'
            : 'Limited edition print';
        
        // Card HTML
        card.innerHTML = `
            <div class="thumb" style="${thumbStyle}">
                <img src="${encodeURI(p.file)}" style="${imgStyle}" alt="${escapeHtml(p.name)}" loading="lazy">
            </div>
            ${badge}
            <div class="card-body">
                <div class="product-name">${escapeHtml(p.name)}</div>
                <div class="product-price">${formatINR(defaultSizePrice)}</div>
                <div class="muted">${itemType}${selectedType === 'Posters' ? ' • <span class="size-label">A4</span>' : ''}</div>
                <div class="controls">
                    ${selectedType === 'Posters' ? `
                        <div class="size-select-wrapper">
                            <label class="size-select-label">Select Size</label>
                            <select class="size-select" data-id="${p.id}">${sizeHtml}</select>
                        </div>
                    ` : ''}
                    <div class="controls-row">
                        <div class="qty">Qty: <span style="font-weight:900;margin-left:8px" id="${p.id}-display">0</span></div>
                        <button class="add" data-id="${p.id}">Buy now</button>
                    </div>
                </div>
            </div>
        `;
        
        // Wire size change handler
        if(selectedType === 'Posters' || selectedType === 'Split Posters') {
            const sel = card.querySelector('.size-select');
            sel?.addEventListener('change', (ev) => {
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
    
    // Show more/less toggle
    const existingToggle = document.getElementById('show-toggle');
    if (existingToggle) {
        existingToggle.remove();
    }
    
    if (all.length > SHOW_INITIAL) {
        const toggle = document.createElement('div');
        toggle.id = 'show-toggle';
        toggle.style.textAlign = 'center';
        toggle.style.marginTop = '24px';
        toggle.innerHTML = `
            <button class="checkout" id="toggle-btn" style="padding:10px 20px;font-size:14px;font-weight:600">
                ${showingAll ? 'Show less' : 'Show more'}
            </button>
        `;
        
        toggle.querySelector('button').addEventListener('click', () => {
            showingAll = !showingAll;
            renderProducts();
            updateUI();
        });
        
        grid.parentNode.insertBefore(toggle, grid.nextSibling);
    }

    // Attach image error handlers and diagnostic logging so missing images are detected
    try {
        document.querySelectorAll('#product-grid img').forEach(img => {
            // Already attached? skip
            if (img.dataset._errorHandlerAttached) return;
            img.dataset._errorHandlerAttached = '1';
            img.addEventListener('error', () => {
                const src = img.getAttribute('src') || '';
                console.warn('Image failed to load:', src, ' — replacing with placeholder');
                const placeholder = 'data:image/svg+xml;utf8,' + encodeURIComponent(
                    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect width="100%" height="100%" fill="#f3f3f3"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#888" font-size="20">Image not found</text></svg>'
                );
                img.src = placeholder;
                img.classList.add('broken');
            });
            // Optional: log successful loads (helps debug caching/404)
            img.addEventListener('load', () => {
                // decodeURI to display readable path
                try { console.debug('Image loaded:', decodeURIComponent(img.getAttribute('src'))); } catch(e) { console.debug('Image loaded:', img.getAttribute('src')); }
            });
        });
    } catch (err) {
        console.error('Error attaching image handlers', err);
    }
}

// Cart functionality
const cart = {};

document.addEventListener('click', (e) => {
    const btn = e.target.closest('button.add');
    if(!btn) return;
    
    const id = btn.getAttribute('data-id');
    const card = btn.closest('.card');
    let size = 'A4', price = 39;
    
    // Treat Split Posters the same as Posters for size/price selection
    if((selectedType === 'Posters' || selectedType === 'Split Posters') && card) {
        const sel = card.querySelector('.size-select');
        if(sel) {
            size = sel.value;
            price = Number(sel.selectedOptions[0].dataset.price || price);
        }
    } else if(selectedType === 'Stickers') {
        price = selectedSubcat === 'FULLPAGE' ? STICKER_A4_PRICE : 9;
    } else if (selectedType === 'Bookmarks') {
        // For bookmarks use the product's configured price (do not use default 39)
        const bp = bookmarkProducts.find(p => p.id === id);
        if (bp) {
            price = Number(bp.price || price);
        }
        // bookmarks don't have sizes
        size = '';
    }
    
    addToCart(id, 1, size, price);
    createToast('Added to cart', 600);
});

// Cart functionality
function addToCart(id, qty=1, size='A4', priceOverride=null) {
    let prod = selectedType === 'Posters' || selectedType === 'Split Posters' ? posterProducts.find(p => p.id === id)
             : selectedType === 'Bookmarks' ? bookmarkProducts.find(p => p.id === id)
             : selectedType === 'Stickers' ? stickerProducts.find(p => p.id === id)
             : null;
    
    if(!prod) return;
    
    const key = id + '::' + size;
    if(!cart[key]) {
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

function removeFromCart(id) {
    delete cart[id];
    updateUI();
}

function changeQty(id, newQty) {
    if(newQty <= 0) {
        removeFromCart(id);
        return;
    }
    if(cart[id]) cart[id].qty = newQty;
    updateUI();
}

function clearCart() {
    Object.keys(cart).forEach(k => delete cart[k]);
    updateUI();
}

// Cart UI
const cartBody = document.getElementById('cart-body');
const cartCount = document.getElementById('cart-count');
const cartTotal = document.getElementById('cart-total');

// Offer logic
function computeOfferForEntries(entries) {
    // Offers defined as groupSize -> freePerGroup, larger groups first (better value)
    // New offer rules: Buy 10 get 5 free (group 15 pay 10), Buy 5 get 2 free (group 7 pay 5), Buy 3 get 1 free (group 4 pay 3)
    const offers = [
        { group: 15, free: 5 }, // Buy 10 get 5 free -> group of 15 (pay 10)
        { group: 7, free: 2 },  // Buy 5 get 2 free  -> group of 7 (pay 5)
        { group: 4, free: 1 }   // Buy 3 get 1 free  -> group of 4 (pay 3)
    ];

    if (!entries || entries.length === 0) return { applied: false };
    // derive categories and top-level types for entries
    const cats = new Set(entries.map(e => (String(e.category||'').toUpperCase())));
    // derive top-level type for each entry's category so offers can apply per-type
    const typesFromEntries = new Set(entries.map(e => {
        const c = String(e.category || '').toUpperCase();
        // map manifest/category names to top-level type names used in UI
        if (c === 'SPLIT POSTERS') return 'SPLIT_POSTERS';
        if (c === 'BOOKMARK' || c === 'BOOKMARKS') return 'BOOKMARKS';
        if (c === 'FULLPAGE' || c === 'SINGLE STICKERS' || c.includes('STICKER')) return 'STICKERS';
        // any other category is treated as Posters
        return 'POSTERS';
    }));
    // Previously we required uniform category or top-level type. Make offers
    // apply cart-wide so customers get the promotion regardless of mixed
    // categories (this matches user expectation that offers apply across
    // the whole cart). If you want per-category offers instead, we can
    // restore the stricter check.

    const totalQty = entries.reduce((s, it) => s + (Number(it.qty) || 0), 0);
    if (totalQty <= 0) return { applied: false };

    let remaining = totalQty;
    let freeCount = 0;
    for (const o of offers) {
        const groups = Math.floor(remaining / o.group);
        if (groups > 0) {
            freeCount += groups * o.free;
            remaining -= groups * o.group;
        }
    }

    if (freeCount <= 0) return { applied: false };

    // compute discount amount: make the cheapest units free (fair for mixed prices)
    const unitPrices = [];
    entries.forEach(it => {
        for (let i = 0; i < (it.qty || 0); i++) unitPrices.push(Number(it.price || 0));
    });
    unitPrices.sort((a,b) => a - b);
    const freeUnits = Math.min(freeCount, unitPrices.length);
    const discount = unitPrices.slice(0, freeUnits).reduce((s, v) => s + v, 0);

    // Build human-friendly message: prefer category name when uniform, otherwise use top-level type
    let message;
    if (cats.size === 1) {
        const catName = Array.from(cats)[0];
        message = `${catName} offer applied`;
    } else {
        const t = Array.from(typesFromEntries)[0];
        const pretty = t === 'POSTERS' ? 'Posters' : t === 'SPLIT_POSTERS' ? 'Split Posters' : t === 'STICKERS' ? 'Stickers' : 'Bookmarks';
        message = `${pretty} offer applied`;
    }
    return { applied: true, freeCount, discount, message };
}

// Update the small offer banner in the toolbar next to the search box
function updateOfferBanner() {
    const el = document.getElementById('offer-banner');
    if (!el) return;
    const baseText = 'Offers: Buy 3 Get 1 Free • Buy 5 Get 2 Free • Buy 10 Get 5 Free';
    // Show scope of offer depending on selection
    if (selectedType === 'Posters') {
        if (selectedSubcat) {
            el.textContent = `${baseText} — Applies to ${selectedSubcat}`;
        } else {
            el.textContent = `${baseText} — Select a poster category to apply`;
        }
    } else if (selectedType === 'Split Posters') {
        // show that offers apply specifically to Split Posters
        el.textContent = `${baseText} — Applies to Split Posters`;
    } else if (selectedType === 'Stickers') {
        if (selectedSubcat) {
            const label = selectedSubcat === 'SINGLE STICKERS' ? 'Single Stickers' : selectedSubcat;
            el.textContent = `${baseText} — Applies to ${label}`;
        } else {
            el.textContent = `${baseText} — Select a sticker category to apply`;
        }
    } else if (selectedType === 'Bookmarks') {
        el.textContent = `${baseText} — Applies to Bookmarks`;
    } else {
        // For other types show generic info
        el.textContent = `${baseText} — Applies per category or top-level type (Posters, Split Posters, Stickers, Bookmarks)`;
    }
}

function updateUI() {
    // Update quantity displays
    document.querySelectorAll('[id$="-display"]').forEach(el => {
        const id = el.id.replace('-display', '');
        const qty = Object.values(cart)
            .filter(ci => ci.id.startsWith(id + '::') || ci.id === id)
            .reduce((s,i) => s + (i.qty||0), 0);
        el.textContent = qty;
    });
    
    // Update cart
    const entries = Object.values(cart);
    
    if(entries.length === 0) {
        cartBody.innerHTML = '<div class="empty">Your cart is empty — add some items!</div>';
        cartCount.textContent = '0 items';
        cartTotal.textContent = '₹0';
        return;
    }
    
    cartBody.innerHTML = '';
    let total = 0;
    
    entries.forEach(item => {
        total += item.price * item.qty;
        cartBody.innerHTML += `
            <div class="cart-item">
                <img src="${encodeURI(item.file)}" alt="${escapeHtml(item.name)}">
                <div class="meta">
                    <div class="name">${escapeHtml(item.name)}
                        ${item.size ? ` <span style="font-weight:600;color:var(--muted)">(${item.size})</span>` : ''}
                    </div>
                    <div class="line">₹${item.price} × ${item.qty} = ₹${item.price * item.qty}</div>
                </div>
                <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end">
                    <div style="display:flex;gap:6px">
                        <button class="decrease" data-id="${item.id}">−</button>
                        <button class="increase" data-id="${item.id}">+</button>
                    </div>
                    <button class="remove" data-id="${item.id}">Remove</button>
                </div>
            </div>
        `;
    });
    
    const itemCount = entries.reduce((s,i) => s + i.qty, 0);
    cartCount.textContent = itemCount + ' items';

    // Compute offers (apply only when all items are from the same category)
    const offerResult = computeOfferForEntries(entries);
    if (offerResult.applied) {
        // Show original total struck-through and discounted total
        cartTotal.innerHTML = `<span style="text-decoration:line-through;color:var(--muted)">₹${total}</span> <strong style="margin-left:8px">₹${(total - offerResult.discount)}</strong>`;
        const offerMsgEl = document.getElementById('cart-offer-msg');
        if (offerMsgEl) offerMsgEl.textContent = `${offerResult.message} — you get ${offerResult.freeCount} free item(s), saved ₹${offerResult.discount}`;
    } else {
        cartTotal.textContent = '₹' + total;
        const offerMsgEl = document.getElementById('cart-offer-msg');
        if (offerMsgEl) offerMsgEl.textContent = '';
    }
    
    // Update nav cart count
    const navCount = document.getElementById('nav-cart-count');
    if(navCount) navCount.textContent = itemCount + ' items';

    // Update offer banner (shows available offers and applied category)
    try {
        updateOfferBanner();
    } catch (e) { /* ignore */ }
}

// Cart buttons
cartBody?.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if(!btn) return;
    
    const id = btn.dataset.id;
    if(!id) return;
    
    if(btn.classList.contains('increase')) changeQty(id, (cart[id]?.qty || 1) + 1);
    if(btn.classList.contains('decrease')) changeQty(id, (cart[id]?.qty || 1) - 1);
    if(btn.classList.contains('remove')) removeFromCart(id);
});

document.getElementById('clear-cart')?.addEventListener('click', clearCart);

// WhatsApp checkout
document.getElementById('send-whatsapp')?.addEventListener('click', () => {
    const entries = Object.values(cart);
    if(entries.length === 0) {
        alert('Your cart is empty. Add items before sending.');
        return;
    }

    // Enforce minimum order value for WhatsApp checkout and account for offers
    const MIN_ORDER_VALUE = 250; // in INR
    const rawTotal = entries.reduce((s, it) => s + (Number(it.price || 0) * (Number(it.qty) || 0)), 0);
    const offer = computeOfferForEntries(entries);
    const payable = rawTotal - (offer.applied ? offer.discount : 0);
    if (payable < MIN_ORDER_VALUE) {
        alert(`Minimum order value to send via WhatsApp is ₹${MIN_ORDER_VALUE}. Your cart total after offers is ₹${payable}.`);
        return;
    }

    const orderRef = 'PP-' + new Date().toISOString().replace(/[:.]/g, '').slice(0,15);
    let msg = `Order Ref: ${orderRef}\nOrder from Poster Point:\n\n`;
    entries.forEach(it => {
        msg += `${it.name}${it.size ? ` (${it.size})` : ''} × ${it.qty}\n`;
    });
    if (offer.applied) msg += `\nOffer applied: saved ₹${offer.discount}`;
    msg += `\nTotal: ₹${payable}`;

    window.open(`https://wa.me/919395508081?text=${encodeURIComponent(msg)}`, '_blank');
});

// Cart drawer
const navCartBtn = document.getElementById('nav-cart-btn');
const cartDrawer = document.getElementById('cart');
const cartCloseBtn = document.getElementById('cart-close-btn');

navCartBtn?.addEventListener('click', () => {
    const isOpen = cartDrawer.classList.contains('open');
    if(isOpen) closeCart(); else openCart();
});

cartCloseBtn?.addEventListener('click', closeCart);

function openCart() {
    cartDrawer?.classList.add('open');
    updateNavIcon(true);
    updateUI();
}

function closeCart() {
    cartDrawer?.classList.remove('open');
    updateNavIcon(false);
}

function updateNavIcon(open) {
    if(!navCartBtn) return;
    
    navCartBtn.innerHTML = open
        ? '✕ <span style="margin-left:6px">Close</span>'
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
             <path d="M3 3h2l.4 2M7 13h10l3-8H6.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
           </svg>
           <span id="nav-cart-count" style="margin-left:6px">${cartCount?.textContent || '0 items'}</span>`;
}

function createToast(msg, ms = 700) {
    const toast = document.createElement('div');
    Object.assign(toast.style, {
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
    
    toast.textContent = msg;
    document.body.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 180);
        }, ms);
    });
}

// Initialize app
// Initialize app: wait for catalogReady if present so we don't race with manifest.js
window.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing app...');
    const startApp = () => {
        initializePosters();
        initializeStickers();
        initializeBookmarks();
        initSidebar();
        renderProducts();
        updateUI();
    };

    // Runtime duplicate scanner: checks window.imageCatalog after it is populated
    function checkRuntimeManifestDuplicates() {
        try {
            if (!window.imageCatalog || typeof window.imageCatalog !== 'object') {
                console.info('Runtime duplicate check: no imageCatalog present');
                return;
            }
            let any = false;
            Object.keys(window.imageCatalog).forEach(cat => {
                const items = window.imageCatalog[cat] || [];
                const seen = new Set();
                const dups = [];
                items.forEach(it => {
                    if (seen.has(it)) dups.push(it);
                    else seen.add(it);
                });
                if (dups.length) {
                    any = true;
                    console.warn(`Runtime manifest duplicates detected in category '${cat}': ${dups.length} duplicates`);
                    // show up to 20 duplicates for quick inspection
                    console.warn(dups.slice(0, 20));
                }
            });
            if (!any) console.info('Runtime manifest duplicate check: no duplicates found');
        } catch (e) {
            console.error('Runtime manifest duplicate check failed', e);
        }
    }

    if (window.catalogReady && typeof window.catalogReady.then === 'function') {
        window.catalogReady.then(() => {
            console.info('Catalog ready — starting app');
            // run runtime duplicate check so duplicates from dynamic manifests are caught
            checkRuntimeManifestDuplicates();
            startApp();
        }).catch(err => {
            console.warn('Catalog failed to load, starting app anyway', err);
            startApp();
        });
    } else {
        // run duplicate check even if there is no catalogReady promise (static manifest)
        checkRuntimeManifestDuplicates();
        startApp();
    }

    // Sidebar hamburger handlers (mobile)
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebarEl = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function openSidebar() {
        if (!sidebarEl) return;
        sidebarEl.classList.add('open');
        sidebarOverlay?.classList.add('open');
        // prevent body scroll while sidebar open on mobile
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebarEl) return;
        sidebarEl.classList.remove('open');
        sidebarOverlay?.classList.remove('open');
        document.body.style.overflow = '';
    }

    function toggleSidebar() {
        if (sidebarEl && sidebarEl.classList.contains('open')) closeSidebar(); else openSidebar();
    }

    if (hamburgerBtn && sidebarEl) {
        hamburgerBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleSidebar(); });
        sidebarOverlay?.addEventListener('click', closeSidebar);
        // when a user selects a type or subcategory on mobile, automatically close sidebar
        document.getElementById('type-list')?.addEventListener('click', () => { if (window.innerWidth <= 720) closeSidebar(); });
        document.getElementById('subcats')?.addEventListener('click', () => { if (window.innerWidth <= 720) closeSidebar(); });
    }

    // Global quick-size dropdown (toolbar) — allows forcing A3 for Split Posters
    const globalSizeSelect = document.getElementById('global-size-select');
    if (globalSizeSelect) {
        globalSizeSelect.addEventListener('change', (ev) => {
            const val = globalSizeSelect.value;
            // If user selects the A3 quick option, set all visible size-selects to A3
            if (val === 'A3-SPLIT') {
                document.querySelectorAll('.size-select').forEach(sel => {
                    // Only change selects that belong to Split Posters (inspect surrounding card)
                    const card = sel.closest('.card');
                    if (!card) return;
                    // Heuristic: the select's options include A3 with data-price 259 for Split Posters
                    const hasA3 = Array.from(sel.options).some(o => o.value === 'A3' && Number(o.dataset.price || 0) === 259);
                    if (hasA3) {
                        sel.value = 'A3';
                        sel.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            } else {
                // Default: don't change per-card selections; user can individually change sizes
                // Optionally we could reset selects to their inherent default (A4), but keep non-destructive
            }
        });
    }
});

// Runtime diagnostics helper: print manifest categories and counts
try {
    if (window.imageCatalog && typeof window.imageCatalog === 'object') {
        console.info('Runtime manifest summary:', Object.keys(window.imageCatalog).map(k => `${k}:${(window.imageCatalog[k]||[]).length}`).join(', '));
    }
} catch (e) { /* ignore */ }