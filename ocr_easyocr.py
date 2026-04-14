"""
EasyOCR daemon — FaegAz Notes için OCR motoru.

Kurulum:
  pip install easyocr pillow numpy

Kullanım (otomatik, ocr.js tarafından spawn edilir):
  python ocr_easyocr.py --langs en,fr,de

Protokol (JSON Lines, stdin/stdout):
  İstek  (stdin):  {"image": "<base64 PNG>"}
  Yanıt (stdout): {"text": "..."}  veya  {"error": "..."}
"""
import sys
import json
import base64
import io
import urllib.request
import urllib.parse

import numpy as np
from PIL import Image
import easyocr


def translate(text):
    try:
        url = ('https://api.mymemory.translated.net/get?q='
               + urllib.parse.quote(text) + '&langpair=autodetect|tr')
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            result = data.get('responseData', {}).get('translatedText', '')
            return result if result else text
    except Exception:
        return text


# ── Dil listesini argümandan al ──
langs_arg = 'en'
for i, arg in enumerate(sys.argv):
    if arg == '--langs' and i + 1 < len(sys.argv):
        langs_arg = sys.argv[i + 1]
        break
langs = [l.strip() for l in langs_arg.split(',') if l.strip()]

# ── Modelleri yükle ──
reader = easyocr.Reader(langs, gpu=False, verbose=False)
sys.stderr.write('[EasyOCR] Model yüklendi, hazır.\n')
sys.stderr.flush()

# ── Ana döngü ──
for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
        continue
    try:
        data = json.loads(raw)
        img_bytes = base64.b64decode(data['image'])
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img_array = np.array(img)

        result = reader.readtext(img_array, decoder='greedy', beamWidth=1, detail=0)

        seen = set()
        texts = []
        for item in result:
            t = item.strip()
            if t and t not in seen:
                seen.add(t)
                texts.append(t)
        text = ' '.join(texts)
        translated = translate(text) if text else ''
        print(json.dumps({'text': text, 'translated': translated}), flush=True)
    except Exception as exc:
        print(json.dumps({'error': str(exc)}), flush=True)
