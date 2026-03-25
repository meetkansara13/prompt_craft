'use strict';
const UI = {
  esc: s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'),
  estTokens: t => t ? Math.max(1, Math.round(t.trim().length / 4)) : 0,
  liveCount(el, tid, cid) {
    const t = document.getElementById(tid), c = document.getElementById(cid);
    if (t) t.textContent = this.estTokens(el.value).toLocaleString() + ' tokens';
    if (c) c.textContent = el.value.length.toLocaleString() + ' chars';
  },
  toast(msg, type='ok') {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    const colors = { ok:'var(--green2)', warn:'var(--accent2)', err:'var(--rose2)' };
    el.style.borderColor = colors[type]||colors.ok;
    el.style.color = colors[type]||colors.ok;
    el.classList.add('on');
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('on'), 2800);
  },
  copy(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      this.toast('Copied!');
      if (btn) { const o=btn.textContent; btn.textContent='✓ Copied'; btn.classList.add('ok'); setTimeout(()=>{btn.textContent=o;btn.classList.remove('ok');},2000); }
    }).catch(() => this.toast('Copy failed','err'));
  },
  download(filename, content) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content],{type:'text/plain'}));
    a.download = filename; a.click(); URL.revokeObjectURL(a.href);
    this.toast('Downloaded!');
  },
  animLoader(stepIds, messages, ms=600) {
    let i = 0;
    const timer = setInterval(() => {
      if (i > 0 && stepIds[i-1]) { const p = document.getElementById(stepIds[i-1]); if(p) p.className = 'lstep done'; }
      if (i < stepIds.length) { const c = document.getElementById(stepIds[i]); if(c) c.className = 'lstep active'; }
      i++;
      if (i > stepIds.length) clearInterval(timer);
    }, ms);
    return timer;
  },
  finishLoader(stepIds, timerId) {
    clearInterval(timerId);
    stepIds.forEach(id => { const el = document.getElementById(id); if(el) el.className = 'lstep done'; });
  },
};

const KEY = {
  showModal() { document.getElementById('keyOverlay')?.classList.remove('gone'); setTimeout(()=>document.getElementById('keyInput')?.focus(),100); },
  hideModal() { document.getElementById('keyOverlay')?.classList.add('gone'); },
  onInput() {
    const v = document.getElementById('keyInput').value;
    const inp = document.getElementById('keyInput');
    const err = document.getElementById('keyError');
    err.textContent = ''; inp.classList.remove('err','ok');
    if (v.length > 10) {
      if (v.startsWith('gsk_') && v.length > 20) inp.classList.add('ok');
      else if (v.length > 15) { inp.classList.add('err'); err.textContent = 'Groq key must start with gsk_'; }
    }
  },
  toggleVisibility() {
    const inp = document.getElementById('keyInput');
    inp.type = inp.type === 'password' ? 'text' : 'password';
    document.getElementById('keyToggle').textContent = inp.type === 'password' ? '👁' : '🙈';
  },
  async submit() {
    const key = document.getElementById('keyInput').value.trim();
    const err = document.getElementById('keyError');
    const btn = document.getElementById('keySubmit');
    if (!key) { err.textContent = 'Please paste your Groq key'; return; }
    btn.textContent = 'Verifying…'; btn.disabled = true; err.textContent = '';
    try {
      const data = await API.setKey(key);
      document.getElementById('keyInput').value = '';
      this.hideModal();
      this.setStatus(true, data.masked||'');
      UI.toast('API key connected!');
    } catch(e) { err.textContent = e.message||'Key rejected'; document.getElementById('keyInput').classList.add('err'); }
    btn.textContent = 'Connect Free API →'; btn.disabled = false;
  },
  setStatus(set, masked='') {
    const btn  = document.getElementById('keyStatusBtn');
    const text = document.getElementById('keyStatusText');
    if (btn)  btn.classList.toggle('connected', set);
    if (text) text.textContent = set ? (masked||'API Connected') : 'No API Key';
  },
  init(hasKey) {
    if (hasKey) { this.hideModal(); this.setStatus(true); }
    document.getElementById('keyOverlay')?.addEventListener('click', e => { if (e.target.id==='keyOverlay' && hasKey) this.hideModal(); });
  },
};

const APP = {
  switchModule(name) {
    ['gen','img','tok','hist'].forEach(m => {
      document.getElementById(m+'Module')?.classList.toggle('active', m===name);
      document.getElementById(m+'Module')?.classList.toggle('hidden', m!==name);
      document.getElementById('nav'+m.charAt(0).toUpperCase()+m.slice(1))?.classList.toggle('active', m===name);
    });
    if (name === 'hist') HIST.load();
  },
};

const HIST = {
  async load() {
    const el = document.getElementById('histList');
    if (!el) return;
    let items;
    try { items = (await API.listHistory()).items || []; } catch { items = []; }
    if (!items.length) { el.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><div class="empty-title">No history yet</div><div class="empty-sub">Generate a prompt to auto-save it here</div></div>'; return; }
    const colors = {claude:'var(--violet2)',chatgpt:'var(--green2)',gemini:'var(--blue2)',universal:'var(--accent2)',gpt5:'var(--green2)',deepseek:'var(--blue2)',grok:'var(--rose2)'};
    el.innerHTML = `<div class="hist-list">` +
      items.map(item => `<div class="hist-item" onclick="HIST.loadItem(${item.id})"><div class="hist-score">${item.score||'—'}</div><div class="hist-meta"><div class="hist-goal">${UI.esc(item.goal||'Untitled')}</div><div class="hist-tags"><span class="hist-tag" style="color:${colors[item.model]||'var(--t3)'}">${item.model||'claude'}</span>${item.framework?`<span class="hist-tag">${item.framework}</span>`:''}</div></div><div class="hist-ts">${UI.esc(item.timestamp||'')}</div></div>`).join('') +
      `</div><div style="margin-top:12px"><button class="btn-secondary" onclick="HIST.clearAll()">🗑 Clear All</button></div>`;
  },
  async loadItem(id) {
    try {
      const data = await API.getHistory(id);
      const item = data.item;
      if (!item) return;
      APP.switchModule('gen');
      const g = document.getElementById('goalInput');
      if (g) { g.value = item.goal||''; GEN.onGoalInput(g); }
      const m = document.getElementById('g_model'); if (m && item.model) m.value = item.model;
      const f = document.getElementById('g_fw');    if (f && item.framework) f.value = item.framework;
      if (item.full_data && Object.keys(item.full_data).length) {
        GEN.data = item.full_data;
        GEN._showResult();
        UI.toast('Prompt loaded from history');
      }
    } catch { UI.toast('Could not load prompt', 'err'); }
  },
  async clearAll() {
    if (!confirm('Clear all history?')) return;
    await API.clearHistory();
    await this.load();
    UI.toast('History cleared');
  },
};
