/* ==========================================================================
   Splitwise app core — window.SplitwiseApp
   --------------------------------------------------------------------------
   Shared by every app page (login.html, index.html, group.html). Load after
   the UI kit:

     <link rel="stylesheet" href="assets/splitwise.css">
     <script src="assets/splitwise.js"></script>
     <script src="assets/splitwise-app.js"></script>

   What lives here (and nowhere else):
     data      SplitwiseApp.state / save()  — users, groups, transactions
     people    me(), user(id), nameOf(id), avatar(id, size), addUser(name)
     groups    group(id), myGroups(), makeCode(name)
     money     shares(t, members), balances(group), settlePlan(balances)
     rules     involves(t, id), hasHistory(group, id), nameError(name, exceptId)
     session   requireUser() (mockup: sample user, no redirect), signIn(id), signOut(), flash(msg)/takeFlash()
     chrome    renderTopbar(headerEl, { group, onGroupClick })

   Data model (key 'splitwise.v2' in localStorage, or the fallback storage below):
     users  [{ id, name }]
     groups [{ id, name, currency, code, members: [userId], tx: [...] }]
     tx     payment  { id, type:'payment', desc, amount, date, payer, participants[], created }
            internal { id, type:'internal', from, to, amount, date, note, created }
   Amounts are integer minor units (cents). Never floats.
   ========================================================================== */
