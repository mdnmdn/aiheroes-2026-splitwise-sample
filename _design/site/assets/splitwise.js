/* ==========================================================================
   Splitwise UI kit — shared script (window.Splitwise)
   --------------------------------------------------------------------------
   Load in <head> WITHOUT defer so the saved theme/accent is applied before
   first paint:   <script src="assets/splitwise.js"></script>

   API overview
     Splitwise.icon(name, label?)        → '<svg class="i">…'   (see ICONS)
     Splitwise.hydrate(root?)            → replaces <span data-icon="x"> with SVGs
     Splitwise.appearance.get()          → { theme, accent, resolved }
     Splitwise.appearance.set(patch)     → save + apply { theme?, accent? }
     Splitwise.appearance.mount(el, {inline?}) → renders the selector into el
     Splitwise.toast(message) / Splitwise.copy(text)
     Splitwise.confirm({ title, body, ok }) → Promise<boolean>
     Splitwise.forms.bind(form, validate, submit) / paint / reset / focusField
     Splitwise.money.{decimals, fmt, fmtSigned, symbol, parse, toInput}
     Splitwise.balance.{html, label, cls}
     Splitwise.avatar(name, index?, size?)
     Splitwise.{esc, uid, todayISO, fmtDate, $}

   Events
     document 'splitwise:appearance' → detail { theme, accent, resolved }
   ========================================================================== */
