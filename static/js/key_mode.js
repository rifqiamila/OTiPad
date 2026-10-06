// Menentukan key_type / key_value untuk backend.
(() => {
  const O = (window.OTP = window.OTP || {});

  O.key = {
    // keyMode: 'manual' | 'auto' | 'default'
    async resolve(keyMode, length) {
      if (keyMode === 'manual') {
        const v = document.querySelector('#key-text').value;
        if (!v) return { ok: false, error: 'Masukkan key terlebih dahulu.' };
        return { ok: true, keyType: 'text', keyValue: v, key: v, keyId: null };
      }
      if (keyMode === 'auto') {
        const res = await fetch('/api/key/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ length }),
        });
        let d = {};
        try { d = await res.json(); } catch {}
        if (!res.ok || d.ok === false) {
          return { ok: false, error: d.message || d.reason || d.error
                  || `Gagal membuat key (HTTP ${res.status}).` };
        }

        const id = d.key_id ?? d.id ?? d.generated_id;
        if (!id) return { ok: false, error: 'Backend tidak mengembalikan key_id.' };

        return {
          ok: true,
          keyType: 'generated_id',
          keyValue: id,
          key: d.preview || '(preview only)',
          keyId: id,
        };
      }
      return { ok: true, keyType: 'template', keyValue: null,
              key: 'Template key (5,000,000 letters)', keyId: null };
    },
  };
})();