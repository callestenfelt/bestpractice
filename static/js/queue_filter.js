(function () {
  const filter = document.querySelector('[data-queue-source-filter]');
  if (!filter) return;

  const checkboxes = Array.from(filter.querySelectorAll('input[type="checkbox"]'));
  const resetBtn = filter.querySelector('[data-queue-source-reset]');
  const emptyHint = document.querySelector('[data-queue-source-empty]');
  const cards = Array.from(document.querySelectorAll('.qcard[data-source]'));

  function apply() {
    const allowed = new Set(
      checkboxes.filter((c) => c.checked).map((c) => c.value)
    );
    const allOn = allowed.size === checkboxes.length;
    let visible = 0;
    for (const card of cards) {
      const src = card.getAttribute('data-source') || '';
      const show = allOn || allowed.has(src);
      card.hidden = !show;
      if (show) visible++;
    }
    if (emptyHint) emptyHint.hidden = visible !== 0 || allOn;
    if (resetBtn) resetBtn.hidden = allOn;
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
