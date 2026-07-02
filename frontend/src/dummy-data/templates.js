export const TEMPLATES = {
  whatsapp: [
    { id: "tw1", name: "Welcome message", preview: "Hi {{first_name}}, welcome to {{workspace}}! We're thrilled to have you onboard. Reply START to begin.", language: "EN", category: "Utility", status: "Approved", lastEdited: "Feb 12" },
    { id: "tw2", name: "Pricing reminder", preview: "Hey {{first_name}}, just a gentle nudge — your custom quote is ready and waiting. Want to walk through it?", language: "EN", category: "Marketing", status: "Approved", lastEdited: "Feb 10" },
    { id: "tw3", name: "Demo confirmation", preview: "Confirmed! Your demo with {{owner}} is on {{date}} at {{time}} IST. Reply CANCEL to reschedule.", language: "EN", category: "Utility", status: "Approved", lastEdited: "Feb 6" },
    { id: "tw4", name: "Renewal nudge", preview: "Hey {{first_name}}, your {{plan}} renews in {{days}} days. Tap below to extend with a 10% loyalty discount.", language: "EN", category: "Marketing", status: "In Review", lastEdited: "Today" },
    { id: "tw5", name: "Festive greeting", preview: "Warm wishes from {{workspace}} this festive season! Thank you for being part of our story.", language: "HI", category: "Marketing", status: "Approved", lastEdited: "Jan 21" },
    { id: "tw6", name: "Cart abandonment", preview: "Still thinking about it? {{product}} is back in stock for you, {{first_name}}.", language: "EN", category: "Marketing", status: "Draft", lastEdited: "Yesterday" },
  ],
  email: [
    { id: "te1", name: "Q1 proposal", preview: "Subject: Your Q1 proposal — Growth Plan\nHi {{first_name}}, attached is the tailored Growth plan we discussed last week…", language: "EN", category: "Sales", status: "Approved", lastEdited: "Feb 8" },
    { id: "te2", name: "Onboarding day 1", preview: "Subject: Welcome to {{workspace}}\nWe're so glad you're here. Here's your roadmap for the first 7 days…", language: "EN", category: "Lifecycle", status: "Approved", lastEdited: "Feb 1" },
    { id: "te3", name: "Demo recap", preview: "Subject: Recap from our call today\nHi {{first_name}}, here's a quick summary plus the resources I mentioned…", language: "EN", category: "Sales", status: "Approved", lastEdited: "Jan 28" },
    { id: "te4", name: "Renewal terms", preview: "Subject: Your renewal terms for {{year}}\nWe've prepared an updated commercial for your account…", language: "EN", category: "Lifecycle", status: "Draft", lastEdited: "Today" },
  ],
  sms: [
    { id: "ts1", name: "OTP", preview: "Your OTP is {{code}}. Valid for 5 minutes. Do not share.", language: "EN", category: "Transactional", status: "Approved", lastEdited: "Stable" },
    { id: "ts2", name: "Delivery update", preview: "Your order {{order_id}} is out for delivery. Track: {{link}}", language: "EN", category: "Transactional", status: "Approved", lastEdited: "Stable" },
    { id: "ts3", name: "Demo reminder", preview: "Reminder: Demo with {{owner}} at {{time}} today. Reply 1 to confirm.", language: "EN", category: "Utility", status: "Approved", lastEdited: "Feb 4" },
  ],
  voice: [
    { id: "tv1", name: "Appointment confirmation IVR", preview: "Hello, this is a confirmation call for your appointment on {{date}}. Press 1 to confirm, 2 to reschedule.", language: "EN", category: "IVR", status: "Approved", lastEdited: "Feb 2" },
    { id: "tv2", name: "Renewal reminder voice", preview: "This is a friendly reminder from {{workspace}} that your subscription renews soon. Press 1 to speak to your account manager.", language: "EN", category: "Lifecycle", status: "Draft", lastEdited: "Today" },
  ],
};
