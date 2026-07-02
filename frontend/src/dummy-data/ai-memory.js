// AI Memory store — long-term knowledge the assistant has accumulated.
export const AI_MEMORY = [
  { id: "mem1", label: "Brand voice", value: "Warm, concise, decisive. Avoid emoji in B2B contexts. Prefer first-name address." },
  { id: "mem2", label: "Pricing rules", value: "Never quote below ₹2L ARR without manager approval. Always default to Growth tier." },
  { id: "mem3", label: "Working hours", value: "Mon–Fri, 9:30 AM – 6:30 PM IST. After-hours messages get an auto-acknowledgement." },
  { id: "mem4", label: "Escalation policy", value: "Sentiment < 0.3 OR mentions of 'cancel', 'refund', 'angry' route to a human CSM in <5 min." },
  { id: "mem5", label: "Disqualifying signals", value: "<10 employees, no business email, free-tier-only intent." },
  { id: "mem6", label: "Preferred CTAs", value: "Book a demo · See pricing · Talk to sales. Avoid 'Sign up free'." },
];

export const AI_KNOWLEDGE_USAGE = [
  { id: "ku1", source: "Pricing Page", hits: 482, lastUsed: "2m ago" },
  { id: "ku2", source: "Product Docs", hits: 1218, lastUsed: "Just now" },
  { id: "ku3", source: "Help Center", hits: 326, lastUsed: "8m ago" },
  { id: "ku4", source: "Sales Battlecards", hits: 184, lastUsed: "32m ago" },
];
