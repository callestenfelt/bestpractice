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
    [['[data-action="select-all"]', true], ['[data-action="clear-all"]', false]].forEach(function (p) {
      document.querySelectorAll(p[0]).forEach(function (btn) {
        btn.addEventListener('click', function () {
          document.querySelectorAll('input[name="phase"]').forEach(function (cb) { cb.checked = p[1]; });
          applyFilters();
        });
      });
    });
  }

  function setupMobileDialog() {
    var trigger = document.querySelector('[data-action="open-filters"]');
    var dialog = document.querySelector('#filters-dialog');
    if (!trigger || !dialog || !dialog.showModal) return;
    var body = dialog.querySelector('[data-role="filters-body"]');
    var rail = document.querySelector('.rail');
    if (!body || !rail) return;
    var mq = window.matchMedia('(max-width: 960px)');

    function syncLocation() {
      if (mq.matches && body.childElementCount === 0) {
        while (rail.firstChild) body.appendChild(rail.firstChild);
      } else if (!mq.matches && body.childElementCount > 0) {
        if (dialog.open) dialog.close();
        while (body.firstChild) rail.appendChild(body.firstChild);
      }
    }
    syncLocation();
    if (mq.addEventListener) mq.addEventListener('change', syncLocation);

    trigger.addEventListener('click', function () { dialog.showModal(); });
    dialog.querySelectorAll('[data-action="close-filters"]').forEach(function (b) {
      b.addEventListener('click', function () { dialog.close(); });
    });
    dialog.addEventListener('click', function (e) {
      if (e.target !== dialog) return;
      var r = dialog.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
        dialog.close();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    setupMobileDialog();
    document.querySelectorAll('input[name="phase"]').forEach(function (cb) {
      cb.addEventListener('change', applyFilters);
    });
    var sw = document.querySelector('#toggle-sitewide');
    if (sw) sw.addEventListener('change', applyFilters);
    bindBulk();
    applyFilters();
  });
})();
