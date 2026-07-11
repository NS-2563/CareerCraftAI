import { useEffect, useState } from "react";

import { checkHealth } from "../services/healthService";

export default function BackendStatus() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    checkHealth().then((result) => {
      setStatus(result.online ? "online" : "offline");
    });
  }, []);

  if (status === "checking") return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "16px",
        right: "16px",
        padding: "8px 12px",
        borderRadius: "8px",
        fontSize: "12px",
        fontWeight: "500",
        zIndex: 9999,
        backgroundColor: status === "online" ? "#22c55e" : "#ef4444",
        color: "white",
      }}
    >
      Backend: {status === "online" ? "Connected" : "Offline"}
    </div>
  );
}
