// Mode teks: kirim JSON, terima JSON.
(() => {
  const O = (window.OTP = window.OTP || {});

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
      // ASUMSI: nama field hasil di JSON
      const out = d.ciphertext ?? d.plaintext ?? d.result ?? '';
      return { ok: true, display: out, text: out, blob: null, filename: `${mode}ed.txt` };
    },
  };
})();