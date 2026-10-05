// Mode teks: kirim JSON, terima JSON.
(() => {
  const O = (window.OTP = window.OTP || {});

  // Cadangan kalau server tidak mengirim field `grouped`
  const group5 = (s) => (s.match(/.{1,5}/g) || []).join(' ');

  O.text = {
    async run(mode, text, k) {
      const field = mode === 'encrypt' ? 'plaintext' : 'ciphertext';
      const res = await fetch(`/api/${mode}/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: text, key_type: k.keyType, key_value: k.keyValue }),
      });
      const d = await res.json();
      if (!d.ok) return { ok: false, error: O.errMsg(d) };

      const raw = d.ciphertext ?? d.plaintext ?? '';
      return {
        ok: true,
        display: raw,                       // kotak atas: tanpa grup
        grouped: d.grouped ?? group5(raw),  // kotak bawah: HELLO WORLD XYZAB
        text: raw,
        blob: null,
        filename: `${mode}ed.txt`,
      };
    },
  };

  // Isi textarea dari file .txt (tombol "Pilih .txt" atau drag & drop ke kotak)
  O.attachTxt = (box) => {
    const ta = box.querySelector('textarea');
    const pick = box.querySelector('.txt-file');
    const load = async (f) => {
      if (!f) return;
      if (!/\.txt$/i.test(f.name) && f.type !== 'text/plain') {
        return O.showError('Hanya file .txt yang bisa dimuat ke kotak ini.');
      }
      O.showError('');
      ta.value = await f.text();
    };
    pick.addEventListener('change', async () => { await load(pick.files[0]); pick.value = ''; });
    ['dragenter', 'dragover'].forEach((ev) =>
      box.addEventListener(ev, (e) => { e.preventDefault(); box.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((ev) =>
      box.addEventListener(ev, (e) => { e.preventDefault(); box.classList.remove('over'); }));
    box.addEventListener('drop', (e) => load(e.dataTransfer.files[0]));
  };
})();