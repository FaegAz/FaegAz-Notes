// MyMemory API — otomatik dil algılama ile Türkçeye çevirir
async function translate(text) {
  const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=autodetect|tr`;
  const response = await fetch(url);
  const data = await response.json();
  return data.responseData?.translatedText || text;
}

module.exports = { translate };
