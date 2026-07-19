import {forwardRef } from "react";

const TEMPLATE_STYLES = {
  modern: {
    container: "font-sans",
    header: "text-2xl font-bold text-gray-900 mb-6",
    subtitle: "text-lg text-gray-600 mb-4",
    body: "text-base leading-relaxed text-gray-800 mb-4",
    signature: "mt-8",
  },
  professional: {
    container: "font-serif",
    header: "text-xl font-bold text-gray-900 uppercase tracking-wide mb-4",
    subtitle: "text-md text-gray-700 mb-3 italic",
    body: "text-sm leading-relaxed text-gray-700 mb-4",
    signature: "mt-8 italic",
  },
  executive: {
    container: "font-sans",
    header: "text-2xl font-serif font-bold text-gray-900 mb-5 border-b-2 border-gray-900 pb-2",
    subtitle: "text-lg text-gray-700 mb-4 font-medium",
    body: "text-base leading-relaxed text-gray-800 mb-4",
    signature: "mt-8 font-serif",
  },
  minimal: {
    container: "font-sans",
    header: "text-lg font-bold text-black mb-3",
    subtitle: "text-sm text-gray-600 mb-2",
    body: "text-sm leading-normal text-gray-900 mb-3",
    signature: "mt-6",
  },
};

function parseContentToSections(content) {
  if (!content) return null;

  const lines = content.split("\n").filter((line) => line.trim());
  const sections = {
    header: "",
    body: [],
    closing: "",
  };

  let inClosing = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Detect closing (usually last paragraph with "Sincerely" or similar)
    if (
      line.toLowerCase().includes("sincerely") ||
      line.toLowerCase().includes("best regards") ||
      line.toLowerCase().includes("respectfully") ||
      line.toLowerCase().includes("thank you")
    ) {
      inClosing = true;
    }

    if (i === 0 && line.includes(",")) {
      // Likely header line with date/address
      sections.header = line;
    } else if (inClosing) {
      sections.closing += line + "\n";
    } else {
      sections.body.push(line);
    }
  }

  return sections;
}

const CoverLetterPreview = forwardRef(function CoverLetterPreview(
  { template = "modern", content = "", personalInfo = {} },
  ref
) {
  const style = TEMPLATE_STYLES[template] || TEMPLATE_STYLES.modern;
  const sections = parseContentToSections(content);

  return (
    <div
      ref={ref}
      className={`${style.container} bg-white p-8 shadow-sm max-w-3xl mx-auto`}
    >
      {/* Header */}
      {sections?.header ? (
        <div className={style.subtitle}>{sections.header}</div>
      ) : (
        <div>
          {personalInfo?.name && (
            <div className={style.header}>{personalInfo.name}</div>
          )}
          {personalInfo?.email && (
            <div className={style.subtitle}>
              {personalInfo.email}
              {personalInfo.phone && ` | ${personalInfo.phone}`}
              {personalInfo.location && ` | ${personalInfo.location}`}
            </div>
          )}
        </div>
      )}

      {/* Date */}
      <div className="text-sm text-gray-600 mb-4">
        {new Date().toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        })}
      </div>

      {/* Body */}
      {sections?.body?.length > 0 ? (
        <div className={style.body}>
          {sections.body.map((line, index) => (
            <p key={index} className="mb-3">
              {line}
            </p>
          ))}
        </div>
      ) : content ? (
        <div className={style.body}>
          <pre className="whitespace-pre-wrap font-inherit">{content}</pre>
        </div>
      ) : (
        <div className="text-gray-400 italic">
          Your cover letter content will appear here...
        </div>
      )}

      {/* Closing */}
      {sections?.closing && (
        <div className={style.signature}>
          <pre className="whitespace-pre-wrap font-inherit">{sections.closing}</pre>
        </div>
      )}

      {/* Personal Info Signature */}
      {personalInfo?.name && !sections?.closing && (
        <div className={style.signature}>
          <p>Sincerely,</p>
          <p className="font-semibold">{personalInfo.name}</p>
          {personalInfo.title && <p className="text-gray-600">{personalInfo.title}</p>}
        </div>
      )}
    </div>
  );
});

export default CoverLetterPreview;

