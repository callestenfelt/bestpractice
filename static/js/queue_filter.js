// /admin/queue source filter.
// - Chips toggle .qcard[data-source] visibility client-side.
// - Active selection is mirrored to ?sources= in the URL so reload + back
//   navigation preserve it, and is propagated onto each .qcard__link href
//   so clicking through to /admin/queue/<id> carries the filter into the
//   server-side prev/next stepper.
(function () {
  const filter = document.querySelector('[data-queue-source-filter]');
  if (!filter) return;

  const checkboxes = Array.from(filter.querySelectorAll('input[type="checkbox"]'));
  const resetBtn = filter.querySelector('[data-queue-source-reset]');
  const emptyHint = document.querySelector('[data-queue-source-empty]');
  const cards = Array.from(document.querySelectorAll('.qcard[data-source]'));
  const cardLinks = Array.from(document.querySelectorAll('.qcard__link'));

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
    }
    if (emptyHint) emptyHint.hidden = visible !== 0 || allOn;
    if (resetBtn) resetBtn.hidden = allOn;

    // Mirror to URL (without ?sources= when all are on, keeps URLs clean).
    const url = new URL(window.location.href);
    url.searchParams.delete('sources');
    if (!allOn) for (const v of checked) url.searchParams.append('sources', v);
    history.replaceState(null, '', url.toString());

    // Rewrite card links so clicking into the item view carries the filter.
    for (const a of cardLinks) {
      const href = a.getAttribute('href');
      if (!href) continue;
      const target = new URL(href, window.location.origin);
      target.searchParams.delete('sources');
      if (!allOn) for (const v of checked) target.searchParams.append('sources', v);
      a.setAttribute('href', target.pathname + target.search);
    }
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