(function () {
  'use strict';
  const root = document.documentElement;
  const LOCALE = navigator.language || 'en'; // ponytail: Intl is the locale layer; UI strings are English-only

  /* ---------- small utilities ---------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  /** Escape text for safe insertion into HTML strings. */
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  /** Short random id — fine for local data, not for security. */
  const uid = () => Math.random().toString(36).slice(2, 10);
  /** Today as YYYY-MM-DD in local time (matches <input type="date">). */
  const todayISO = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
  /** 'YYYY-MM-DD' → "16 Oct 2026" in the browser locale. */
  const fmtDate = iso => { const [y, m, d] = iso.split('-').map(Number); return new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(y, m - 1, d)); };
  // One-time migration from the product's earlier name: copy 'splitly.*' keys to 'splitwise.*'.
  try {
    for (const k of Object.keys(localStorage)) {
      const nk = k.replace(/^splitly\./, 'splitwise.');
      if (nk !== k && localStorage.getItem(nk) === null) localStorage.setItem(nk, localStorage.getItem(k));
    }
  } catch { /* storage blocked */ }
  /**
   * Storage that never throws, shared by the kit and the app (Splitwise.storage).
   * localStorage, else sessionStorage, else window.name. Sandboxed previews and
   * some privacy modes block Web Storage; without a fallback the saved theme /
   * accent was dropped and re-read as the default, so the picker seemed dead.
   * window.name survives page-to-page navigation in the same tab.
   */
  const storage = (() => {
    for (const s of ['localStorage', 'sessionStorage']) {
      try { const st = window[s]; st.setItem('__sw_test', '1'); st.removeItem('__sw_test'); return st; } catch { /* blocked */ }
    }
    // ponytail: per-tab fallback; fine for a prototype, not real persistence
    let data = {};
    try { const v = JSON.parse(window.name || '{}'); if (v && typeof v === 'object') data = v; } catch { /* not ours */ }
    const sync = () => { window.name = JSON.stringify(data); };
    return {
      getItem: k => (k in data ? data[k] : null),
      setItem: (k, v) => { data[k] = String(v); sync(); },
      removeItem: k => { delete data[k]; sync(); },
    };
  })();
  const store = { get: k => storage.getItem(k), set: (k, v) => storage.setItem(k, v) };

  /* ---------- icons: one stroke family, 24px grid ---------- */
  const ICONS = {
    logo: '<path d="M12 3v18M5 8l7-5 7 5M5 16l7 5 7-5"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    receipt: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"/>',
    pay: '<path d="M4 8h14l-4-4M20 16H6l4 4"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    palette: '<path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.6-.8 1.6-1.6 0-.9-.6-1.3-.6-2.1 0-.9.7-1.6 1.6-1.6H17a4 4 0 0 0 4-4C21 6.6 17 3 12 3z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="14.5" cy="7" r="1"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0 1 14 0M16 4.5a3.5 3.5 0 0 1 0 7M18 13.5a7 7 0 0 1 4 6.5"/>',
    logout: '<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16zM13 7l4 4"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V4H4v12h4"/>',
  };
  /** SVG markup for an icon. Pass `label` only when the icon stands alone and means something. */
  function icon(name, label) {
    const a11y = label ? `role="img" aria-label="${esc(label)}"` : 'aria-hidden="true"';
    return `<svg class="i" viewBox="0 0 24 24" ${a11y}>${ICONS[name] || ''}</svg>`;
  }
  /** Replace every <span data-icon="name"> placeholder inside `scope` with its SVG. */
  function hydrate(scope = document) {
    scope.querySelectorAll('[data-icon]').forEach(el => { el.outerHTML = icon(el.dataset.icon, el.dataset.label); });
  }

  /* ---------- appearance: theme + accent ---------- */
  const KEYS = { theme: 'splitwise.theme', accent: 'splitwise.accent' };
  const THEMES = [['light', 'Light'], ['dark', 'Dark'], ['system', 'System']];
  /** swatch = the light-theme accent value, used only to paint the picker dot. */
  const ACCENTS = [
    { id: 'pop', label: 'Purple & orange', swatch: '#7c3aed' },
    { id: 'teal', label: 'Teal', swatch: '#0f766e' },
    { id: 'blue', label: 'Blue', swatch: '#1d4ed8' },
    { id: 'green', label: 'Green', swatch: '#15803d' },
    { id: 'violet', label: 'Violet', swatch: '#6d28d9' },
    { id: 'orange', label: 'Orange', swatch: '#c2410c' },
    { id: 'rose', label: 'Rose', swatch: '#be123c' },
  ];
  const mq = matchMedia('(prefers-color-scheme: dark)');
  function getAppearance() {
    const theme = store.get(KEYS.theme) || 'system';
    const accent = ACCENTS.some(a => a.id === store.get(KEYS.accent)) ? store.get(KEYS.accent) : 'pop';
    return { theme, accent, resolved: theme === 'system' ? (mq.matches ? 'dark' : 'light') : theme };
  }
  function applyAppearance() {
    const a = getAppearance();
    root.dataset.theme = a.resolved;
    root.dataset.accent = a.accent;
    document.dispatchEvent(new CustomEvent('splitwise:appearance', { detail: a }));
  }
  /** Save and apply. Example: Splitwise.appearance.set({ accent: 'blue' }) */
  function setAppearance(patch) {
    if (patch.theme) store.set(KEYS.theme, patch.theme);
    if (patch.accent) store.set(KEYS.accent, patch.accent);
    applyAppearance();
  }
  /**
   * Render the appearance selector into `el`.
   * Default: an icon button opening a popover menu (top bars).
   * { inline: true }: the controls laid out in place (settings pages, docs).
   */
  function mountAppearance(el, { inline = false } = {}) {
    const id = 'ap-' + uid();
    const controls = `
      <fieldset class="menu-group"><legend>Theme</legend>
        <div class="segmented">${THEMES.map(([v, l]) => `<label><input type="radio" name="${id}-theme" value="${v}"><span>${l}</span></label>`).join('')}</div>
      </fieldset>
      <fieldset class="menu-group"><legend>Accent</legend>
        <div class="swatches">${ACCENTS.map(a => `<label class="swatch" style="--sw:${a.swatch}"><input type="radio" name="${id}-accent" value="${a.id}"><span class="sr-only">${a.label}</span></label>`).join('')}</div>
      </fieldset>`;
    el.innerHTML = inline
      ? `<div class="appearance-inline">${controls}</div>`
      : `<div class="appearance-bar">
          <button type="button" class="icon-btn" data-quick-theme></button>
          <details class="menu"><summary class="btn ghost sm appearance-btn" aria-label="Appearance: theme and accent">${icon('palette')}<span class="appearance-label">Theme</span></summary><div class="menu-pop" role="group" aria-label="Appearance">${controls}</div></details>
        </div>`;
    // Quick toggle: one click flips the resolved theme between light and dark.
    const quick = el.querySelector('[data-quick-theme]');
    if (quick) quick.onclick = () => setAppearance({ theme: getAppearance().resolved === 'dark' ? 'light' : 'dark' });
    const sync = () => {
      const a = getAppearance();
      el.querySelectorAll('input').forEach(i => { i.checked = i.value === (i.name.endsWith('-theme') ? a.theme : a.accent); });
      if (quick) {
        const dark = a.resolved === 'dark';
        quick.innerHTML = icon(dark ? 'sun' : 'moon');
        quick.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
      }
    };
    el.addEventListener('change', e => {
      const i = e.target;
      setAppearance(i.name.endsWith('-theme') ? { theme: i.value } : { accent: i.value });
    });
    document.addEventListener('splitwise:appearance', sync);
    sync();
    return el;
  }
  mq.addEventListener('change', applyAppearance);
  window.addEventListener('storage', e => { if (e.key === KEYS.theme || e.key === KEYS.accent) applyAppearance(); }); // keep open tabs in sync
  applyAppearance();

  /* Menus: close on outside click and on Esc (focus returns to the trigger). */
  document.addEventListener('click', e => {
    document.querySelectorAll('details.menu[open]').forEach(d => { if (!d.contains(e.target)) d.open = false; });
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const d = e.target.closest?.('details.menu[open]');
    if (d) { d.open = false; d.querySelector('summary').focus(); }
  });

  /* ---------- toast ---------- */
  let toastEl, toastTimer;
  /** Short confirmation message at the bottom of the screen (role=status). */
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); toastEl.setAttribute('aria-live', 'polite');
      document.body.append(toastEl);
    }
    requestAnimationFrame(() => { toastEl.textContent = msg; toastEl.classList.add('show'); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 2800);
  }

  /** Copy text to the clipboard and confirm with a toast (falls back to a hint if blocked). */
  async function copy(text, done = 'Copied to clipboard') {
    try { await navigator.clipboard.writeText(text); toast(done); }
    catch { toast('Copy is blocked here — select the text and copy it manually'); }
  }

  /* ---------- confirm dialog ---------- */
  let confirmEl;
  /**
   * Ask before a destructive action. Resolves true on confirm, false on cancel/Esc.
   * Focus starts on Cancel so Enter never destroys by accident.
   */
  function confirm({ title, body = '', ok = 'Confirm' }) {
    if (!confirmEl) {
      confirmEl = document.createElement('dialog');
      confirmEl.dataset.strict = '';
      confirmEl.setAttribute('aria-labelledby', 'sp-cf-title');
      confirmEl.setAttribute('aria-describedby', 'sp-cf-body');
      confirmEl.innerHTML = `<div class="dlg">
        <header class="dlg-head od-row"><h2 id="sp-cf-title"></h2><span class="od-spacer" style="width:44px;height:44px"></span></header>
        <div class="dlg-body"><p id="sp-cf-body" class="muted"></p></div>
        <footer class="dlg-foot od-row"><button type="button" class="btn secondary" data-cf="0">Cancel</button><button type="button" class="btn primary" data-cf="1"></button></footer></div>`;
      document.body.append(confirmEl);
    }
    $('#sp-cf-title', confirmEl).textContent = title;
    $('#sp-cf-body', confirmEl).textContent = body;
    $('[data-cf="1"]', confirmEl).textContent = ok;
    return new Promise(res => {
      const done = v => { confirmEl.close(); res(v); };
      confirmEl.querySelectorAll('[data-cf]').forEach(b => { b.onclick = () => done(b.dataset.cf === '1'); });
      confirmEl.oncancel = e => { e.preventDefault(); done(false); };
      confirmEl.showModal(); $('[data-cf="0"]', confirmEl).focus();
    });
  }

  /* ---------- dialogs: [data-close] and backdrop click ---------- */
  document.addEventListener('click', e => {
    const c = e.target.closest('[data-close]');
    if (c) return c.closest('dialog')?.close();
    if (e.target.tagName === 'DIALOG' && !('strict' in e.target.dataset)) e.target.close();
  });

  /* ---------- forms: validate on blur, everything on submit ---------- */
  /**
   * Wire a form to a validator.
   *   validate() → { key: 'message' }  (keys match .field[data-k])
   *   submit()   → called only when validate() returns {}
   * Errors show per field after blur, all of them after the first submit;
   * 2+ errors also fill the form's .err-summary (optional element).
   */
  function bind(form, validate, submit) {
    form._touched = new Set();
    const live = () => { if (form._touched.size || form._submitted) paint(form, validate()); };
    form.addEventListener('focusout', e => {
      const w = e.target.closest('[data-k]');
      if (!w || w.contains(e.relatedTarget)) return;
      form._touched.add(w.dataset.k); paint(form, validate());
    });
    form.addEventListener('input', live);
    form.addEventListener('change', live);
    form.addEventListener('submit', e => {
      e.preventDefault(); form._submitted = true;
      const errs = validate();
      if (Object.keys(errs).length) return paint(form, errs, true);
      submit();
    });
  }
  /** Render errors into the form. `focus` moves focus to the summary or the only bad field. */
  function paint(form, errs, focus) {
    form.querySelectorAll('[data-k]').forEach(w => {
      const k = w.dataset.k, msg = (form._submitted || form._touched.has(k)) && errs[k];
      const errEl = w.querySelector('.err'); if (errEl) errEl.textContent = msg || '';
      w.querySelectorAll('input:not([type=checkbox]):not([type=radio]),select,textarea').forEach(c => c.setAttribute('aria-invalid', msg ? 'true' : 'false'));
    });
    const sum = form.querySelector('.err-summary'), keys = Object.keys(errs);
    if (sum && (!keys.length || !form._submitted)) sum.hidden = true;
    if (!focus) return;
    if (sum && keys.length > 1) {
      sum.innerHTML = `<strong>Fix ${keys.length} fields to continue:</strong><ul>${keys.map(k => `<li><a href="#" data-goto="${k}">${esc(errs[k])}</a></li>`).join('')}</ul>`;
      sum.hidden = false; sum.focus();
    } else focusField(form, keys[0]);
  }
  function focusField(form, k) { form.querySelector(`[data-k="${k}"] :is(input,select,textarea)`)?.focus(); }
  /** Clear touched/submitted state and all messages (call when (re)opening a form). */
  function reset(form) { form._touched?.clear(); form._submitted = false; paint(form, {}); }
  document.addEventListener('click', e => {
    const g = e.target.closest('[data-goto]');
    if (g) { e.preventDefault(); focusField(g.closest('form'), g.dataset.goto); }
  });

  /* ---------- money: integer minor units only ---------- */
  const MAX_MAJOR = 100000000;
  const money = {
    /** Decimal places for an ISO 4217 code (EUR 2, JPY 0). */
    decimals: cur => new Intl.NumberFormat('en', { style: 'currency', currency: cur }).resolvedOptions().maximumFractionDigits,
    /** 9540, 'EUR' → "€95.40" */
    fmt(minor, cur) {
      const d = money.decimals(cur);
      return new Intl.NumberFormat(LOCALE, { style: 'currency', currency: cur, minimumFractionDigits: d, maximumFractionDigits: d }).format(minor / 10 ** d);
    },
    /** Signed with a real minus: "+€1.00", "−€1.00", "€0.00". */
    fmtSigned: (v, cur) => v > 0 ? '+' + money.fmt(v, cur) : v < 0 ? '−' + money.fmt(-v, cur) : money.fmt(0, cur),
    symbol: cur => new Intl.NumberFormat(LOCALE, { style: 'currency', currency: cur }).formatToParts(0).find(p => p.type === 'currency').value,
    /** User text → minor units (number), or an error message (string). Accepts "12,5". */
    parse(str, d) {
      const s = String(str).trim().replace(/\s/g, '').replace(',', '.');
      if (!s) return 'Enter an amount.';
      if (!/^\d+(\.\d*)?$/.test(s)) return 'Use digits only, e.g. 12.50.';
      const [int, frac = ''] = s.split('.');
      if (frac.length > d) return d ? `Use at most ${d} decimals.` : 'This currency has no decimals.';
      if (Number(int) >= MAX_MAJOR) return 'Amount is too large.';
      const minor = Number(int) * 10 ** d + Number((frac + '0'.repeat(d)).slice(0, d) || 0);
      return minor > 0 ? minor : 'Amount must be more than zero.';
    },
    /** Minor units → input text without float maths: 1250, 2 → "12.50". */
    toInput(minor, d) {
      if (!d) return String(minor);
      const s = String(minor).padStart(d + 1, '0');
      return s.slice(0, -d) + '.' + s.slice(-d);
    },
  };

  /* ---------- balance amount ---------- */
  const balance = {
    label: v => v > 0 ? 'gets back' : v < 0 ? 'owes' : 'settled up',
    cls: v => v > 0 ? 'pos' : v < 0 ? 'neg' : 'muted',
    /** The .amt stack: signed amount over its label. Colour is never the only cue. */
    html: (v, cur) => `<span class="amt od-stat od-fixed"><span class="num od-nowrap ${balance.cls(v)}">${money.fmtSigned(v, cur)}</span><span class="amt-label">${balance.label(v)}</span></span>`,
  };

  /** Avatar markup. `index` spreads hues (join order); size: '' | 'sm' | 'lg'. */
  const avatar = (name, index = 0, size = '') =>
    `<span class="avatar ${size}" style="--h:${(index * 67 + 170) % 360}" aria-hidden="true">${esc((name || '?')[0].toUpperCase())}</span>`;

  document.addEventListener('DOMContentLoaded', () => hydrate());

  window.Splitwise = {
    version: '1.0.0',
    $, esc, uid, todayISO, fmtDate,
    icon, icons: Object.keys(ICONS), hydrate,
    appearance: { get: getAppearance, set: setAppearance, mount: mountAppearance, THEMES, ACCENTS },
    toast, confirm, copy, storage,
    forms: { bind, paint, reset, focusField },
    money, balance, avatar,
  };
})();
