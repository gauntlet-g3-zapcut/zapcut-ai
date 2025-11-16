import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./globals.css";
import { initWebShim } from "./lib/webShim";

// CRITICAL: Initialize web shim IMMEDIATELY before anything else
// This ensures the Electron API shim is available before React renders
if (typeof window !== 'undefined') {
  // The shim should already be initialized from module load, but ensure it's there
  initWebShim();
  
  // Verify initialization
  const apiExists = typeof (window as any).electronAPI !== 'undefined';
  const hasOpenFileDialog = typeof (window as any).electronAPI?.openFileDialog === 'function';
  
  if (!apiExists || !hasOpenFileDialog) {
    console.warn('Web shim not properly initialized, retrying...');
    initWebShim();
  }
  
  // Log for debugging
  console.log('Web shim status after main.tsx init:', {
    electronAPI: typeof (window as any).electronAPI !== 'undefined',
    openFileDialog: typeof (window as any).electronAPI?.openFileDialog === 'function',
    isElectron: navigator.userAgent.includes('Electron'),
    shimInitialized: typeof (window as any).__WEB_SHIM_INITIALIZED !== 'undefined',
  });
  
  // Make API available globally for debugging
  if (typeof (window as any).electronAPI !== 'undefined') {
    (window as any).__DEBUG_ELECTRON_API = (window as any).electronAPI;
  }
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
