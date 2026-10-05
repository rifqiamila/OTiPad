// Penghubung: state UI, submit, dan aksi hasil.
(() => {
  const O = (window.OTP = window.OTP || {});
  const $ = (s) => document.querySelector(s);
  const el = {
    input: $('#sel-input'), mode: $('#sel-mode'), key: $('#sel-key'),
    boxText: $('#box-text'), boxFile: $('#box-file'), boxKey: $('#box-key'),
    text: $('#input-text'), form: $('#otp-form'), submit: $('#btn-submit'), error: $('#error'),
    result: $('#result'), resultTitle: $('#result-title'), resultText: $('#result-text'),
    hint: $('#hint'), share: $('#btn-share'), copyResult: $('#btn-copy-result'),
    dlResult: $('#btn-dl-result'), keyResult: $('#key-result'), keyOut: $('#key-out'),
    dlKey: $('#btn-dl-key'), copyKey: $('#btn-copy-key'),
    // kotak hasil bergrup
    groupBox: $('#grouped-result'), groupLabel: $('#group-label'), groupText: $('#grouped-text'),
    dlGroup: $('#btn-dl-grouped'), copyGroup: $('#btn-copy-grouped'),
  };
  let out = { blob: null, text: '', grouped: '', filename: 'result.txt', key: '' };

  /* ---------- helper bersama ---------- */
  O.errMsg = (d) => d.message || d.reason || d.error || 'Terjadi kesalahan.';
  const showError = (m) => { el.error.textContent = m; el.error.hidden = !m; };
  O.showError = showError;
  const save = (blob, name) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name; a.click();
    URL.revokeObjectURL(a.href);
  };
  const flash = (btn) => {
    btn.classList.add('copied');
    setTimeout(() => btn.classList.remove('copied'), 1200);
  };
  const copy = async (text, btn) => {
    try { await navigator.clipboard.writeText(text); flash(btn); }
    catch { showError('Gagal menyalin. Salin manual dari kotak teks.'); }
  };

  /* ---------- state UI ---------- */
  function syncUI() {
    const inputVal = el.input.value;
    const isDecrypt = el.mode.value === 'decrypt';

    el.boxText.hidden = inputVal !== 'text';
    el.boxFile.hidden = inputVal !== 'file';
    el.boxText.querySelector('.box-label').textContent =
      isDecrypt ? 'Input Ciphertext' : 'Input Text';

    el.key.querySelector('option[value="auto"]').disabled = isDecrypt;
    if (isDecrypt && el.key.value === 'auto') el.key.value = '';

    el.boxKey.hidden = el.key.value !== 'manual';
    el.submit.hidden = !(el.input.value && el.mode.value && el.key.value);
  }
  [el.input, el.mode, el.key].forEach((s) => s.addEventListener('change', syncUI));
  syncUI();

  O.attachTxt(el.boxText);
  O.attachTxt(el.boxKey);

  /* ---------- submit ---------- */
  el.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    showError('');
    if (!el.input.value || !el.mode.value || !el.key.value)
      return showError('Pilih Input, Encrypt/Decrypt, dan Key Option terlebih dahulu.');

    const mode = el.mode.value, isFile = el.input.value === 'file', keyMode = el.key.value;
    const file = O.file.get(), text = el.text.value;

    if (isFile && !file) return showError('Pilih file terlebih dahulu.');
    if (!isFile && !text.trim()) return showError('Masukkan teks terlebih dahulu.');

    el.submit.disabled = true;
    try {
      const k = await O.key.resolve(keyMode, isFile ? file.size : text.length);
      if (!k.ok) return showError(k.error);
      const r = isFile ? await O.file.run(mode, file, k) : await O.text.run(mode, text, k);
      if (!r.ok) return showError(r.error);

      out = {
        blob: r.blob, text: r.text, grouped: r.grouped || '',
        filename: r.filename, key: k.key,
      };
      showResult(mode, r.display, out.grouped, keyMode === 'auto');
    } catch {
      showError('Tidak bisa terhubung ke server.');
    } finally {
      el.submit.disabled = false;
    }
  });

  function showResult(mode, display, grouped, auto) {
    const noun = mode === 'encrypt' ? 'ciphertext' : 'plaintext';
    el.resultTitle.textContent = mode === 'encrypt' ? 'Ciphertext Result:' : 'Plaintext Result:';
    el.resultText.value = display;

    // Kotak bergrup: hanya muncul kalau ada hasil bergrup (input Text)
    el.groupBox.hidden = !grouped;
    el.groupText.value = grouped || '';
    el.groupLabel.textContent = `Grouped ${noun} (5 letters per group):`;

    el.hint.textContent = `Copy ${noun} or download it by clicking the 'download' button.`;
    el.share.hidden = true;
    el.copyResult.hidden = false;
    el.hint.hidden = auto;
    el.keyResult.hidden = !auto;
    el.keyOut.value = out.key;
    el.result.hidden = false;
    el.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ---------- aksi hasil ---------- */
  el.dlResult.addEventListener('click', () =>
    save(out.blob || new Blob([out.text], { type: 'text/plain' }), out.filename));
  el.copyResult.addEventListener('click', () => copy(out.text || el.resultText.value, el.copyResult));

  // Aksi untuk hasil bergrup
  el.dlGroup.addEventListener('click', () =>
    save(new Blob([out.grouped], { type: 'text/plain' }),
         out.filename.replace(/\.txt$/i, '_grouped.txt')));
  el.copyGroup.addEventListener('click', () => copy(out.grouped, el.copyGroup));

  el.share.addEventListener('click', async () => {
    const payload = out.blob ? { files: [new File([out.blob], out.filename)] } : { text: out.text };
    if (navigator.canShare && navigator.canShare(payload)) {
      try { await navigator.share(payload); } catch { /* dibatalkan user */ }
    } else if (!out.blob) {
      copy(out.text, el.share);
    } else {
      showError('Browser ini belum mendukung berbagi file. Gunakan Download.');
    }
  });
  el.dlKey.addEventListener('click', () =>
    save(new Blob([out.key], { type: 'text/plain' }), 'otp-key.txt'));
  el.copyKey.addEventListener('click', () => copy(out.key, el.copyKey));
})();