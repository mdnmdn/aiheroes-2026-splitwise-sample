/* App glue for htmx: user header, 422 swap, toasts, component init.
   The sign-in is a development simulation, not security (_docs/tech/guide-authentication.md). */
(function () {
  'use strict';
  const TOKEN_KEY = 'sw_user';       // signed token, sent as header X-Splitwise-User
  const USER_ID_KEY = 'sw_user_id';  // user id next to the token, read by the head script of base.html

  const store = {
    get: k => { try { return sessionStorage.getItem(k); } catch { return null; } },
    set: (k, v) => { try { sessionStorage.setItem(k, v); } catch { /* storage blocked */ } },
    del: k => { try { sessionStorage.removeItem(k); } catch { /* storage blocked */ } },
  };

  /* The event session-start calls SwSession.signIn(token, userId). Sign out calls SwSession.signOut(). */
  window.SwSession = {
    signIn(token, userId) { store.set(TOKEN_KEY, token); store.set(USER_ID_KEY, String(userId)); },
    signOut() { store.del(TOKEN_KEY); store.del(USER_ID_KEY); },
  };

  document.addEventListener('htmx:configRequest', e => {
    const token = store.get(TOKEN_KEY);
    if (token) e.detail.headers['X-Splitwise-User'] = token;
  });

  /* htmx 2 does not swap 4xx by default. The server sends form errors as 422 fragments. */
  document.addEventListener('htmx:beforeSwap', e => {
    if (e.detail.xhr.status === 422) {
      e.detail.shouldSwap = true; e.detail.isError = false;
    }
  });

  /* Events from the HX-Trigger header. They bubble to document, which a body swap keeps. */
  document.addEventListener('toast', e => {
    const message = e.detail && e.detail.message;
    if (message) Splitwise.toast(message);
  });
  /* The sign-in answer carries the token of the new user for this tab. */
  document.addEventListener('session-start', e => window.SwSession.signIn(e.detail.token, e.detail.user_id));

  /* Sign out: clear the storage of this tab. The form posts to /logout, which clears the cookie.
     Other tabs keep their user. They resume it on their next full load. */
  document.addEventListener('click', e => {
    if (e.target.closest('[data-sign-out]')) window.SwSession.signOut();
  });

  /* A form with data-new-user="VALUE" shows the name field for the option with that value. */
  function syncNewUser(form, focus) {
    const field = form.querySelector('[data-k="name"]');
    field.hidden = form.elements.user_id.value !== form.dataset.newUser;
    if (focus && !field.hidden) form.elements.name.focus();
  }
  document.addEventListener('change', e => {
    const form = e.target.form;
    if (form && form.hasAttribute('data-new-user') && e.target.name === 'user_id') syncNewUser(form, true);
  });

  /* After a 422 swap, focus the error summary or the first invalid field. The target can be
     the replaced element, so search the dialog or the page. */
  document.addEventListener('htmx:afterSwap', e => {
    if (e.detail.xhr.status !== 422) return;
    const scope = document.querySelector('#dialog-host dialog[open]') || document.getElementById('main');
    const el = scope.querySelector('.err-summary:not([hidden])') || scope.querySelector('[aria-invalid="true"]');
    if (el) el.focus();
  });

  /* A swap of the members panel removes the button that held the focus. Focus the heading. */
  document.addEventListener('htmx:afterSettle', e => {
    const from = e.detail.requestConfig && e.detail.requestConfig.elt;
    if (from && from.id === 'members-region' && document.activeElement === document.body) {
      document.getElementById('memTitle')?.focus();
    }
  });

  /* A swap of the body keeps the <body> attributes. Take data-user-id from the new page. */
  document.addEventListener('htmx:beforeSwap', e => {
    if (e.detail.target !== document.body) return;
    const found = /<body[^>]*\sdata-user-id="([^"]*)"/.exec(e.detail.serverResponse);
    if (found) document.body.dataset.userId = found[1];
  });

  /* Dialogs: the server puts one dialog in #dialog-host, onLoad opens it. */
  const host = () => document.getElementById('dialog-host');
  document.addEventListener('close-dialog', () => host().querySelector('dialog')?.close());
  document.addEventListener('close', e => {
    if (e.target.parentElement === host()) host().innerHTML = '';
  }, true);

  /* data-confirm-title, -body and -ok on a button: ask first, then send the request. */
  document.addEventListener('htmx:confirm', e => {
    const d = e.detail.elt.dataset;
    if (!d.confirmTitle) return;
    e.preventDefault();
    Splitwise.confirm({ title: d.confirmTitle, body: d.confirmBody, ok: d.confirmOk })
      .then(ok => { if (ok) e.detail.issueRequest(true); });
  });
  /* The confirm dialog of splitwise.js is a child of <body>. A body swap removes it. Put it back. */
  let confirmEl = null;
  document.addEventListener('htmx:beforeSwap', e => {
    if (e.detail.target === document.body) confirmEl = document.querySelector('dialog[aria-labelledby="sp-cf-title"]');
  });
  document.addEventListener('htmx:afterSwap', () => {
    if (confirmEl && !confirmEl.isConnected) document.body.append(confirmEl);
  });

  /* "Select all" / "Clear all" in the expense dialog. The change event starts the share preview;
     the server answers with the new link text. */
  document.addEventListener('click', e => {
    const toggle = e.target.closest('[data-toggle-all]');
    if (!toggle) return;
    const boxes = [...toggle.closest('fieldset').querySelectorAll('input[type="checkbox"]')];
    const all = boxes.every(b => b.checked);
    boxes.forEach(b => { b.checked = !all; });
    boxes[0]?.dispatchEvent(new Event('change', { bubbles: true }));
  });

  document.addEventListener('click', e => {
    const copy = e.target.closest('[data-copy]');
    if (copy) Splitwise.copy(copy.dataset.copy, copy.dataset.copied);
    if (e.target.closest('[data-clear-filters]')) {
      const form = document.getElementById('groupFilters');
      form.elements.q.value = '';
      form.querySelector('input[name="filter"][value="all"]').checked = true;
      htmx.trigger(form, 'submit');
      form.elements.q.focus();
    }
  });

  /* A failed request without its own message. A response with a toast event explains itself. */
  const failed = e => {
    const xhr = e.detail.xhr;
    if (xhr && xhr.getResponseHeader('HX-Trigger')) return;
    Splitwise.toast('Something went wrong. Try again.');
  };
  document.addEventListener('htmx:responseError', failed);
  document.addEventListener('htmx:sendError', failed);

  /* The elements in el that match, and el itself. */
  const within = (el, selector) => [...(el.matches(selector) ? [el] : []), ...el.querySelectorAll(selector)];

  /* Runs for the first load and for each swapped element. */
  htmx.onLoad(el => {
    Splitwise.hydrate(el);
    within(el, '[data-appearance]:empty').forEach(mount => Splitwise.appearance.mount(mount));
    within(el, '#flash').forEach(flash => {
      if (flash.dataset.message) Splitwise.toast(flash.dataset.message);
      flash.dataset.message = '';
    });
    within(el, '[data-new-user]').forEach(form => syncNewUser(form, false));
    within(el, '#loginForm').forEach(form => {
      if (!form.querySelector('[aria-invalid="true"]')) form.querySelector('select, input:not([hidden])').focus();
    });
    within(el, 'dialog:not([open])').filter(d => d.parentElement.id === 'dialog-host').forEach(d => {
      d.showModal();
      d.querySelector('[data-autofocus]')?.focus(); // the next Mark as paid, or Done
    });
  });
})();
