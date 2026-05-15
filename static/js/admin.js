// Auto-submit forms tagged [data-auto-submit] on change; <noscript> fallback for JS-off.
document.querySelectorAll('form[data-auto-submit]').forEach(function (form) {
  form.addEventListener('change', function () { form.submit(); });
});
