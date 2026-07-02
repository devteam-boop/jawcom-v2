export const CHANNELS = {
  whatsapp: {
    id: "whatsapp",
    label: "WhatsApp",
    provider: "Meta Cloud API",
    templateSource: "Meta-hosted templates",
    approval: "Meta-approved",
    icon: "MessageCircle",
  },
  email: {
    id: "email",
    label: "Email",
    provider: "SMTP / Gmail API",
    templateSource: "JawCom-hosted templates",
    approval: "Internal approval",
    icon: "Mail",
  },
};

export const CHANNEL_LIST = Object.values(CHANNELS);

export const CHANNEL_ICON = {
  whatsapp: "MessageCircle",
  email: "Mail",
};
