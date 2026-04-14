# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm install       # Bağımlılıkları yükle
npm start         # Geliştirme modunda çalıştır (electron .)
npm run build     # dist/FaegAz Notes 1.0.0.exe üret
```

Test veya lint komutu yok.

## Proje Özeti

Windows Electron masaüstü uygulaması. Notlar, görevler, kelime kartları, alışkanlık takibi, takvim ve OCR/çeviri özellikleri. UI Türkçe, kod İngilizce yorumlu.

## Dosya Haritası

```
src/
  main/
    index.js       ← Ana process: pencere yönetimi, IPC, tray, bildirimler
    preload.js     ← contextBridge ile renderer'a window.api expose eder
  modules/
    storage.js     ← SQLite (sql.js) — tüm DB işlemleri
    ocr.js         ← EasyOCR Python daemon yönetimi + Sharp görüntü işleme
    translator.js  ← MyMemory API çevirisi (autodetect → Türkçe)
  renderer/
    main.html      ← Ana pencere HTML + CSS (780×540)
    main-app.js    ← Ana pencere JS mantığı
    index.html     ← Floating panel HTML + CSS (272×480)
    app.js         ← Floating panel JS mantığı
    screen-select.html ← Tam ekran OCR bölge seçici overlay
ocr_easyocr.py     ← Python OCR daemon (stdin/stdout JSON Lines)
```

## Mimari

### 3 BrowserWindow

| Pencere | Boyut | Özellik |
|---|---|---|
| Ana pencere | 780×540 | Frameless, tray'e küçülür |
| Floating panel | 272×480 | alwaysOnTop `screen-saver` seviyesi (oyunların üstünde kalır), Alt+Shift+1 |
| Screen select | Tam ekran | OCR bölge seçimi için crosshair overlay |

### IPC Kanalları (window.api.*)

Tüm renderer↔main iletişimi `preload.js` üzerinden geçer. Mevcut API:

```
// Pencere
hideWindow, minimizeWindow, maximizeWindow, openFloatingPanel

// Notlar (notes tablosu, type='note')
addNote(content, title), getNotes(), updateNoteTitle(id, title),
deleteNote(id), searchNotes(query)

// Görevler
addTodo(text), getTodos(), toggleTodo(id), deleteTodo(id)

// Kelimeler (notes tablosu, type='word')
addWord(original, translated), deleteNote(id)

// Alışkanlıklar
createHabit(title, totalDays), getHabits(),
toggleHabitDay(habitId, day), deleteHabit(id)

// Takvim
addCalendarEvent(date, text), getCalendarEvents(), deleteCalendarEvent(id)

// OCR
startScreenCapture(mode)   // mode: 'word' | 'note'

// OCR Dil Ayarları
getOcrLangs()              // { available: [...], enabled: [...] }
setOcrLangs(langs)         // lang kodları dizisi, her zaman 'en' içerir

// Olaylar (main→renderer)
onDataChanged(callback)    // OCR ile veri eklenince tetiklenir
```

### DB Şeması (sql.js, %APPDATA%/faegaz-notes/faegaz.db)

```sql
notes(id, type TEXT, title TEXT, content TEXT, original TEXT,
      translated TEXT, created_at TEXT)
  -- type='note' → not | type='word' → kelime kartı

todos(id, text TEXT, done INTEGER, created_at TEXT)

habits(id, title TEXT, total_days INTEGER, created_at TEXT)
habit_checks(id, habit_id INTEGER, day INTEGER)

calendar_events(id, date TEXT, text TEXT)
```

### OCR Akışı

1. Floating panel `startScreenCapture(mode)` çağırır
2. Panel fade-out animasyonuyla şeffaflaşır (ekran görüntüsüne girmesin)
3. screenshot-desktop ile tam ekran PNG alınır
4. `screen-select.html` overlay açılır, kullanıcı bölge seçer
5. Sharp ile kırp + gri ton + normalize
6. `ocr_easyocr.py` daemon'a JSON Lines ile gönderilir: `{"image": "<base64>"}`
7. Python EasyOCR metni okur, MyMemory API ile Türkçeye çevirir
8. Sonuç storage'a kaydedilir, her iki pencereye `data-changed` eventi gönderilir
9. Panel fade-in ile geri döner

### OCR Dil Yönetimi

- Aktif diller `%APPDATA%/faegaz-notes/ocr-langs.json`'da saklanır
- `setOcrLangs()` daemon'u yeniden başlatır (EasyOCR modeli otomatik indirir)
- İngilizce her zaman zorunlu
- Latin alfabesi dilleri (fr, de, es, it vb.) ekstra indirme gerektirmez
- Farklı alfabe dilleri (ja, ko, ru, ar vb.) ~40-50MB model indirir

### Takvim Bildirimleri

Uygulama açılışında ve her gece yarısı `checkCalendarNotifications()` çalışır.
Electron `Notification` API'si ile Windows bildirimi gösterir.

### Önemli Kalıplar

- Renderer'da yeni IPC kanalı eklemek için: `preload.js` + `index.js setupIPC()` + `window.api.*` çağrısı
- `storage.js` senkron çalışır (sql.js in-memory, dosyaya periyodik flush)
- Floating panel hem `app.js` hem `main-app.js`'den bağımsız çalışır — her ikisinde de aynı veri işlemleri tekrarlanır
- `escapeHtml()` her iki renderer dosyasında ayrı tanımlı (XSS koruması)
