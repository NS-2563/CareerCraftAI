import PersonalInfo from "../sections/PersonalInfo";
import Summary from "../sections/Summary";
import Experience from "../sections/Experience";
import Education from "../sections/Education";
import Skills from "../sections/Skills";
import Projects from "../sections/Projects";
import Certifications from "../sections/Certifications";
import Languages from "../sections/Languages";
import Interests from "../sections/Interests";
import References from "../sections/References";

/**
 * Resume sections registry (UI order + metadata only)
 * IMPORTANT:
 * - DO NOT add hooks here
 * - DO NOT import context or API
 * - Keep this file PURE
 */
const steps = [
  {
    id: "personal",
    title: "Personal Information",
    component: PersonalInfo,
  },
  {
    id: "summary",
    title: "Summary",
    component: Summary,
  },
  {
    id: "experience",
    title: "Experience",
    component: Experience,
  },
  {
    id: "education",
    title: "Education",
    component: Education,
  },
  {
    id: "skills",
    title: "Skills",
    component: Skills,
  },
  {
    id: "projects",
    title: "Projects",
    component: Projects,
  },
  {
    id: "certifications",
    title: "Certifications",
    component: Certifications,
  },
  {
    id: "languages",
    title: "Languages",
    component: Languages,
  },
  {
    id: "interests",
    title: "Interests",
    component: Interests,
  },
  {
    id: "references",
    title: "References",
    component: References,
  },
];

export default steps;

