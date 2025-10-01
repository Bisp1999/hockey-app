import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import './i18n';

// Suppress ResizeObserver errors (known benign React dev mode issue)
// This prevents the error from reaching React's error boundary
window.addEventListener('error', (e) => {
  if (e.message === 'ResizeObserver loop completed with undelivered notifications.' || 
      e.message === 'ResizeObserver loop limit exceeded') {
    e.stopImmediatePropagation();
    e.preventDefault();
  }
});

// Also suppress in console
const resizeObserverErr = window.console.error;
window.console.error = (...args: any[]) => {
  if (typeof args[0] === 'string' && args[0].includes('ResizeObserver loop')) {
    return;
  }
  resizeObserverErr(...args);
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);