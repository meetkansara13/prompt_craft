/* PromptCraft Pro v4 — Generator + Image Module */
'use strict';

const GEN = {
  data: null, refineCount: 0, currentModel: 'claude',
  selectedTones: ['professional'], selectedTechs: ['cot','fewshot','role'], selectedCheats: [],

  init() {
    document.querySelectorAll('#toneRow .chip').forEach(c => c.addEventListener('click', () => {
      c.classList.toggle('on'); this.selectedTones = [...document.querySelectorAll('#toneRow .chip.on')].map(x => x.dataset.v);
    }));
    document.querySelectorAll('#techRow .chip').forEach(c => c.addEventListener('click', () => {
      c.classList.toggle('on'); this.selectedTechs = [...document.querySelectorAll('#techRow .chip.on')].map(x => x.dataset.v);
    }));
    document.querySelectorAll('#cheatRow .chip').forEach(c => c.addEventListener('click', () => {
      c.classList.toggle('on'); this.selectedCheats = [...document.querySelectorAll('#cheatRow .chip.on')].map(x => x.dataset.v);
    }));
  },

  onGoalInput(el) {
    const tc = document.getElementById('genTokenCount');
    const cc = document.getElementById('genCharCount');
    const t = UI.estTokens(el.value);
    if (tc) tc.textContent = t.toLocaleString() + ' tokens';
    if (cc) cc.textContent = el.value.length.toLocaleString() + ' chars';
  },

  toggleAdvanced() {
    const body = document.getElementById('advBody');
    const arrow = document.getElementById('advArrow');
    body.classList.toggle('hidden');
    if (arrow) arrow.textContent = body.classList.contains('hidden') ? '▼' : '▲';
  },

  async loadTemplates() {
    const scroll = document.getElementById('templateScroll');
    if (!scroll) return;
    try {
      const data = await API.getTemplates();
      scroll.innerHTML = '';
      (data.templates || []).forEach(t => {
        const btn = document.createElement('button');
        btn.className = 'template-btn';
        btn.innerHTML = `<span class="t-icon">${t.icon}</span> ${t.label}`;
        btn.onclick = () => this.applyTemplate(t);
        scroll.appendChild(btn);
      });
    } catch { scroll.innerHTML = '<div class="template-loading" style="color:var(--t3)">Templates unavailable</div>'; }
  },

  applyTemplate(t) {
    const g = document.getElementById('goalInput');
    if (g) { g.value = t.goal; this.onGoalInput(g); }
    const m = document.getElementById('g_model');  if (m) m.value = t.model;
    const c = document.getElementById('g_cat');    if (c) c.value = t.category;
    const f = document.getElementById('g_fw');     if (f) f.value = t.framework;
    const x = document.getElementById('g_cplx');   if (x) x.value = t.complexity;
    // Apply techniques
    this.selectedTechs = t.techniques || [];
    document.querySelectorAll('#techRow .chip').forEach(chip => {
      chip.classList.toggle('on', this.selectedTechs.includes(chip.dataset.v));
    });
    UI.toast(`Template loaded: ${t.label}`);
  },

  async generate() {
    const goal = document.getElementById('goalInput')?.value.trim();
    if (!goal) { UI.toast('Please describe your goal first', 'warn'); return; }

    this._showLoading();
    this.refineCount = 0;

    const steps = ['ls1','ls2','ls3','ls4','ls5','ls6'];
    const msgs  = ['Detecting intent…','Selecting framework…','Injecting expertise…','Applying cheat codes…','Structuring sections…','Scoring & assembling…'];
    const tid   = UI.animLoader(steps, msgs, 700);

    try {
      const result = await API.generate({
        goal,
        model:         document.getElementById('g_model')?.value || 'claude',
        category:      document.getElementById('g_cat')?.value   || 'auto',
        output_format: 'auto',
        complexity:    document.getElementById('g_cplx')?.value  || 'auto',
        tones:         this.selectedTones,
        framework:     document.getElementById('g_fw')?.value    || 'RISEN',
        techniques:    this.selectedTechs,
        cheat_codes:   this.selectedCheats,
      });

      UI.finishLoader(steps, tid);
      this.data = result.data;
      this._showResult();

      API.saveHistory({
        goal,
        model:     document.getElementById('g_model')?.value || 'claude',
        framework: document.getElementById('g_fw')?.value    || 'RISEN',
        score:     this.data?.quality_score?.score || 0,
        prompt:    this.data?.final_prompt || '',
        full_data: this.data || {},
      }).catch(() => {});

    } catch(err) {
      UI.finishLoader(steps, tid);
      this._hideLoading();
      if (err.message?.includes('401')) KEY.showModal();
      UI.toast(err.message || 'Generation failed', 'err');
    }
  },

  async refine() {
    const feedback = document.getElementById('refineFeedback')?.value.trim();
    if (!feedback || !this.data) { UI.toast('Generate first, then describe your feedback', 'warn'); return; }
    const btn = document.getElementById('refineBtn');
    if (btn) { btn.textContent = '⟳ Refining…'; btn.disabled = true; }
    try {
      const result = await API.refine({ current_prompt: this.data.final_prompt || '', feedback });
      const d = result.data;
      if (d.improved_prompt) this.data.final_prompt = d.improved_prompt;
      if (d.token_optimized_prompt) this.data.token_optimized_prompt = d.token_optimized_prompt;
      if (d.quality_score) this.data.quality_score = { ...this.data.quality_score, ...d.quality_score };
      this.refineCount++;
      this._renderScore(this.data.quality_score);
      this._renderModelOutput();
      const lbl = document.getElementById('refineLabel');
      if (lbl) lbl.innerHTML = `Refine & Iterate <span style="background:var(--tglow);border:1px solid rgba(48,191,172,.3);color:var(--teal2);padding:1px 8px;border-radius:20px;font-size:10px;margin-left:6px">${this.refineCount} applied</span>`;
      document.getElementById('refineFeedback').value = '';
      UI.toast(`✓ Refined — iteration ${this.refineCount}`);
      API.saveHistory({ goal: document.getElementById('goalInput')?.value||'', model: document.getElementById('g_model')?.value||'claude', framework: document.getElementById('g_fw')?.value||'RISEN', score: this.data.quality_score?.score||0, prompt: this.data.final_prompt||'', full_data: this.data }).catch(()=>{});
    } catch(err) { UI.toast(err.message || 'Refine failed', 'err'); }
    if (btn) { btn.textContent = '⟳ Refine'; btn.disabled = false; }
  },

  switchModel(m) {
    this.currentModel = m;
    document.querySelectorAll('#modelTabs .mtab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#modelTabs [data-m="${m}"]`)?.classList.add('active');
    this._renderModelOutput();
  },

  copyModel() { UI.copy(this.data?.model_variants?.[this.currentModel] || this.data?.final_prompt || '', document.getElementById('copyModelBtn')); },
  copyOptimized() { UI.copy(this.data?.token_optimized_prompt || this.data?.final_prompt || '', document.getElementById('copyOptBtn')); },

  downloadAll() {
    if (!this.data) return;
    const mv = this.data.model_variants || {};
    UI.download('promptcraft-v4-prompt.txt', [
      'PROMPTCRAFT PRO v4 — Generated Prompt', new Date().toLocaleString(), '═'.repeat(60), '',
      'FINAL PROMPT:', this.data.final_prompt||'', '',
      '─'.repeat(60), '⚡ TOKEN-OPTIMIZED:', this.data.token_optimized_prompt||'', '',
      '─'.repeat(60), 'CLAUDE:', mv.claude||'', '', '─'.repeat(60), 'CHATGPT:', mv.chatgpt||'', '',
      '─'.repeat(60), 'GEMINI:', mv.gemini||'', '', '─'.repeat(60), 'GPT-5:', mv.gpt5||'', '',
      '─'.repeat(60), 'DEEPSEEK:', mv.deepseek||'', '', '─'.repeat(60), 'GROK:', mv.grok||'', '',
      '─'.repeat(60), 'UNIVERSAL:', mv.universal||'',
    ].join('\n'));
  },

  // ── Private render ────────────────────────────────────────────────────
  _showLoading() {
    document.getElementById('genEmpty')?.classList.add('hidden');
    document.getElementById('genResult')?.classList.add('hidden');
    const l = document.getElementById('genLoading');
    if (l) { l.classList.remove('hidden'); l.classList.add('fade'); }
    document.querySelectorAll('[id^="ls"]').forEach(el => el.className = 'lstep');
  },

  _hideLoading() {
    document.getElementById('genLoading')?.classList.add('hidden');
  },

  _showResult() {
    this._hideLoading();
    const r = document.getElementById('genResult');
    if (r) { r.classList.remove('hidden'); r.classList.add('fade'); }
    this._renderScore(this.data.quality_score);
    this._renderDiagram(this.data.diagram_data);
    this._renderAnalysis(this.data.analysis, this.data.quality_score);
    this._renderSections(this.data.prompt_sections, this.data.final_prompt, this.data.token_optimized_prompt);
    this._renderModelOutput();
    this._renderRefineQuick();
    this._renderExpls(this.data.explanations);
    document.getElementById('genResult')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  },

  _renderScore(q) {
    if (!q) return;
    const score = q.score || 85;
    const fill  = document.getElementById('scoreRingFill');
    const num   = document.getElementById('scoreNum');
    const grade = document.getElementById('scoreGrade');
    const sub   = document.getElementById('scoreSub');
    const color = score >= 90 ? 'var(--green2)' : score >= 75 ? 'var(--accent2)' : score >= 55 ? 'var(--teal2)' : 'var(--rose2)';
    if (fill) { fill.style.stroke = color; setTimeout(() => { let c=0; const t=setInterval(()=>{ c=Math.min(c+2,score); if(num) num.textContent=c; if(fill) fill.style.strokeDashoffset=175.9-(175.9*c/100); if(c>=score)clearInterval(t); },18); },300); }
    if (grade) { grade.textContent = (q.grade||'Good') + ' Prompt'; grade.style.color = color; }
    if (sub) sub.textContent = `Clarity ${q.clarity||0}% · Specificity ${q.specificity||0}% · Techniques ${q.technique_use||0}%`;
    const bars = document.getElementById('scoreBars');
    if (bars) { bars.innerHTML = ['clarity','specificity','technique_use','completeness'].map(k => `<div class="sbar"><div class="sbar-lbl">${k.replace('_',' ')}</div><div class="sbar-track"><div class="sbar-fill" data-w="${q[k]||0}"></div></div><div class="sbar-val">${q[k]||0}%</div></div>`).join(''); setTimeout(()=>{ document.querySelectorAll('.sbar-fill[data-w]').forEach(el=>el.style.width=el.dataset.w+'%'); },200); }
  },

  _renderDiagram(dd) {
    const el = document.getElementById('promptDiagram');
    if (!el || !dd?.sections) return;
    const colors = { violet:'var(--violet2)', gold:'var(--accent2)', teal:'var(--teal2)', green:'var(--green2)', rose:'var(--rose2)', blue:'var(--blue2)' };
    el.innerHTML = '<div class="diagram">' +
      dd.sections.map((s,i) => `<div class="diag-row">${i>0?'<div class="diag-arrow">↓</div>':''}<div class="diag-box" style="border-left:3px solid ${colors[s.color]||'var(--t3)'}"><div class="diag-label" style="color:${colors[s.color]||'var(--t3)'}">${s.label}</div><div class="diag-summary">${UI.esc(s.summary||'')}</div><div class="diag-tokens">~${s.tokens||0} tokens</div></div></div>`).join('') +
      `<div style="margin-top:8px;font-size:11px;color:var(--t3);font-family:var(--mono)">Total: ~${dd.total_tokens||0} tokens · Optimized: ~${dd.optimized_tokens||0} tokens</div>` +
      '</div>';
  },

  _renderAnalysis(a, q) {
    const el = document.getElementById('genAnalysis');
    if (!el || !a) return;
    let html = `
      <div class="achip"><div class="achip-l">Detected Intent</div><div class="achip-v av-gold">${UI.esc(a.detected_intent||'—')}</div></div>
      <div class="achip"><div class="achip-l">Type · Domain</div><div class="achip-v av-teal">${UI.esc(a.task_type||'—')} · ${UI.esc(a.detected_domain||'—')}</div></div>
      <div class="achip"><div class="achip-l">Complexity</div><div class="achip-v av-violet">${UI.esc(a.complexity||'—')}</div></div>
      <div class="achip"><div class="achip-l">Domain Expert</div><div class="achip-v av-gold">${UI.esc(a.domain_expertise_used||'—')}</div></div>
    `;
    if ((a.key_requirements||[]).length) html += `<div class="achip full"><div class="achip-l">Key Requirements</div><div class="tag-list">${a.key_requirements.map(r=>`<span class="tag">${UI.esc(r)}</span>`).join('')}</div></div>`;
    if ((a.ambiguities_resolved||[]).length) html += `<div class="achip full"><div class="achip-l">Ambiguities Resolved</div><div class="tag-list">${a.ambiguities_resolved.map(r=>`<span class="tag" style="color:var(--accent2)">${UI.esc(r)}</span>`).join('')}</div></div>`;
    if ((q?.improvements||[]).length) html += `<div class="achip full" style="border-color:rgba(200,153,58,.2)"><div class="achip-l" style="color:var(--accent2)">Improvements Suggested</div><div class="tag-list">${q.improvements.map(r=>`<span class="tag" style="color:var(--accent2)">${UI.esc(r)}</span>`).join('')}</div></div>`;
    el.innerHTML = html;
  },

  _renderSections(ps, final, optimized) {
    const el = document.getElementById('genSections');
    if (!el || !ps) return;
    const secs = [
      {key:'system_context',    badge:'pb-role', lbl:'ROLE',         title:'Expert Persona'},
      {key:'context_background',badge:'pb-ctx',  lbl:'CONTEXT',      title:'Background & Situation'},
      {key:'main_task',         badge:'pb-task', lbl:'TASK',         title:'Core Instructions'},
      {key:'examples_format',   badge:'pb-ex',   lbl:'EXAMPLES',     title:'INPUT→OUTPUT Examples'},
      {key:'constraints_rules', badge:'pb-con',  lbl:'CONSTRAINTS',  title:'Hard Rules'},
      {key:'self_check',        badge:'pb-ver',  lbl:'VERIFICATION', title:'Self-Check Checklist'},
    ];
    el.innerHTML = secs.filter(s=>ps[s.key]).map(s => {
      const uid = 'ps_'+s.key;
      return `<div class="psec"><div class="psec-hdr"><div style="display:flex;align-items:center;gap:7px"><span class="psec-badge ${s.badge}">${s.lbl}</span><span style="font-size:11px;color:var(--t3)">${s.title}</span></div><button class="btn-copy" onclick="UI.copy(document.getElementById('${uid}').textContent,this)">Copy</button></div><div class="psec-body" id="${uid}">${UI.esc(ps[s.key])}</div></div>`;
    }).join('');
    if (final) el.innerHTML += `<div class="psec" style="border-color:rgba(78,192,116,.2)"><div class="psec-hdr"><div style="display:flex;align-items:center;gap:7px"><span class="psec-badge pb-fin">FINAL</span><span style="font-size:11px;color:var(--green2)">Complete assembled prompt</span></div><button class="btn-copy" onclick="UI.copy(document.getElementById('psFinal').textContent,this)">Copy All</button></div><div class="psec-body" id="psFinal">${UI.esc(final)}</div></div>`;
    if (optimized) { const ot=UI.estTokens(final||''),opt=UI.estTokens(optimized),saved=Math.max(0,ot-opt),pct=ot>0?Math.round(saved/ot*100):0; el.innerHTML += `<div class="psec" style="border-color:rgba(48,191,172,.2)"><div class="psec-hdr"><div style="display:flex;align-items:center;gap:7px"><span class="psec-badge pb-opt">OPTIMIZED</span><span style="font-size:11px;color:var(--teal2)">~${saved} tokens saved · ${pct}% smaller</span></div><button class="btn-copy" onclick="UI.copy(document.getElementById('psOpt').textContent,this)">Copy</button></div><div class="psec-body" id="psOpt" style="color:var(--teal2)">${UI.esc(optimized)}</div></div>`; }
  },

  _renderModelOutput() {
    const el = document.getElementById('modelOutput');
    if (!el || !this.data) return;
    el.textContent = this.data.model_variants?.[this.currentModel] || this.data.final_prompt || '';
  },

  _renderRefineQuick() {
    const el = document.getElementById('refineQuick');
    if (!el) return;
    const chips = ['Make constraints more specific','Add a few-shot example','Make 30% shorter','Remove filler phrases','Add token budget declaration','Make tone more direct'];
    el.innerHTML = chips.map(c => `<button class="btn-copy" onclick="document.getElementById('refineFeedback').value='${c}'">${c}</button>`).join('');
  },

  _renderExpls(expls) {
    const el = document.getElementById('genExpls');
    if (!el || !expls) return;
    el.innerHTML = (expls||[]).map(ex => `<div class="expl"><div class="expl-icon ei-${ex.color||'teal'}">${ex.icon||'✦'}</div><div><div class="expl-title">${UI.esc(ex.title||'')}</div><div class="expl-desc">${UI.esc(ex.desc||'')}</div></div></div>`).join('');
  },
};

/* ── IMAGE MODULE ── */
const IMG = {
  imageBase64: null, imageType: 'image/jpeg',
  selectedFw: 'react', selectedPt: 'build',

  init() {},

  onDrop(e) {
    e.preventDefault();
    document.getElementById('uploadZone').classList.remove('drag');
    const file = e.dataTransfer.files[0];
    if (file) this.loadFile(file);
  },
  onDragOver(e) { e.preventDefault(); document.getElementById('uploadZone').classList.add('drag'); },
  onDragLeave()  { document.getElementById('uploadZone').classList.remove('drag'); },
  onFileSelect(e) { const f = e.target.files[0]; if (f) this.loadFile(f); },

  loadFile(file) {
    if (file.size > 20 * 1024 * 1024) { UI.toast('Image too large — max 20MB', 'err'); return; }

    // Accept any image/* — AVIF, HEIC, WEBP, PNG, JPG all accepted
    // Canvas will re-encode everything as JPEG so Groq always gets a valid format
    if (!file.type.startsWith('image/')) {
      UI.toast('Please upload an image file', 'err');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      const img = new Image();
      img.onload = () => {
        // Resize: max 1024px on longest side — Groq rejects very large base64
        const MAX = 1024;
        let w = img.width, h = img.height;
        if (!w || !h) { UI.toast('Image dimensions unreadable', 'err'); return; }
        if (w > MAX || h > MAX) {
          if (w >= h) { h = Math.round(h * MAX / w); w = MAX; }
          else        { w = Math.round(w * MAX / h); h = MAX; }
        }

        // Draw onto canvas — this is the key step:
        // no matter what the original format (AVIF, HEIC, WEBP, PNG),
        // canvas.toDataURL always outputs a browser-native JPEG.
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext('2d');
        // White background before drawing (handles transparent PNGs)
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0, w, h);

        // Force JPEG output — this is what Groq actually accepts
        const jpeg = canvas.toDataURL('image/jpeg', 0.90);
        const b64  = jpeg.split(',')[1];

        // Sanity check: real JPEG starts with /9j/ in base64
        if (!b64 || b64.length < 500) {
          UI.toast('Canvas conversion failed — try a different image', 'err');
          return;
        }

        this.imageBase64 = b64;
        this.imageType   = 'image/jpeg'; // always jpeg after canvas conversion

        const preview = document.getElementById('imgPreview');
        if (preview) { preview.src = jpeg; preview.classList.remove('hidden'); }
        document.getElementById('uploadTitle').textContent = file.name + ' (' + w + '×' + h + ')';
        document.getElementById('uploadIcon').textContent  = '✓';
        document.getElementById('imgBtn').disabled = false;
        UI.toast('Image ready (' + w + '×' + h + ')');
      };
      img.onerror = () => {
        // If Image() can't decode it (e.g. HEIC on Windows), tell the user clearly
        UI.toast('Browser cannot decode this format. Convert to JPG/PNG first.', 'err');
      };
      img.src = dataUrl;
    };
    reader.onerror = () => UI.toast('File read failed', 'err');
    reader.readAsDataURL(file);
  },

  selectFw(btn) {
    document.querySelectorAll('#fwGrid .fw-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    this.selectedFw = btn.dataset.fw;
  },

  selectPt(btn) {
    document.querySelectorAll('#ptGrid .pt-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    this.selectedPt = btn.dataset.pt;
  },

  async analyze() {
    if (!this.imageBase64) { UI.toast('Please upload an image first', 'warn'); return; }

    document.getElementById('imgEmpty')?.classList.add('hidden');
    document.getElementById('imgResult')?.classList.add('hidden');
    const l = document.getElementById('imgLoading');
    if (l) { l.classList.remove('hidden'); l.classList.add('fade'); }

    const steps = ['il1','il2','il3','il4','il5'];
    const msgs  = ['Analyzing layout…','Extracting colors…','Detecting components…','Identifying interactions…','Generating prompt…'];
    const tid   = UI.animLoader(steps, msgs, 800);

    try {
      const result = await API.analyzeImage({
        image_base64: this.imageBase64,
        image_type:   this.imageType,
        framework:    this.selectedFw,
        prompt_type:  this.selectedPt,
      });

      UI.finishLoader(steps, tid);
      document.getElementById('imgLoading')?.classList.add('hidden');
      this._renderResult(result.data);
      const r = document.getElementById('imgResult');
      if (r) { r.classList.remove('hidden'); r.classList.add('fade'); }
      r?.scrollIntoView({ behavior:'smooth', block:'start' });

    } catch(err) {
      UI.finishLoader(steps, tid);
      document.getElementById('imgLoading')?.classList.add('hidden');
      if (err.message?.includes('401')) KEY.showModal();
      UI.toast(err.message || 'Analysis failed', 'err');
    }
  },

  _renderResult(d) {
    if (!d) return;
    this._lastPrompt = d.generated_prompt || '';

    // Complexity badge
    const cb = document.getElementById('imgComplexity');
    if (cb) cb.textContent = d.build_complexity || '';

    // Full analysis — all 4 accuracy dimensions
    const an = document.getElementById('imgAnalysis');
    if (an && d.analysis) {
      const a = d.analysis;
      let html = '';

      // Row 1: meta
      html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">
        <div class="achip"><div class="achip-l">Page Type</div><div class="achip-v av-gold">${UI.esc(a.page_type||'—')}</div></div>
        <div class="achip"><div class="achip-l">Navigation</div><div class="achip-v av-teal">${UI.esc(a.navigation_type||'—')}</div></div>
        <div class="achip"><div class="achip-l">Mode</div><div class="achip-v av-violet">${a.is_dark_mode?'🌙 Dark':'☀️ Light'}</div></div>
        <div class="achip"><div class="achip-l">Responsive</div><div class="achip-v av-teal">${a.is_responsive?'✓ Yes':'✗ No'}</div></div>
      </div>`;

      // DIMENSION 1: Colors — exact hex swatches
      if ((a.color_scheme||[]).length) {
        html += `<div style="margin-bottom:10px"><div class="achip-l" style="margin-bottom:6px">Colors extracted (${a.color_scheme.length})</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            ${a.color_scheme.map(c=>`
              <div style="display:flex;align-items:center;gap:6px;background:var(--s3);border:1px solid var(--border);border-radius:var(--r);padding:5px 9px">
                <div style="width:20px;height:20px;border-radius:4px;border:1px solid var(--border2);background:${UI.esc(c.hex_value)};flex-shrink:0"></div>
                <div>
                  <div style="font-family:var(--mono);font-size:11px;color:var(--t1);font-weight:500">${UI.esc(c.hex_value)}</div>
                  <div style="font-size:10px;color:var(--t3)">${UI.esc(c.role)}</div>
                </div>
              </div>`).join('')}
          </div>
        </div>`;
      }

      // DIMENSION 2: Components — every one detected
      if ((a.components_detected||[]).length) {
        html += `<div style="margin-bottom:10px"><div class="achip-l" style="margin-bottom:6px">Components detected (${a.components_detected.length})</div>
          <div style="display:flex;flex-direction:column;gap:5px">
            ${a.components_detected.map(c=>`
              <div style="background:var(--s3);border:1px solid var(--border);border-radius:var(--r);padding:7px 11px;display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
                <div>
                  <div style="font-size:12px;font-weight:500;color:var(--t1)">${UI.esc(c.name)}</div>
                  ${c.description?`<div style="font-size:11px;color:var(--t3);margin-top:2px">${UI.esc(c.description)}</div>`:''}
                </div>
                ${c.count>1?`<span style="font-family:var(--mono);font-size:10px;color:var(--teal2);background:var(--tglow);border:1px solid rgba(48,191,172,.2);padding:1px 7px;border-radius:20px;flex-shrink:0">×${c.count}</span>`:''}
              </div>`).join('')}
          </div>
        </div>`;
      }

      // DIMENSION 3 & 4: Interactions (hover + animations + scroll)
      if ((a.interactions_detected||[]).length) {
        const ints = a.interactions_detected;
        html += `<div style="margin-bottom:6px"><div class="achip-l" style="margin-bottom:6px">Interactions detected (${ints.length})</div>
          <div style="display:flex;flex-direction:column;gap:4px">
            ${ints.map(i=>`
              <div style="background:var(--s3);border:1px solid rgba(142,108,239,.15);border-radius:var(--r);padding:6px 11px;font-size:11px;color:var(--t2);display:flex;align-items:center;gap:7px">
                <span style="color:var(--violet2);font-size:13px">⟳</span>
                ${UI.esc(i)}
              </div>`).join('')}
          </div>
        </div>`;
      }

      // Content sections detected
      if ((a.content_sections||[]).length) {
        html += `<div class="achip full" style="margin-top:6px"><div class="achip-l">Sections (${a.content_sections.length})</div>
          <div class="tag-list" style="margin-top:4px">${a.content_sections.map(s=>`<span class="tag">${UI.esc(s)}</span>`).join('')}</div>
        </div>`;
      }

      an.innerHTML = html;
    }

    // Prompt output
    const out = document.getElementById('imgOutput');
    if (out) out.textContent = d.generated_prompt || '';

    // Key features
    const feats = document.getElementById('imgTips');
    if (feats) {
      let html = '';
      if ((d.key_features||[]).length) {
        html += `<div style="margin-bottom:10px"><div class="achip-l" style="margin-bottom:6px">Key Features</div>
          ${d.key_features.map(f=>`<div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:12px;color:var(--t2);display:flex;gap:8px">
            <span style="color:var(--green2)">✓</span>${UI.esc(f)}</div>`).join('')}
        </div>`;
      }
      if ((d.tips||[]).length) {
        html += `<div class="achip-l" style="margin-bottom:6px">Build Tips</div>
          ${d.tips.map(t=>`<div class="achip" style="margin-bottom:5px"><div class="achip-l" style="color:var(--teal2)">TIP</div><div style="font-size:12px;color:var(--t2)">${UI.esc(t)}</div></div>`).join('')}`;
      }
      feats.innerHTML = html || '<div style="font-size:12px;color:var(--t3)">No tips available</div>';
    }
  },

  copy()  { UI.copy(this._lastPrompt||'', document.getElementById('imgCopyBtn')); },
  download() { if (this._lastPrompt) UI.download(`promptcraft-${this.selectedFw}-${this.selectedPt}.txt`, this._lastPrompt); },
  _lastPrompt: '',
};