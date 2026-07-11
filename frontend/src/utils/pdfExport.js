// NOTE: PDF export pipeline (html2canvas/jsPDF + DOM cloning + oklch sanitization) has been removed.
// This file is kept only to avoid broken imports from older code paths.

export function generateFilename() {
  return "Resume.pdf";
}

export async function exportToPDF() {
  return {
    success: false,
    error: "exportToPDF removed. Use the browser print dialog (react-to-print).",
  };
}

export async function printResume() {
  return {
    success: false,
    error: "printResume removed. Use react-to-print.",
  };
}

