/* accordion.js — URL hash <-> open state, two-level (large.sub) */

(function () {
  function parseHash() {
    var raw = (location.hash || "").replace(/^#/, "");
    if (!raw) return [];
    return raw.split(",").filter(Boolean);
  }

  function writeHash(ids) {
    var next = ids.length ? "#" + ids.join(",") : window.location.pathname + window.location.search;
    history.replaceState(null, "", next);
  }

  function openIds(ids) {
    ids.forEach(function (id) {
      // hash entries can be "consideration-id" or "consideration-id.sub-id"
      var parts = id.split(".");
      var topId = parts[0];
      var subId = parts[1];
      var top = document.getElementById(topId);
      if (top && top.tagName === "DETAILS") top.open = true;
      if (subId) {
        var sub = document.getElementById(topId + "." + subId);
        if (sub && sub.tagName === "DETAILS") sub.open = true;
      }
    });
  }

  function currentOpen() {
    var ids = [];
    var tops = document.querySelectorAll("details.consideration[open]");
    tops.forEach(function (t) {
      if (!t.id) return;
      var anySubOpen = false;
      t.querySelectorAll("details.sub[open]").forEach(function (s) {
        if (s.id) {
          ids.push(s.id);
          anySubOpen = true;
        }
      });
      if (!anySubOpen) ids.push(t.id);
    });
    return ids;
  }

  function bind() {
    document.querySelectorAll("details.consideration, details.sub").forEach(function (d) {
      d.addEventListener("toggle", function () {
        writeHash(currentOpen());
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    openIds(parseHash());
    bind();
  });
})();
