import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function AILoading({ message = "Generating..." }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg"
    >
      <Loader2 className="w-5 h-5 animate-spin text-primary" />
      <span className="text-sm text-muted-foreground">{message}</span>
    </motion.div>
  );
}