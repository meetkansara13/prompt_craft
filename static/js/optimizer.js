'use strict';
const TOK = {
  data: null, currentVer: 'balanced',
  EXAMPLE: `You are a very helpful, friendly, and knowledgeable AI assistant. Please make sure to always be polite and respectful in all your responses. I would like you to please help me with the following task. Could you please try to write a detailed and comprehensive blog post about artificial intelligence? Please make sure the blog post is engaging and interesting to read. The blog post should be around 800-1000 words in length. Please make sure to include an introduction, at least 3 main sections with subheadings, and a conclusion. Please also make sure not to use any technical jargon that might be difficult for a general audience to understand. Try to make it sound natural and conversational. Please ensure the content is accurate and up to date.`,

  init() {},
  loadExample() { const el=document.getElementById('tokInput'); if(el){el.value=this.EXAMPLE;UI.liveCount(el,'tc1','tc2');} UI.toast('Example loaded'); },
  clear() { const el=document.getElementById('tokInput'); if(el)el.value=''; document.getElementById('tokEmpty')?.classList.remove('hidden'); document.getElementById('tokResult')?.classList.add('hidden'); },

  async run() {
    const prompt = document.getElementById('tokInput')?.value.trim();
    if (!prompt) { UI.toast('Paste a prompt first', 'warn'); return; }

    document.getElementById('tokEmpty')?.classList.add('hidden');
    document.getElementById('tokResult')?.classList.add('hidden');
    const l = document.getElementById('tokLoading');
    if (l) { l.classList.remove('hidden'); l.classList.add('fade'); }

    const steps = ['tl1','tl2','tl3','tl4','tl5'];
    const msgs  = ['Tokenizing…','Detecting waste…','Compressing…','Validating…','Generating tips…'];
    const tid   = UI.animLoader(steps, msgs, 560);

    try {
      const result = await API.optimize({
        prompt,
        target_model: document.getElementById('t_model')?.value || 'universal',
        level:        document.getElementById('t_level')?.value || 'balanced',
        sensitivity:  'general',
        techniques:   ['semantic','structure','cod','filler','negative','primacy'],
      });

      UI.finishLoader(steps, tid);
      this.data = result.data;
      document.getElementById('tokLoading')?.classList.add('hidden');
      this._render(this.data, prompt);
      const r = document.getElementById('tokResult');
      if (r) { r.classList.remove('hidden'); r.classList.add('fade'); }
      r?.scrollIntoView({ behavior:'smooth', block:'start' });

    } catch(err) {
      UI.finishLoader(steps, tid);
      document.getElementById('tokLoading')?.classList.add('hidden');
      if (err.message?.includes('401')) KEY.showModal();
      UI.toast(err.message || 'Optimization failed', 'err');
    }
  },

  _render(d, origPrompt) {
    const a=d.analysis||{}, v=d.versions||{}, q=d.quality||{};
    const ot=a.original_tokens||UI.estTokens(origPrompt), opt=v.balanced?.tokens||Math.round(ot*.63), red=v.balanced?.pct||Math.round((1-opt/ot)*100);

    this._animNum('tm1', ot,  '',  'red');
    this._animNum('tm2', opt, '',  'green');
    this._animNum('tm3', red, '%', 'gold');
    this._animNum('tm4', q.semantic_retention||95, '%', 'teal');
    const d2=document.getElementById('td2'); if(d2){d2.textContent=`−${(ot-opt).toLocaleString()} tokens saved`;d2.style.color='var(--green2)';}

    // Breakdown bars
    const tb = document.getElementById('tokBreakdown');
    if (tb) tb.innerHTML = (a.token_breakdown||[]).map(item=>`<div class="prog-row"><div class="prog-lbl">${UI.esc(item.category||'')}</div><div class="prog-track"><div class="prog-fill pf-${item.color||'gold'}" data-w="${item.pct||0}" style="width:0"></div></div><div class="prog-val">${item.tokens||0}tk</div></div>`).join('');
    setTimeout(()=>document.querySelectorAll('.prog-fill[data-w]').forEach(el=>el.style.width=el.dataset.w+'%'),200);

    // Issues
    const ti = document.getElementById('tokIssues');
    const SC={high:'h',medium:'m',low:'l',info:'i'};
    if (ti) ti.innerHTML = (a.issues||[]).map(i=>`<div class="issue ${SC[i.severity]||'i'}"><div class="issue-ico">${i.icon||'•'}</div><div class="issue-body"><div class="issue-title">${UI.esc(i.title||'')}</div><div class="issue-desc">${UI.esc(i.desc||'')}</div>${i.save?`<div class="issue-save">💾 ${UI.esc(i.save)}</div>`:''}</div><div class="issue-sev sev-${SC[i.severity]||'i'}">${(i.severity||'i')[0].toUpperCase()}</div></div>`).join('');

    this.switchVer('balanced');
  },

  switchVer(ver) {
    this.currentVer = ver;
    document.querySelectorAll('.ver-tabs .vtab').forEach(t=>t.classList.remove('active'));
    document.querySelector(`.vtab[data-v="${ver}"]`)?.classList.add('active');
    const v = this.data?.versions?.[ver]; if (!v) return;
    const out = document.getElementById('tokOutput'); if (out) out.textContent = v.prompt||'';
  },

  copy() { UI.copy(this.data?.versions?.[this.currentVer]?.prompt||'', document.getElementById('tokCopyBtn')); },
  download() { if (this.data) { const v=this.data.versions||{}; UI.download('tokenlens-v4.txt',['TOKENLENS PRO v4',new Date().toLocaleString(),'═'.repeat(60),'','BALANCED:',v.balanced?.prompt||'','','AGGRESSIVE:',v.aggressive?.prompt||'','','ULTRA:',v.ultra?.prompt||''].join('\n')); } },

  _animNum(id, to, suffix, cls) {
    const el = document.getElementById(id); if (!el) return;
    el.className = 'metric-val ' + cls;
    let c=0, step=Math.max(1,Math.round(to/40));
    const t=setInterval(()=>{ c=Math.min(c+step,to); el.textContent=c.toLocaleString()+suffix; if(c>=to)clearInterval(t); },22);
  },
};
