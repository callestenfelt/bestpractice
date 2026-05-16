/* filters.js — phase filter + site-wide toggle, hides empty considerations and groups */

(function () {
  function activePhases() {
    var set = new Set();
    document.querySelectorAll('input[name="phase"]:checked').forEach(function (cb) {
      set.add(cb.value);
    });
    return set;
  }

  function applyFilters() {
    var phases = activePhases();
    var showSiteWide = !!document.querySelector('#toggle-sitewide:checked');

    // Site-wide group visibility
    var swGroup = document.querySelector('[data-group="site-wide"]');
    if (swGroup) swGroup.hidden = !showSiteWide;

    document.querySelectorAll('details.consideration').forEach(function (cons) {
      var visibleSubs = 0;
      cons.querySelectorAll('details.sub').forEach(function (sub) {
        var tags = (sub.dataset.phases || "").split(/\s+/).filter(Boolean);
        var match = tags.length === 0 || tags.some(function (t) { return phases.has(t); });
        sub.hidden = !match;
        if (match) visibleSubs += 1;
      });

      // count + new-count badge
      var countEl = cons.querySelector('[data-role="count"]');
      if (countEl) countEl.textContent = visibleSubs + (visibleSubs === 1 ? " item" : " items");

      cons.hidden = visibleSubs === 0;
    });

    // hide group section headers whose considerations are all hidden
    document.querySelectorAll('.group').forEach(function (group) {
      if (group.dataset.group === "site-wide") return; // handled above
      var any = false;
      group.querySelectorAll('details.consideration').forEach(function (c) {
        if (!c.hidden) any = true;
      });
      group.hidden = !any;
    });
  }

  function bindBulk() {
    var all = document.querySelector('[data-action="select-all"]');
    var none = document.querySelector('[data-action="clear-all"]');
    if (all) all.addEventListener('click', function () {
      document.querySelectorAll('input[name="phase"]').forEach(function (cb) { cb.checked = true; });
      applyFilters();
    });
    if (none) none.addEventListener('click', function () {
      document.querySelectorAll('input[name="phase"]').forEach(function (cb) { cb.checked = false; });
      applyFilters();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[name="phase"]').forEach(function (cb) {
      cb.addEventListener('change', applyFilters);
    });
    var sw = document.querySelector('#toggle-sitewide');
    if (sw) sw.addEventListener('change', applyFilters);
    bindBulk();
    applyFilters();
  });
})();
