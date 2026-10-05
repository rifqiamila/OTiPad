// Menentukan key_type / key_value untuk backend.
(() => {
  const O = (window.OTP = window.OTP || {});

  O.key = {
    // keyMode: 'manual' | 'auto' | 'default'
    async resolve(keyMode, length) {
      if (keyMode === 'manual') {
        const v = document.querySelector('#key-text').value;
        if (!v) return { ok: false, error: 'Masukkan key terlebih dahulu.' };
        return { ok: true, keyType: 'text', keyValue: v, key: '' };
      }
      if (keyMode === 'auto') {
        // length dikirim lewat JSON body DAN query string (?length=N) supaya cocok
        // dengan route yang membaca salah satunya. Sesuaikan jika nama param berbeda.
        const res = await fetch(`/api/key/generate?length=${length}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ length }),
        });
        let d = {};
        try { d = await res.json(); } catch { /* bukan JSON */ }
        if (!res.ok || d.ok === false) {
          return { ok: false, error: d.message || d.reason || d.error || `Gagal membuat key (HTTP ${res.status}).` };
        }
        console.log('keygen response:', d);   // lihat bentuk respons di DevTools > Console

        // 1) nama field yang umum  2) cari string A-Z sepanjang key di dalam respons
        const flat = (o) => Object.values(o).flatMap((v) =>
          v && typeof v === 'object' ? flat(v) : [v]);
        const key = d.key ?? d.key_value ?? d.key_text ?? d.generated_key ?? d.letters
          ?? d.data?.key ?? d.result
          ?? flat(d).find((v) => typeof v === 'string' && v.length >= Math.min(length, 8)
                                 && /^[A-Za-z\s]+$/.test(v));
        if (key) return { ok: true, keyType: 'text', keyValue: key, key };

        // 3) hanya id yang dikembalikan -> pakai generated_id (key tidak bisa ditampilkan)
        const id = d.key_id ?? d.id ?? d.generated_id;
        if (id) return { ok: true, keyType: 'generated_id', keyValue: id, key: '' };

        return { ok: false, error: 'Respons key tidak dikenali. Lihat Console (keygen response) lalu kirim isinya.' };
      }
      return { ok: true, keyType: 'template', keyValue: null, key: '' };
    },
  };
})();