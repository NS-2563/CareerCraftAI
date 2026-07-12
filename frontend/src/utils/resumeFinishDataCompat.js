// Small helper to build the exact backend payload for "Finish Resume".
// This intentionally reuses the same mapping as ResumeSaveButton.
//
// DO NOT duplicate business logic: this only appends `completed:true`.

import { mapResumePayloadForBackend } from "@/utils/resumeDataCompat";

export function mapResumePayloadForFinishBackend(resumeData) {
  const payload = mapResumePayloadForBackend(resumeData);
  return {
    ...payload,
    completed: true,
  };
}



