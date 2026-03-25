'use strict';
const API = {
  async _post(url, body) {
    const res  = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  },
  async _get(url) {
    const res  = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  },
  setKey(key)          { return this._post('/api/key/set', { key }); },
  clearKey()           { return this._post('/api/key/clear', {}); },
  keyStatus()          { return this._get('/api/key/status'); },
  generate(payload)    { return this._post('/api/generator/generate', payload); },
  refine(payload)      { return this._post('/api/generator/refine', payload); },
  optimize(payload)    { return this._post('/api/optimizer/optimize', payload); },
  saveHistory(payload) { return this._post('/api/history/save', payload); },
  listHistory()        { return this._get('/api/history/list'); },
  getHistory(id)       { return this._get(`/api/history/${id}`); },
  clearHistory()       { return this._post('/api/history/clear', {}); },
  analyzeImage(payload){ return this._post('/api/image/analyze', payload); },
  getTemplates()       { return this._get('/api/templates'); },
};