(function () {
  'use strict';
  const { esc, icon } = Splitwise;
  const KEY = 'splitwise.v2', OLD_KEY = 'splitwise.v1', USER_KEY = 'splitwise.user', FLASH_KEY = 'splitwise.flash';
  const CURRENCIES = ['EUR','USD','GBP','CHF','JPY','CAD','AUD','SEK','NOK','DKK','PLN','CZK','INR','BRL','MXN'];
  const CODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // no 0/O/1/I/L — easy to read aloud

  /* ---------- storage that never throws ----------
     localStorage, else sessionStorage, else window.name. Sandboxed previews and
     some privacy modes block Web Storage and throw on any access; window.name
     survives page-to-page navigation in the same tab, so sign-in and data still
     carry across login.html → index.html → group.html. */
  const storage = Splitwise.storage; // one shared never-throwing store (see splitwise.js)

  /* ---------- money engine ---------- */
  /** Equal split: remainder cents go one each to participants in group join order. */
  function shares(t, members) {
    const ps = members.filter(id => t.participants.includes(id));
    const base = Math.floor(t.amount / ps.length), rem = t.amount % ps.length;
    return new Map(ps.map((id, i) => [id, base + (i < rem ? 1 : 0)]));
  }
  /** Map userId → balance. Positive = gets back, negative = owes. Always sums to zero. */
  function balances(g) {
    const b = new Map(g.members.map(id => [id, 0]));
    const add = (id, v) => b.set(id, (b.get(id) || 0) + v);
    for (const t of g.tx) {
      if (t.type === 'payment') { add(t.payer, t.amount); for (const [id, s] of shares(t, g.members)) add(id, -s); }
      else { add(t.from, t.amount); add(t.to, -t.amount); }
    }
    const sum = [...b.values()].reduce((a, v) => a + v, 0);
    if (sum !== 0) console.error('Splitwise invariant broken: balances sum to', sum);
    return b;
  }
  /** Greedy: largest debtor pays largest creditor; ≤ (non-zero members − 1) transfers. */
  function settlePlan(b) {
    const cred = [], debt = [], plan = [];
    for (const [id, v] of b) { if (v > 0) cred.push({ id, v }); else if (v < 0) debt.push({ id, v: -v }); }
    while (cred.length && debt.length) {
      cred.sort((x, y) => y.v - x.v); debt.sort((x, y) => y.v - x.v);
      const c = cred[0], d = debt[0], amount = Math.min(c.v, d.v);
      plan.push({ from: d.id, to: c.id, amount });
      c.v -= amount; d.v -= amount;
      if (!c.v) cred.shift();
      if (!d.v) debt.shift();
    }
    return plan;
  }

  /* ---------- data: seed, migration, load/save ---------- */
  function makeCode(name, groups = state.groups) {
    const pre = (name.replace(/[^a-z0-9]/gi, '').slice(0, 3) || 'GRP').toUpperCase().padEnd(3, 'X');
    let c;
    do { c = pre + '-' + Array.from({ length: 4 }, () => CODE_CHARS[Math.floor(Math.random() * CODE_CHARS.length)]).join(''); }
    while (groups.some(g => g.code === c));
    return c;
  }
  function seedFlat(ts) {
    return { id: 'g2', name: 'Flat 3B', currency: 'EUR', code: 'FLA-9HXM', members: ['m1', 'm4'], tx: [
      { id: 'e5', type: 'payment', desc: 'October rent', amount: 140000, date: '2026-10-01', payer: 'm1', participants: ['m1', 'm4'], created: ts + 5 },
      { id: 'p2', type: 'internal', from: 'm4', to: 'm1', amount: 70000, date: '2026-10-03', note: 'Rent share, bank transfer', created: ts + 6 },
      { id: 'e6', type: 'payment', desc: 'Electricity bill', amount: 8642, date: '2026-10-20', payer: 'm4', participants: ['m1', 'm4'], created: ts + 7 },
    ] };
  }
  function seed() {
    const ts = 1760000000000;
    return {
      users: [{ id: 'm1', name: 'Alice' }, { id: 'm2', name: 'Bob' }, { id: 'm3', name: 'Carla' }, { id: 'm4', name: 'Dario' }],
      groups: [
        { id: 'g1', name: 'Lisbon trip', currency: 'EUR', code: 'LIS-7K2Q', members: ['m1', 'm2', 'm3'], tx: [
          { id: 'e1', type: 'payment', desc: 'Apartment in Alfama, 3 nights', amount: 34200, date: '2026-10-14', payer: 'm1', participants: ['m1', 'm2', 'm3'], created: ts },
          { id: 'e2', type: 'payment', desc: 'Dinner at Time Out Market', amount: 8740, date: '2026-10-15', payer: 'm3', participants: ['m1', 'm2', 'm3'], created: ts + 1 },
          { id: 'e3', type: 'payment', desc: 'Train to Sintra', amount: 1350, date: '2026-10-16', payer: 'm2', participants: ['m2', 'm3'], created: ts + 2 },
          { id: 'e4', type: 'payment', desc: 'Pastéis de Belém', amount: 1000, date: '2026-10-16', payer: 'm2', participants: ['m1', 'm2', 'm3'], created: ts + 3 },
          { id: 'p1', type: 'internal', from: 'm2', to: 'm1', amount: 10000, date: '2026-10-17', note: 'Cash after dinner', created: ts + 4 },
        ] },
        seedFlat(ts),
      ],
    };
  }
  /** v1 (single group) → v2. Keeps ids, so a saved sign-in still works. */
  function migrate(old) {
    const st = {
      users: old.members.map(m => ({ id: m.id, name: m.name })),
      groups: [{ id: 'g1', name: old.group.name, currency: old.group.currency, code: makeCode(old.group.name, []), members: old.members.map(m => m.id),
        tx: [...old.expenses.map(e => ({ ...e, type: 'payment' })), ...old.payments.map(p => ({ ...p, type: 'internal', note: '' }))] }],
    };
    if (st.users.some(u => u.id === 'm1') && !st.users.some(u => u.id === 'm4' || u.name.toLowerCase() === 'dario')) {
      st.users.push({ id: 'm4', name: 'Dario' }); st.groups.push(seedFlat(1760000000000));
    }
    return st;
  }
  const read = k => { try { return JSON.parse(storage.getItem(k)); } catch { return null; } };
  function load() { const v2 = read(KEY); if (v2) return v2; const v1 = read(OLD_KEY); return v1 ? migrate(v1) : seed(); }
  let state = load();
  function save() {
    try { storage.setItem(KEY, JSON.stringify(state)); }
    catch { Splitwise.toast('Couldn’t save — browser storage is full or blocked.'); }
  }

  /* ---------- people & groups ---------- */
  const user = id => state.users.find(u => u.id === id);
  const nameOf = id => user(id)?.name ?? 'Unknown';
  const avatar = (id, size = '') => Splitwise.avatar(nameOf(id), state.users.findIndex(u => u.id === id), size);
  const group = id => state.groups.find(g => g.id === id);
  // Mockup: pages never require sign-in. Without a saved choice the sample user (Alice) is signed in.
  const DEMO_USER = 'm1';
  const me = () => { const id = storage.getItem(USER_KEY); return user(id) ? id : user(DEMO_USER) ? DEMO_USER : state.users[0]?.id ?? null; };
  const myGroups = () => state.groups.filter(g => g.members.includes(me()));
  function addUser(name) { const u = { id: Splitwise.uid(), name }; state.users.push(u); return u.id; }
  const involves = (t, id) => t.type === 'payment' ? t.payer === id || t.participants.includes(id) : t.from === id || t.to === id;
  const hasHistory = (g, id) => g.tx.some(t => involves(t, id));
  /** Validation message for a user name, or null. `exceptId` skips that user (renames). */
  function nameError(n, exceptId) {
    const taken = state.users.some(u => u.id !== exceptId && u.name.toLowerCase() === n.toLowerCase());
    return !n ? 'Enter a name.' : n.length > 30 ? 'Keep it under 30 characters.' : taken ? `${n} is already a user. Pick them from the list or use a different name.` : null;
  }

  /* ---------- session & navigation ---------- */
  const here = () => location.pathname.split('/').pop() + location.search;
  /** Returns the signed-in user id. Mockup: no redirect — falls back to the sample user (see me()). */
  function requireUser() { return me(); }
  function signIn(id) { storage.setItem(USER_KEY, id); }
  function signOut() { storage.removeItem(USER_KEY); location.href = 'login.html'; }
  /** Only same-folder page links are allowed as a post-login destination. */
  const safeNext = n => /^[\w-]+\.html(\?[\w=&%.-]*)?$/.test(n || '') ? n : 'index.html';
  /** A message carried across a redirect, shown as a toast on the next page. */
  function flash(msg) { storage.setItem(FLASH_KEY, msg); }
  function takeFlash() {
    const m = storage.getItem(FLASH_KEY); storage.removeItem(FLASH_KEY);
    if (m) Splitwise.toast(m);
  }

  /* ---------- shared top bar ----------
     <header class="topbar" id="topbar"></header> on every app page, then:
       SplitwiseApp.renderTopbar(document.getElementById('topbar'), { group, onGroupClick })
     Logo → index.html · breadcrumb Groups › group · user menu (Sign out) · appearance. */
  function renderTopbar(header, { group: g = null, onGroupClick = null } = {}) {
    const id = me();
    header.innerHTML = `
      <div class="topbar-in od-row">
        <a class="brand od-row od-fixed" href="index.html" aria-label="Splitwise — your groups">
          <span class="brand-mark">${icon('logo')}</span><span class="brand-name">Splitwise</span>
        </a>
        <span class="divider od-fixed" aria-hidden="true"></span>
        <nav class="breadcrumb od-fill" aria-label="Breadcrumb">
          <ol>
            <li class="od-fixed"><a href="index.html"${g ? '' : ' aria-current="page"'}>Groups</a></li>
            ${g ? `<li class="od-fill"><button type="button" data-group-settings aria-current="page" aria-label="${esc(g.name)}, group settings"><span class="od-truncate">${esc(g.name)}</span><span class="chip od-fixed">${g.currency}</span></button></li>` : ''}
          </ol>
        </nav>
        <details class="menu user-menu od-fixed">
          <summary class="user-btn" aria-label="Account: ${esc(nameOf(id))}">${avatar(id, 'sm')}<span class="user-name od-truncate">${esc(nameOf(id))}</span></summary>
          <div class="menu-pop">
            <div class="od-row">${avatar(id)}<div class="od-stat od-fill"><span class="row-title od-truncate">${esc(nameOf(id))}</span><span class="note">Signed in · ${myGroups().length} groups</span></div></div>
            <button type="button" class="btn secondary block" data-sign-out>${icon('logout')}Sign out</button>
          </div>
        </details>
        <div class="od-fixed" data-appearance></div>
      </div>`;
    header.querySelector('[data-sign-out]').onclick = signOut;
    const gb = header.querySelector('[data-group-settings]');
    if (gb && onGroupClick) gb.onclick = onGroupClick;
    Splitwise.appearance.mount(header.querySelector('[data-appearance]'));
  }

  window.SplitwiseApp = {
    CURRENCIES,
    get state() { return state; },
    save, reload() { state = load(); },
    user, nameOf, avatar, addUser, me, group, myGroups, makeCode,
    shares, balances, settlePlan, involves, hasHistory, nameError,
    requireUser, signIn, signOut, safeNext, flash, takeFlash,
    renderTopbar,
    _migrate: migrate, // exposed for the self-check
  };
})();
