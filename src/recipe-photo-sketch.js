/* Converte as fotografias originais para ilustrações monocromáticas.
   Somente a impressão muda: fotos e arquivos no Supabase permanecem intactos. */
(function () {
  'use strict';

  const images = [...document.querySelectorAll('img[data-recipe-sketch]')];

  function finish(img, dataUrl) {
    if (!img.isConnected) return;
    if (dataUrl) {
      img.src = dataUrl;
      img.removeAttribute('crossorigin');
      img.classList.add('sketch-rendered');
    } else {
      // Filtragem monocromática de segurança para imagens sem permissão CORS.
      img.classList.add('sketch-fallback');
    }
  }

  async function convert(img) {
    const source = img.getAttribute('src');
    if (!source) return;
    try {
      const input = new Image();
      input.crossOrigin = 'anonymous';
      input.decoding = 'async';
      await new Promise((resolve, reject) => {
        input.onload = resolve;
        input.onerror = () => reject(new Error('Imagem indisponível para conversão.'));
        input.src = source;
      });

      const w = 720, h = 480;
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) throw new Error('Canvas não disponível.');
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h);
      const sw = input.naturalWidth || input.width;
      const sh = input.naturalHeight || input.height;
      if (!sw || !sh) throw new Error('Foto sem tamanho válido.');
      const scale = Math.max(w / sw, h / sh);
      const cropW = w / scale, cropH = h / scale;
      ctx.drawImage(input, (sw - cropW) / 2, (sh - cropH) / 2, cropW, cropH, 0, 0, w, h);

      const data = ctx.getImageData(0, 0, w, h);
      const pixels = data.data;
      const n = w * h;
      const luma = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        const j = i * 4;
        luma[i] = .299 * pixels[j] + .587 * pixels[j + 1] + .114 * pixels[j + 2];
      }

      // Leve suavização evita contornos pontilhados, mantendo detalhes do produto.
      const smooth = new Float32Array(n);
      for (let y = 1; y < h - 1; y++) {
        for (let x = 1; x < w - 1; x++) {
          const i = y * w + x;
          smooth[i] = (luma[i - w - 1] + 2*luma[i - w] + luma[i - w + 1] +
                       2*luma[i - 1] + 4*luma[i] + 2*luma[i + 1] +
                       luma[i + w - 1] + 2*luma[i + w] + luma[i + w + 1]) / 16;
        }
      }
      for (let x = 0; x < w; x++) {
        smooth[x] = luma[x]; smooth[(h - 1) * w + x] = luma[(h - 1) * w + x];
      }
      for (let y = 0; y < h; y++) {
        smooth[y * w] = luma[y * w];
        smooth[y * w + w - 1] = luma[y * w + w - 1];
      }

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const i = y * w + x;
          const pos = i * 4;
          let ink = 0;
          if (x > 0 && y > 0 && x < w - 1 && y < h - 1) {
            const a = smooth[i - w - 1], b = smooth[i - w], c = smooth[i - w + 1];
            const d = smooth[i - 1], f = smooth[i + 1];
            const g = smooth[i + w - 1], hh = smooth[i + w], k = smooth[i + w + 1];
            const gx = -a + c - 2*d + 2*f - g + k;
            const gy = -a - 2*b - c + g + 2*hh + k;
            const edge = Math.sqrt(gx*gx + gy*gy);
            const outline = Math.min(235, Math.max(0, edge - 24) * 1.10);
            const dark = Math.pow((255 - smooth[i]) / 255, 2.1);
            const pencil = dark * 33;
            const hatch = dark > .16 && ((x + y) % 10 === 0) ? dark * 38 : 0;
            ink = Math.max(outline, pencil + hatch);
          }
          const shade = Math.max(0, 255 - Math.min(252, ink));
          pixels[pos] = pixels[pos + 1] = pixels[pos + 2] = shade;
          pixels[pos + 3] = 255;
        }
      }
      ctx.putImageData(data, 0, 0);
      finish(img, canvas.toDataURL('image/png'));
    } catch (err) {
      finish(img, null);
    }
  }

  const ready = Promise.all(images.map(convert));
  window.RecipeSketch = { ready };
})();