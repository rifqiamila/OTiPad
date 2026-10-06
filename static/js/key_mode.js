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

        const id = d.key_id;
        if (!id) return { ok: false, error: 'Server tidak mengirim key_id.' };

        const downloadUrl = `/api/key/download/${id}`;

        // Ambil kunci utuh hanya kalau cukup kecil untuk ditampilkan di layar
        let fullKey = '';
        if (d.length <= 5000000) {
          const r = await fetch(downloadUrl);
          if (r.ok) fullKey = await r.text();
        }

        return {
          ok: true,
          keyType: 'generated_id',
          keyValue: id,
          key: fullKey,              // terisi kalau kunci <= 200.000 karakter
          keyId: id,
          preview: d.preview,        // potongan awal, untuk kunci besar
          downloadUrl,               // untuk tombol "Unduh kunci"
          filename: d.download_filename,
        };
      }
      return { ok: true, keyType: 'template', keyValue: null, key: '' };
    },
  };
})();