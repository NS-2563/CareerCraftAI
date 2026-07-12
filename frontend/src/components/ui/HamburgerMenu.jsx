import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { History, BarChart3, RefreshCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import "./HamburgerMenu.css";

export default function HamburgerMenu({
  onNewAssessment,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const navigate = useNavigate();

  const handleHistory = () => {
    setIsOpen(false);
    navigate("/career/history");
  };

  const handleAnalytics = () => {
  setIsOpen(false);
  navigate("/career/analytics");
};

  const handleNewAssessment = () => {
    setIsOpen(false);

    if (onNewAssessment) {
      onNewAssessment();
    }
  };

  return (
    <div className="relative">

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`hamburger-menu ${isOpen ? "open" : ""}`}
      >
        <span className="hamburger-line"></span>
        <span className="hamburger-line"></span>
      </button>

      <AnimatePresence>
  {isOpen && (
    <motion.div
    className="origin-top-right"
      initial={{
        opacity: 0,
        scale: 0.95,
        y: -10,
      }}
      animate={{
        opacity: 1,
        scale: 1,
        y: 0,
      }}
      exit={{
        opacity: 0,
        scale: 0.95,
        y: -10,
      }}
      transition={{
        duration: 0.18,
      }}
    >
        <div className="absolute right-0 mt-3 w-64 rounded-xl border bg-white shadow-xl overflow-hidden z-50">
<button
  onClick={handleHistory}
  className="flex items-center gap-3 w-full px-4 py-3 hover:bg-muted transition-all duration-300 hover:-translate-y-0.5"
>
  <History size={18} />
  <span>Career History</span>
</button>

<button
  onClick={handleAnalytics}
  className="flex items-center gap-3 w-full px-4 py-3 hover:bg-muted transition-all duration-300 hover:-translate-y-0.5"
>
  <BarChart3 size={18} />
  <span>Progress Analytics</span>
</button>

<button
  onClick={handleNewAssessment}
  className="flex items-center gap-3 w-full px-4 py-3 hover:bg-muted transition-all duration-300 hover:-translate-y-0.5"
>
  <RefreshCcw size={18} />
  <span>New Assessment</span>
</button>
</div>
    </motion.div>
  )}
</AnimatePresence>
    </div>
  );
}

