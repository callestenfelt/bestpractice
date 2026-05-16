/* search.js — header search; submits to search.html?q=... */

(function () {
  function go(q) {
    var url = "search.html?q=" + encodeURIComponent(q.trim());
    location.href = url;
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
  });
})();
