/* search.js — header search; submits to search.html?q=... */

(function () {
  function go(q) {
    var url = "search.html?q=" + encodeURIComponent(q.trim());
    location.href = url;
  }

  function syncClear(input) {
    var clear = input.parentElement && input.parentElement.querySelector('[data-action="search-clear"]');
    if (clear) clear.hidden = !input.value;
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form.search-form').forEach(function (f) {
      f.addEventListener('submit', function (e) {
        e.preventDefault();
        var input = f.querySelector('input[type="search"]');
        if (input && input.value.trim()) go(input.value);
      });
    });

    // Read ?q= and populate input on search.html
    var params = new URLSearchParams(location.search);
    var q = params.get('q');
    if (q) {
      document.querySelectorAll('input[type="search"][name="q"]').forEach(function (i) {
        i.value = q;
      });
      var echo = document.querySelector('[data-role="query-echo"]');
      if (echo) echo.textContent = q;
    }

    // Clear button: show when input has text, clear on click
    document.querySelectorAll('input[type="search"][name="q"]').forEach(function (input) {
      syncClear(input);
      input.addEventListener('input', function () { syncClear(input); });
    });
    document.querySelectorAll('[data-action="search-clear"]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var input = btn.parentElement && btn.parentElement.querySelector('input[type="search"]');
        if (input) { input.value = ''; input.focus(); syncClear(input); }
      });
    });

    // Responsive drawer: open / close / ESC
    var app = document.querySelector('.app');
    var searchToggle = document.querySelector('[data-action="toggle-search"]');
    function setSearchOpen(open) {
      if (!app) return;
      app.dataset.searchOpen = open ? 'true' : 'false';
      if (searchToggle) {
        searchToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        searchToggle.setAttribute('aria-label', open ? 'Close search' : 'Open search');
      }
      if (open) {
        var drawerInput = document.querySelector('.search-drawer input[type="search"]');
        if (drawerInput) drawerInput.focus();
      }
    }
    if (searchToggle) {
      searchToggle.addEventListener('click', function () {
        setSearchOpen(app && app.dataset.searchOpen !== 'true');
      });
    }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && app && app.dataset.searchOpen === 'true') {
        setSearchOpen(false);
        if (searchToggle) searchToggle.focus();
      }
    });
  });
})();
