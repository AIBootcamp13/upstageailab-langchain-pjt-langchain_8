// public/custom.js
// Small script to capture client-side rendering errors and send them to the server
(function () {
  // Avoid double-installing
  if (window.__chainlit_custom_js_installed) return;
  window.__chainlit_custom_js_installed = true;

  function sendError(payload) {
    try {
      fetch('/_client_error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(function (e) {
        console.warn('Failed to report client error to server', e);
      });
    } catch (e) {
      console.warn('Reporting error failed', e);
    }
  }

  // Global uncaught errors
  window.addEventListener('error', function (event) {
    sendError({
      type: 'error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: (event.error && event.error.stack) ? String(event.error.stack) : undefined,
      userAgent: navigator.userAgent,
      time: new Date().toISOString()
    });
  });

  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', function (event) {
    sendError({
      type: 'unhandledrejection',
      reason: (event.reason && event.reason.stack) ? String(event.reason.stack) : (event.reason || ''),
      userAgent: navigator.userAgent,
      time: new Date().toISOString()
    });
  });

  // Optional: capture console.error calls
  const origConsoleError = console.error;
  console.error = function () {
    try {
      const args = Array.prototype.slice.call(arguments);
      sendError({
        type: 'console.error',
        args: args.map(a => (typeof a === 'string' ? a : (a && a.stack) ? String(a.stack) : JSON.stringify(a))),
        userAgent: navigator.userAgent,
        time: new Date().toISOString()
      });
    } catch (e) {
      // ignore
    }
    origConsoleError.apply(console, arguments);
  };
})();

// Add a small pencil button to assistant/draft messages to open the inline editor.
(function () {
  // Avoid double-installing
  if (window.__chainlit_inline_edit_button_installed) return;
  window.__chainlit_inline_edit_button_installed = true;

  // Helper to create the pencil button
  function makeButton(messageId) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.title = 'Edit draft';
    btn.innerText = '✏️';
    btn.style.marginLeft = '8px';
    btn.style.border = 'none';
    btn.style.background = 'transparent';
    btn.style.cursor = 'pointer';
    btn.style.fontSize = '14px';
    btn.dataset.inlineEditTarget = messageId;
    btn.addEventListener('click', async function (e) {
      e.preventDefault();
      const id = this.dataset.inlineEditTarget;
      try {
        // POST to Chainlit's action endpoint to trigger the server-side callback.
        await fetch('/_action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'open_inline_editor', payload: { message_id: id } }),
        });
      } catch (err) {
        console.warn('Failed to call open_inline_editor action', err);
      }
    });
    return btn;
  }

  // Find message nodes and attach buttons. We look for elements that contain the author text
  // '🤖 BlogGenerator' or '📝 Draft' and that have a data-message-id attribute (Chainlit client markup may vary).
  function scanAndAttach(root) {
    const authors = ['🤖 BlogGenerator', '📝 Draft'];
    // Look for any element that contains the author text
    const nodes = Array.from((root || document).querySelectorAll('*'));
    for (const node of nodes) {
      try {
        if (!node.textContent) continue;
        for (const author of authors) {
          if (node.textContent.includes(author)) {
            // Try to find a nearby message container with a data-message-id attribute
            const msg = node.closest('[data-message-id]') || node.parentElement && node.parentElement.closest('[data-message-id]');
            if (msg && !msg.querySelector('button[data-inline-edit-target]')) {
              const mid = msg.getAttribute('data-message-id') || msg.dataset?.messageId;
              if (mid) {
                const btn = makeButton(mid);
                // Insert at the end of the author node if possible
                node.appendChild(btn);
              }
            }
          }
        }
      } catch (e) {
        // ignore DOM errors
      }
    }
  }

  // Run initial scan after a short delay to let the client render
  setTimeout(() => scanAndAttach(document), 1200);

  // Observe DOM changes to attach buttons to new messages
  const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.addedNodes && m.addedNodes.length) {
        for (const n of m.addedNodes) {
          if (n.nodeType === 1) scanAndAttach(n);
        }
      }
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });
})();
