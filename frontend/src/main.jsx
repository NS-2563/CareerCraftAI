/* eslint react-refresh/only-export-components: "off" */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ResumeProvider } from "./context/ResumeContext";
import App from "./App";
import BackendStatus from "./components/BackendStatus";

import "./index.css";

// -------------------------
// React Query Client
// -------------------------
const queryClient = new QueryClient();


// -------------------------
// ROOT RENDER
// -------------------------
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ResumeProvider>
        <BrowserRouter>
          <App />
          <Toaster
    richColors
    position="top-right"
    closeButton
    duration={3000}
  />
          <BackendStatus />
        </BrowserRouter>
      </ResumeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);

