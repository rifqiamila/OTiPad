// Menentukan key_type / key_value untuk backend.
(() => {
  const O = (window.OTP = window.OTP || {});

  O.key = {
    async resolve(keyMode, length) {
      // ---------- MANUAL ----------
      if (keyMode === 'manual') {
        const v = document.querySelector('#key-text').value;
        if (!v) return { ok: false, error: 'Masukkan key terlebih dahulu.' };
        return {
          ok: true,
          keyType: 'text',
          keyValue: v,
          key: v,
          preview: '',
          keyId: null,
          downloadUrl: null,
          filename: 'otp-key.txt',
        };
      }

      // ---------- AUTO ----------
      if (keyMode === 'auto') {
        const res = await fetch('/api/key/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ length }),
        });
        let d = {};
        try { d = await res.json(); } catch {}
        if (!res.ok || d.ok === false) {
          return {
            ok: false,
            error: d.message || d.reason || d.error
                   || `Gagal membuat key (HTTP ${res.status}).`,
          };
        }

        const id = d.key_id;
        if (!id) return { ok: false, error: 'Server tidak mengirim key_id.' };

        const downloadUrl = `/api/key/download/${id}`;

        // Fetch the full key only if it's small enough to display
        let fullKey = '';
        if (d.length <= 200_000) {
          try {
            const r = await fetch(downloadUrl);
            if (r.ok) fullKey = await r.text();
          } catch { /* fall back to preview */ }
        }

        return {
          ok: true,
          keyType: 'generated_id',
          keyValue: id,
          key: fullKey,               // '' if too large to inline
          preview: d.preview || '',   // 80-char teaser, separate field
          keyId: id,
          downloadUrl,
          filename: d.download_filename,
        };
      }

      // ---------- TEMPLATE ----------
      return {
        ok: true,
        keyType: 'template',
        keyValue: null,
        key: 'Template key (5,000,000 letters)',
        preview: '',
        keyId: null,
        downloadUrl: '/api/key/template',
        filename: 'key_template.txt',  
      };
    },
  };
})();