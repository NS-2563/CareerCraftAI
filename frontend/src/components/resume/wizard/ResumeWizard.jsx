import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { useResumeContext } from "@/context/useResumeContext";
import steps from "./steps";
import StepIndicator from "./StepIndicator";
import NavigationButtons from "./NavigationButtons";

function validateStep(stepIndex, resumeData) {
  const step = steps[stepIndex];
  if (!step) return { valid: true, message: "" };

  const title = step.title.toLowerCase();

  // Personal Information - First Name, Last Name, Email required
  if (title === "personal information") {
    const { firstName, lastName, email } = resumeData.personal || {};
    if (!firstName?.trim() || !lastName?.trim() || !email?.trim()) {
      return {
        valid: false,
        message: "Please complete the required fields: First Name, Last Name, and Email.",
      };
    }
    return { valid: true, message: "" };
  }

  // Summary - Minimum 30 characters
  if (title === "summary") {
    const summary = resumeData.summary || "";
    if (summary.trim().length < 30) {
      return {
        valid: false,
        message: "Summary must be at least 30 characters.",
      };
    }
    return { valid: true, message: "" };
  }

  // Experience - At least one with Company and Position
  if (title === "experience") {
    const experience = resumeData.experience || [];
    const hasValid = experience.some(
      (exp) => exp?.company?.trim() && exp?.position?.trim()
    );
    if (!hasValid) {
      return {
        valid: false,
        message: "Please add at least one experience with Company and Position.",
      };
    }
    // Validate date ranges
for (const exp of experience) {
  if (exp?.current) continue;
  if (!exp?.startDate || !exp?.endDate) continue;

  if (exp.endDate < exp.startDate) {
    return {
      valid: false,
      message: "Experience end date cannot be earlier than the start date.",
    };
  }
}
    return { valid: true, message: "" };
  }

  // Education - At least one with Institution and Degree
  if (title === "education") {
    const education = resumeData.education || [];
    const hasValid = education.some(
      (edu) => edu?.institution?.trim() && edu?.degree?.trim()
    );
    if (!hasValid) {
      return {
        valid: false,
        message: "Please add at least one education with Institution and Degree.",
      };
    }
    // Validate date ranges
for (const edu of education) {
  if (edu?.current) continue;
  if (!edu?.startDate || !edu?.endDate) continue;

  if (edu.endDate < edu.startDate) {
    return {
      valid: false,
      message: "Education end date cannot be earlier than the start date.",
    };
  }
}
    return { valid: true, message: "" };
  }

  // Skills - At least one non-empty skill
  if (title === "skills") {
    const skills = resumeData.skills || [];
    const hasValid = skills.some((skill) => skill?.name?.trim());
    if (!hasValid) {
      return {
        valid: false,
        message: "Please add at least one skill.",
      };
    }
    return { valid: true, message: "" };
  }

  // Optional sections - always valid
  if (
    title === "projects" ||
    title === "certifications" ||
    title === "languages" ||
    title === "interests" ||
    title === "references"
  ) {
    return { valid: true, message: "" };
  }

  return { valid: true, message: "" };
}

export default function ResumeWizard({ initialSection }) {
  const [currentStep, setCurrentStep] = useState(() => {
    if (initialSection) {
      const idx = steps.findIndex((s) => s.id === initialSection);
      if (idx >= 0) return idx;
    }
    return 0;
  });
  const [validationError, setValidationError] = useState("");
  const { resumeData } = useResumeContext();
  const totalSteps = steps.length;

  function handlePrevious() {
    setCurrentStep((s) => Math.max(0, s - 1));
    setValidationError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleNext() {
    const validation = validateStep(currentStep, resumeData);
    if (!validation.valid) {
      setValidationError(validation.message);
      return;
    }
    setValidationError("");
    setCurrentStep((s) => Math.min(steps.length - 1, s + 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const CurrentComponent = steps[currentStep]?.component;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="w-full">
        <div className="flex justify-between text-sm text-muted-foreground mb-2">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Step Counter */}
      <div className="text-lg font-semibold text-foreground">
        Step {currentStep + 1} of {totalSteps}
      </div>

      <StepIndicator steps={steps} currentStep={currentStep} />

      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {CurrentComponent ? <CurrentComponent /> : null}
        </motion.div>
      </AnimatePresence>

      <NavigationButtons
        currentStep={currentStep}
        totalSteps={totalSteps}
        onPrevious={handlePrevious}
        onNext={handleNext}
        validationError={validationError}
      />
    </div>
  );
}

