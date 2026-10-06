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

  // Full result state. `keyId`, `downloadUrl`, and `keyFilename`
  let out = {
    blob: null,
    text: '',
    grouped: '',
    filename: 'result.txt',
    key: '',
    keyId: null,
    downloadUrl: null,
    keyFilename: null,
  };

  /* ---------- helper bersama ---------- */
  O.errMsg = (d) => d.message || d.reason || d.error || 'Terjadi kesalahan.';
  const showError = (m) => { el.error.textContent = m; el.error.hidden = !m; };
  O.showError = showError;

  const save = (blob, name) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const flash = (btn) => {
    btn.classList.add('copied');
    setTimeout(() => btn.classList.remove('copied'), 1200);
  };

  const copy = async (text, btn) => {
    if (!text) {
      showError('Tidak ada key untuk disalin.');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      flash(btn);
    } catch {
      showError('Gagal menyalin. Salin manual dari kotak teks.');
    }
  };

  /* ---------- state UI ---------- */
  function syncUI() {
    const inputVal = el.input.value;
    const isDecrypt = el.mode.value === 'decrypt';

    el.boxText.hidden = inputVal !== 'text';
    el.boxFile.hidden = inputVal !== 'file';
    el.boxText.querySelector('.box-label').textContent =
      isDecrypt ? 'Input Ciphertext' : 'Input Text';

    // Auto key is only available for encryption
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

    const mode = el.mode.value;
    const isFile = el.input.value === 'file';
    const keyMode = el.key.value;
    const file = O.file.get();
    const text = el.text.value;

    if (isFile && !file) return showError('Pilih file terlebih dahulu.');
    if (!isFile && !text.trim()) return showError('Masukkan teks terlebih dahulu.');

    el.submit.disabled = true;
    try {
      const k = await O.key.resolve(keyMode, isFile ? file.size : text.length);
      if (!k.ok) return showError(k.error);

      const r = isFile
        ? await O.file.run(mode, file, k)
        : await O.text.run(mode, text, k);
      if (!r.ok) return showError(r.error);

      // Carry every key-related field into out so result actions can use them.
      out = {
        blob: r.blob,
        text: r.text,
        grouped: r.grouped || '',
        filename: r.filename,
        key: k.key || '',
        preview: k.preview || '',
        keyId: k.keyId || null,
        downloadUrl: k.downloadUrl || null,
        keyFilename: k.filename || null,
        keyType: k.keyType || 'template',
      };

      showResult(mode, r.display, out.grouped, keyMode);
    } catch (err) {
      console.error(err);
      showError('Tidak bisa terhubung ke server.');
    } finally {
      el.submit.disabled = false;
    }
  });

    /* ---------- result rendering ---------- */
  function showResult(mode, display, grouped, keyMode) {
    const noun = mode === 'encrypt' ? 'ciphertext' : 'plaintext';

    // Use out.keyType (stable values from backend) instead of keyMode
    // (which uses UI names like 'default'). This avoids string mismatches.
    const isTemplate = out.keyType === 'template';
    const auto       = out.keyType === 'generated_id';
    const isManual   = out.keyType === 'text';

    const isPreviewOnly = auto && !out.key;

    el.resultTitle.textContent =
      mode === 'encrypt' ? 'Ciphertext Result:' : 'Plaintext Result:';
    el.resultText.value = display;

    el.groupBox.hidden = !grouped;
    el.groupText.value = grouped || '';
    el.groupLabel.textContent = `Grouped ${noun} (5 letters per group):`;

    // Hint text per key type
    if (isTemplate) {
      el.hint.textContent =
        'The template key lives on the server. Click Download to save the full 5,000,000-letter file.';
    } else if (auto) {
      el.hint.textContent = isPreviewOnly
        ? 'The key below is only a preview. Click Download to save the full key file.'
        : 'Copy the key or download it by clicking the download button.';
    } else if (isManual) {
      el.hint.textContent =
        'Your manual key is shown below. Copy or download it to reuse later.';
    } else {
      el.hint.textContent =
        `Copy ${noun} or download it by clicking the 'download' button.`;
    }

    el.share.hidden = true;
    el.copyResult.hidden = false;
    el.hint.hidden = false;
    el.keyResult.hidden = false;   // always show the key panel

    // Key textarea: full key when small, preview when large, label for template
    el.keyOut.value =
      out.key || out.preview || '(key stored on server — click Download)';

    // Hide Copy only when we don't have the full letters locally
    el.copyKey.hidden = isPreviewOnly || isTemplate;

    el.result.hidden = false;
    el.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ---------- result actions ---------- */
  el.dlResult.addEventListener('click', () =>
    save(out.blob || new Blob([out.text], { type: 'text/plain' }), out.filename)
  );

  el.copyResult.addEventListener('click', () =>
    copy(out.text || el.resultText.value, el.copyResult)
  );

  el.dlGroup.addEventListener('click', () =>
    save(
      new Blob([out.grouped], { type: 'text/plain' }),
      out.filename.replace(/\.txt$/i, '_grouped.txt')
    )
  );

  el.copyGroup.addEventListener('click', () =>
    copy(out.grouped, el.copyGroup)
  );

  el.share.addEventListener('click', async () => {
    const payload = out.blob
      ? { files: [new File([out.blob], out.filename)] }
      : { text: out.text };
    if (navigator.canShare && navigator.canShare(payload)) {
      try { await navigator.share(payload); } catch { /* dibatalkan user */ }
    } else if (!out.blob) {
      copy(out.text, el.share);
    } else {
      showError('Browser ini belum mendukung berbagi file. Gunakan Download.');
    }
  });

  /* ---------- download key ---------- */
  el.dlKey.addEventListener('click', async () => {
    // Priority 1: server-side key (auto-generated). Fetch the exact file
    // the backend created — works for any size, avoids the "empty key" bug.
    if (out.downloadUrl) {
      try {
        const res = await fetch(out.downloadUrl);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const name = out.keyFilename
          || `generated_key_${out.keyId || 'auto'}.txt`;
        save(blob, name);
      } catch {
        showError('Gagal mengunduh key. Coba lagi.');
      }
      return;
    }

    // Priority 2: we only know the id but no URL was provided
    if (out.keyId) {
      try {
        const res = await fetch(`/api/key/download/${out.keyId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        save(blob, `generated_key_${out.keyId}.txt`);
      } catch {
        showError('Gagal mengunduh key. Coba lagi.');
      }
      return;
    }

    // Priority 3: manual / template — save whatever the textarea holds
    if (!out.key) {
      showError('Tidak ada key untuk diunduh.');
      return;
    }
    save(new Blob([out.key], { type: 'text/plain' }), 'otp-key.txt');
  });

  el.copyKey.addEventListener('click', () => copy(out.key, el.copyKey));
})();