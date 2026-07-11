import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Home, LogIn, AlertTriangle } from "lucide-react";

export default function NotFound() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center">
            <AlertTriangle className="w-10 h-10 text-muted-foreground" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-bold mb-2">404</h1>
        <h2 className="text-xl text-muted-foreground mb-6">Page Not Found</h2>

        {/* Description */}
        <p className="text-muted-foreground mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Home className="w-4 h-4" />
            Return to Dashboard
          </Link>

          {!isAuthenticated && (
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-4 py-2 border rounded-md hover:bg-accent"
            >
              <LogIn className="w-4 h-4" />
              Return to Login
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}