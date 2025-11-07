// Shared utilities for Poster Point (safe, non-module, attaches to window.Utils)
(function(window){
  const Utils = {
    normalizeKey: function(k){ return String(k || '').toLowerCase().replace(/\s+/g,''); },
    escapeHtml: function(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); },
    formatINR: function(n){ return '₹' + Number(n || 0).toFixed(0); },
    // derive title: look for prefix+number patterns in filename stem
    deriveTitleFromFilename: function(fname, cat, idx) {
      if (!fname || typeof fname !== 'string') return null;
      try {
        const parts = fname.replace(/\\/g, '/').split('/');
        let base = parts[parts.length - 1] || fname;
        try { base = decodeURIComponent(base); } catch(e) { /* ignore */ }
        let stem = base.replace(/\.[^.]+$/, '');
        stem = stem.replace(/(_c?_?triptych|_?triptych|_?full|_?columns|_?rows|_c|_a)/i, '');
        const m = stem.match(/^([A-Za-z]{1,4})[-_ ]?0*([0-9]{1,4})/);
        if (m) {
          return m[1].toUpperCase() + '-' + String(m[2]).padStart(3, '0');
        }
        const m2 = stem.match(/([0-9]{1,4})$/);
        if (m2) {
          return (cat === 'MOVIE POSTERS' ? ('MP-' + String(idx+1).padStart(3,'0')) : (cat + ' #' + String(idx+1).padStart(3,'0')));
        }
      } catch (e) {
        // ignore
      }
      return null;
    }
  };
  window.Utils = window.Utils || Utils;
})(window);
