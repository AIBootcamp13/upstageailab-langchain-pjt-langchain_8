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
