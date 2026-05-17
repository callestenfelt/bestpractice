// Full-page approval stepper.
// - Enter on a single-line input submits the form (Approve & Next).
// - Each dest_key checkbox toggles its <details> open and enables/disables
//   the matching consideration <select>.
// - data-action buttons: reject confirms then submits to the reject URL,
//   save submits to the save URL, new-cons prompts and POSTs to the
//   inline-create endpoint, then appends a selected <option> to the
//   sibling <select>.
(function () {
  const form = document.getElementById('approve-form');
  if (!form) return;
  const newConsUrl = form.dataset.newConsAction;

  // Enter anywhere except textareas/buttons fires Approve & Next.
  form.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const t = e.target;
    if (!t || t.tagName === 'TEXTAREA' || t.tagName === 'BUTTON') return;
    e.preventDefault();
    form.submit();
  });

  // Toggle destination details + select on checkbox change.
  form.querySelectorAll('input[name="dest_key"]').forEach((cb) => {
    cb.addEventListener('change', () => {
      const details = cb.closest('details');
      if (!details) return;
      const select = details.querySelector('select');
      details.open = cb.checked;
      if (select) {
        select.disabled = !cb.checked;
        if (!cb.checked) select.value = '';
      }
    });
    // Prevent the <summary> click from toggling the checkbox state.
    cb.addEventListener('click', (e) => e.stopPropagation());
  });

  form.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn || !form.contains(btn)) return;
    const action = btn.dataset.action;
    if (action === 'reject') {
      e.preventDefault();
      if (!confirm('Reject this item?')) return;
      form.action = form.dataset.rejectAction;
      form.submit();
    } else if (action === 'new-cons') {
      e.preventDefault();
      const title = (prompt('New consideration title:') || '').trim();
      if (!title) return;
      const body = new URLSearchParams({
        parent_type: btn.dataset.kind,
        parent_slug: btn.dataset.slug,
        title: title,
      });
      fetch(newConsUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body,
      })
        .then((r) => r.json().then((d) => ({ ok: r.ok, data: d })))
        .then(({ ok, data }) => {
          if (!ok || !data || !data.ok) {
            alert((data && data.error) || 'Could not create.');
            return;
          }
          const select = btn.parentElement.querySelector('select');
          if (!select) return;
          // Also ensure the checkbox is on and the select is enabled.
          const details = btn.closest('details');
          const cb = details && details.querySelector('input[name="dest_key"]');
          if (cb && !cb.checked) {
            cb.checked = true;
            cb.dispatchEvent(new Event('change'));
          }
          const opt = document.createElement('option');
          opt.value = data.id;
          opt.textContent = data.label;
          opt.selected = true;
          select.appendChild(opt);
        })
        .catch(() => alert('Network error.'));
    }
  });
})();
