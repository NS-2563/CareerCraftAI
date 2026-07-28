import { Mail, Send, Heart, MessageSquare, UserPlus, Reply } from "lucide-react";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

const MESSAGE_TYPES = [
  {
    type: "cold_email",
    title: "Cold Email",
    description: "Reach out to a hiring manager or recruiter",
    icon: Mail,
  },
  {
    type: "follow_up",
    title: "Follow-Up",
    description: "Check in after submitting an application",
    icon: Send,
  },
  {
    type: "thank_you",
    title: "Thank-You Note",
    description: "Post-interview appreciation message",
    icon: Heart,
  },
  {
    type: "linkedin_note",
    title: "LinkedIn Note",
    description: "Short connection request message (~300 chars)",
    icon: MessageSquare,
  },
  {
    type: "referral_request",
    title: "Referral Request",
    description: "Ask a contact for an internal referral",
    icon: UserPlus,
  },
  {
    type: "recruiter_reply",
    title: "Reply to a Recruiter",
    description: "Respond to an inbound message from a recruiter",
    icon: Reply,
  },
];

export default function MessageTypeSelector({ onSelect, selectedType }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {MESSAGE_TYPES.map(({ type, title, description, icon: Icon }) => (
        <Card
          key={type}
          size="sm"
          className={`cursor-pointer transition-all hover:shadow-md ${
            selectedType === type
              ? "ring-2 ring-primary border-primary"
              : ""
          }`}
          onClick={() => onSelect(type)}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-sm">{title}</CardTitle>
                <CardDescription className="text-xs">
                  {description}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
