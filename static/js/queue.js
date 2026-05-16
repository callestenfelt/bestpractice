// Review queue — edit-and-approve dialog wiring. The dialog is a single
// shared <dialog> at the bottom of the page; clicking "Edit & approve"
// on a qcard reads that row's data-* attributes into the form and opens
// the dialog. Submit posts to /admin/queue/<id>/edit_approve.
(function () {
  const dialog = document.getElementById('edit-approve-dialog');
  if (!dialog) return;
  const form = document.getElementById('edit-approve-form');
  const oneLiner = form.querySelector('#edit-one-liner');
  const body = form.querySelector('#edit-body');
  const sourceUrl = form.querySelector('#edit-source-url');
  const sourceDate = form.querySelector('#edit-source-date');
  const consSelect = form.querySelector('#edit-cons-id');
  const phaseInputs = form.querySelectorAll('input[name="phase"]');

  // Strip the <p> wrapper the server adds so editing the textarea sees
  // raw text. The submit handler re-wraps server-side.
  function unwrapBody(html) {
    if (!html) return '';
    return html
      .replace(/^\s*<p>/i, '')
      .replace(/<\/p>\s*$/i, '')
      .trim();
  }

  function openFor(card) {
    const subId = card.dataset.subId;
    form.action = '/admin/queue/' + subId + '/edit_approve';
    oneLiner.value = card.dataset.oneLiner || '';
    body.value = unwrapBody(card.dataset.body || '');
    sourceUrl.value = card.dataset.sourceUrl || '';
    sourceDate.value = card.dataset.sourceDate || '';
    consSelect.value = '';  // operator must consciously pick a destination
    const active = new Set((card.dataset.phases || '').split(/\s+/).filter(Boolean));
    phaseInputs.forEach((input) => { input.checked = active.has(input.value); });
    if (typeof dialog.showModal === 'function') {
      dialog.showModal();
    } else {
      dialog.setAttribute('open', '');
    }
    setTimeout(() => oneLiner.focus(), 0);
  }

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-action="edit-approve"]');
    if (trigger) {
      const card = trigger.closest('.qcard');
      if (card) openFor(card);
      return;
    }
    const closer = event.target.closest('[data-action="dialog-close"]');
    if (closer && dialog.contains(closer)) {
      event.preventDefault();
      dialog.close();
    }
  });

  // Click on the backdrop (outside the form rect) closes the dialog.
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
})();
