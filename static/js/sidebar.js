/* sidebar.js — toggleable left sidebar (Ctrl+. / Cmd+.) and right filters drawer (Ctrl+, / Cmd+,).
   Persists state for both rails in localStorage. */

(function () {
  var SIDEBAR_KEY = 'bp:sidebar-open';
  var FILTERS_KEY = 'bp:filters-open';

  var app = document.querySelector('.app');
  var sidebarToggle = document.querySelector('[data-action="toggle-sidebar"]');
  var filtersToggle = document.querySelector('[data-action="toggle-filters"]');
  var sidebarScrim = document.querySelector('.sidebar-scrim');
  var filtersScrim = document.querySelector('.filters-scrim');

  // ---------------------------------------------------------------
  // Left sidebar
  // ---------------------------------------------------------------
  function setSidebarOpen(open, persist) {
    if (!app) return;
    app.dataset.sidebarOpen = open ? 'true' : 'false';
    if (sidebarToggle) sidebarToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (persist !== false) {
      try { localStorage.setItem(SIDEBAR_KEY, open ? '1' : '0'); } catch (e) {}
    }
  }
  function isSidebarOpen() {
    return app && app.dataset.sidebarOpen === 'true';
  }

  try {
    var s = localStorage.getItem(SIDEBAR_KEY);
    if (s === '0') setSidebarOpen(false, false);
    else setSidebarOpen(true, false);
  } catch (e) {
    setSidebarOpen(true, false);
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function () { setSidebarOpen(!isSidebarOpen()); });
  }
  if (sidebarScrim) {
    sidebarScrim.addEventListener('click', function () { setSidebarOpen(false); });
  }

  // ---------------------------------------------------------------
  // Right filters drawer
  // ---------------------------------------------------------------
  function setFiltersOpen(open, persist) {
    if (!app) return;
    app.dataset.filtersOpen = open ? 'true' : 'false';
    if (filtersToggle) filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (persist !== false) {
      try { localStorage.setItem(FILTERS_KEY, open ? '1' : '0'); } catch (e) {}
    }
  }
  function isFiltersOpen() {
    return app && app.dataset.filtersOpen === 'true';
  }

  try {
    var f = localStorage.getItem(FILTERS_KEY);
    if (f === '0') setFiltersOpen(false, false);
    else setFiltersOpen(true, false);
  } catch (e) {
    setFiltersOpen(true, false);
  }

  if (filtersToggle) {
    filtersToggle.addEventListener('click', function () { setFiltersOpen(!isFiltersOpen()); });
  }
  if (filtersScrim) {
    filtersScrim.addEventListener('click', function () { setFiltersOpen(false); });
  }

  // ---------------------------------------------------------------
  // Shortcuts
  //   Ctrl/Cmd + .  →  toggle left sidebar
  //   Ctrl/Cmd + ,  →  toggle right filters drawer
  // ---------------------------------------------------------------
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.shiftKey || e.altKey) return;
    if (e.key === '.') {
      e.preventDefault();
      setSidebarOpen(!isSidebarOpen());
    } else if (e.key === ',') {
      e.preventDefault();
      setFiltersOpen(!isFiltersOpen());
    }
  });

  // ---------------------------------------------------------------
  // Filters-button count badge (on topbar settings icon).
  // ---------------------------------------------------------------
  function updateFiltersBadge() {
    var badge = document.querySelector('.topbar__toggle-count');
    var railCount = document.querySelector('[data-role="filters-count"]');
    var boxes = document.querySelectorAll('input[name="phase"]');
    var on = 0;
    boxes.forEach(function (b) { if (b.checked) on += 1; });
    var sw = document.querySelector('#toggle-sitewide');
    if (sw && sw.checked) on += 1;

    var label = on > 0 ? String(on) : '';
    if (badge) {
      badge.hidden = !label;
      badge.textContent = label;
    }
    if (railCount) {
      railCount.hidden = !label;
      railCount.textContent = label;
    }
  }

  document.addEventListener('change', function (e) {
    if (e.target && (e.target.name === 'phase' || e.target.id === 'toggle-sitewide')) {
      updateFiltersBadge();
    }
  });
  document.addEventListener('click', function (e) {
    if (e.target && e.target.matches && e.target.matches('[data-action="select-all"], [data-action="clear-all"]')) {
      // filters.js handles the actual change; defer to next tick
      setTimeout(updateFiltersBadge, 0);
    }
  });
  document.addEventListener('DOMContentLoaded', updateFiltersBadge);
})();
