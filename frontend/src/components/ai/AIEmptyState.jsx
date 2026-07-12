import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export default function AIEmptyState({ title = "No suggestions yet" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center gap-3 p-6 text-center"
    >
      <Sparkles className="w-8 h-8 text-muted-foreground/50" />
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="text-xs text-muted-foreground/70">
        Fill in your resume details to get AI-powered suggestions.
      </p>
    </motion.div>
  );
}

