// /admin/queue source filter.
// - Chips toggle .qcard[data-source] visibility client-side.
// - Active selection is mirrored to ?sources= in the URL so reload + back
//   navigation preserve it, and is propagated onto every link/form inside
//   each .qcard that targets the admin queue (main card link, sidebar
//   Open/Edit anchors, per-card Reject and Re-queue forms). The server
//   reads ?sources= via request.values.getlist so URL params on a form's
//   action are picked up identically to hidden inputs.
(function () {
  const filter = document.querySelector('[data-queue-source-filter]');
  if (!filter) return;

  const checkboxes = Array.from(filter.querySelectorAll('input[type="checkbox"]'));
  const resetBtn = filter.querySelector('[data-queue-source-reset]');
  const emptyHint = document.querySelector('[data-queue-source-empty]');
  const cards = Array.from(document.querySelectorAll('.qcard[data-source]'));

  function rewriteUrl(rawUrl, allOn, checked) {
    if (!rawUrl) return rawUrl;
    const target = new URL(rawUrl, window.location.origin);
    if (!target.pathname.startsWith('/admin/queue')) return rawUrl;
    target.searchParams.delete('sources');
    if (!allOn) for (const v of checked) target.searchParams.append('sources', v);
    return target.pathname + target.search;
  }

  function apply() {
    const checked = checkboxes.filter((c) => c.checked).map((c) => c.value);
    const allOn = checked.length === checkboxes.length;
    const allowed = new Set(checked);

    let visible = 0;
    for (const card of cards) {
      const src = card.getAttribute('data-source') || '';
      const show = allOn || allowed.has(src);
      card.hidden = !show;
      if (show) visible++;

      // Rewrite every admin-queue link and form inside the card so the
      // sidebar Reject/Open/Edit/Re-queue actions carry the filter too.
      for (const a of card.querySelectorAll('a[href]')) {
        const next = rewriteUrl(a.getAttribute('href'), allOn, checked);
        if (next) a.setAttribute('href', next);
      }
      for (const f of card.querySelectorAll('form[action]')) {
        const next = rewriteUrl(f.getAttribute('action'), allOn, checked);
        if (next) f.setAttribute('action', next);
      }
    }

    if (emptyHint) emptyHint.hidden = visible !== 0 || allOn;
    if (resetBtn) resetBtn.hidden = allOn;

    // Mirror to the page URL too (without ?sources= when all are on).
    const url = new URL(window.location.href);
    url.searchParams.delete('sources');
    if (!allOn) for (const v of checked) url.searchParams.append('sources', v);
    history.replaceState(null, '', url.toString());
  }

  checkboxes.forEach((c) => c.addEventListener('change', apply));
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      checkboxes.forEach((c) => (c.checked = true));
      apply();
    });
  }

  apply();
})();
