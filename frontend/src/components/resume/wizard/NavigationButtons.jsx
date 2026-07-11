import { Button } from "@/components/ui/button";

export default function NavigationButtons({
  currentStep,
  totalSteps,
  onPrevious,
  onNext,
  validationError,
}) {
  const isFirst = currentStep <= 0;
  const isLast = currentStep >= totalSteps - 1;

  return (
    <div className="space-y-3">
      {validationError && (
        <p className="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-md">
          {validationError}
        </p>
      )}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={onPrevious}
          disabled={isFirst}
          className="transition-all duration-200 hover:shadow-md focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          Previous
        </Button>

        {isLast ? (
          <Button
            onClick={onNext}
            className="transition-all duration-200 hover:shadow-md focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Finish Resume
          </Button>
        ) : (
          <Button
            onClick={onNext}
            className="transition-all duration-200 hover:shadow-md focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Next
          </Button>
        )}
      </div>
    </div>
  );
}