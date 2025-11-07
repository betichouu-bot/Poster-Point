/**
 * Poster Point - Image catalog loader
 * This manifest dynamically queries `list-images.php` for each category so the
 * JS catalog always reflects the filesystem contents. It exposes `window.catalogReady`
 * which resolves once population completes.
 */

(function () {
  const categories = [
    'ANIME', 'AESTHETICS', 'CARS', 'DC', 'DEVOTIONAL', 'MARVEL', 'MOVIE POSTERS', 'SPORTS',
    'SINGLE STICKERS', 'FULLPAGE'
  ];

  // Initialize empty catalog (app.js will validate again if needed)
  window.imageCatalog = window.imageCatalog || {};
  categories.forEach(cat => {
    if (!Array.isArray(window.imageCatalog[cat])) window.imageCatalog[cat] = [];
  });

  // Populate the catalog by requesting the server PHP helper for each category.
  // Expose a Promise so app.js can wait for the catalog to be ready.
  window.catalogReady = (async function populate() {
    console.group('manifest: populateCatalog');
    try {
      await Promise.all(categories.map(async (cat) => {
        try {
          // Use URLSearchParams to let the browser encode the query safely.
          // This avoids manual double-encoding and is robust for categories with spaces.
          const res = await fetch('list-images.php?' + new URLSearchParams({ category: cat }), { cache: 'no-store' });
          if (!res.ok) {
            console.warn(`manifest: could not fetch ${cat} - ${res.status}`);
            return;
          }
          const list = await res.json();
          if (Array.isArray(list)) {
            window.imageCatalog[cat] = list;
            console.info(`manifest: ${cat} -> ${list.length} files`);
          } else {
            console.warn(`manifest: unexpected response for ${cat}`);
          }
        } catch (err) {
          console.warn(`manifest: error fetching ${cat}`, err);
        }
      }));

      // Log final status
      console.log('manifest: catalog populated', Object.entries(window.imageCatalog).map(([c, arr]) => `${c}:${arr.length}`).join(', '));
    } catch (err) {
      console.error('manifest: populate failed', err);
    } finally {
      console.groupEnd();
    }
  })();
})();