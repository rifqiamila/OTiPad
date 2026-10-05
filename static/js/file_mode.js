// Mode file: dropzone + kirim multipart, terima file.
(() => {
  const O = (window.OTP = window.OTP || {});
  const input = document.querySelector('#input-file');
  const label = document.querySelector('#file-name');
  const dz = document.querySelector('#dropzone');
  const placeholder = label.textContent;

  const showName = () => { label.textContent = input.files[0]?.name || placeholder; };
  input.addEventListener('change', showName);
  ['dragenter', 'dragover'].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('over'); }));
  dz.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showName(); }
  });

  O.file = {
    get: () => input.files[0],
    async run(mode, file, k) {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('key_type', k.keyType);
      if (k.keyValue != null) fd.append('key_value', k.keyValue);

      const res = await fetch(`/api/${mode}/file`, { method: 'POST', body: fd });
      if ((res.headers.get('content-type') || '').includes('json')) {
        return { ok: false, error: O.errMsg(await res.json()) };
      }
      const cd = res.headers.get('content-disposition') || '';
      const filename = (cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)/i) || [])[1] || `${mode}ed.dat`;
      return {
        ok: true, display: `File siap diunduh: ${filename}`,
        text: '', blob: await res.blob(), filename,
      };
    },
  };
})();