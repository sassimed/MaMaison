import React from "react";
import ReactDOM from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import "@/index.css";
import "@/smarthome-theme.css";
import App from "@/App";

const rootElement = document.getElementById("root");

// Check if the app is being hydrated (prerendered by react-snap)
if (rootElement.hasChildNodes()) {
  // Hydrate the pre-rendered HTML
  ReactDOM.hydrateRoot(
    rootElement,
    <React.StrictMode>
      <HelmetProvider>
        <App />
      </HelmetProvider>
    </React.StrictMode>
  );
} else {
  // Normal client-side render
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <HelmetProvider>
        <App />
      </HelmetProvider>
    </React.StrictMode>
  );
}
