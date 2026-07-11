import { motion } from "framer-motion";
import { Lightbulb } from "lucide-react";

export default function AISuggestionCard({ suggestion, onClick, delay = 0 }) {
  return (
    <motion.button
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg border hover:border-primary/50 hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-start gap-3">
        <Lightbulb className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
        <div>
          <div className="font-medium text-sm">{suggestion.title}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {suggestion.description}
          </div>
        </div>
      </div>
    </motion.button>
  );
}