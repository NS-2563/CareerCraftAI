import { InterviewProvider } from "@/modules/interview/context/InterviewContext";
import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";
import SetupWizard from "@/modules/interview/pages/SetupWizard";
import InterviewPracticePage from "@/modules/interview/pages/Practice";
import InterviewResultsPage from "@/modules/interview/pages/Results";
import { SESSION_STATUS } from "@/modules/interview/services/constants/interviewConstants";

function InterviewInner() {
  const { sessionStatus } = useInterviewContext();

  if (sessionStatus === SESSION_STATUS.NOT_STARTED) {
    return <SetupWizard />;
  }

  if (sessionStatus === SESSION_STATUS.IN_PROGRESS) {
    return <InterviewPracticePage />;
  }

  if (sessionStatus === SESSION_STATUS.FINISHED) {
    return <InterviewResultsPage />;
  }

  // Fallback for other statuses (paused, etc.)
  return <InterviewPracticePage />;
}

export default function Interview() {
  return (
    <InterviewProvider>
      <InterviewInner />
    </InterviewProvider>
  );
}

