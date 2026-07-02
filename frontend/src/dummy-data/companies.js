export const COMPANIES = [
  { id: "co1", name: "Lumen Studio", logo: "LS", industry: "Design Agency", size: "11-50", primary: "Priya Sharma", openConvos: 3, stage: "Proposal", owner: "Maya Iyer", status: "Active", website: "lumenstudio.io", arr: "₹4.2L", contacts: 6, lastActivity: "2m ago" },
  { id: "co2", name: "Northwind", logo: "NW", industry: "B2B SaaS", size: "201-500", primary: "Daniel Chen", openConvos: 5, stage: "Negotiation", owner: "Maya Iyer", status: "Active", website: "northwind.co", arr: "₹18.4L", contacts: 14, lastActivity: "14m ago" },
  { id: "co3", name: "Atelier Rossi", logo: "AR", industry: "Fashion & Retail", size: "11-50", primary: "Sofia Rossi", openConvos: 1, stage: "Qualified", owner: "Rohan Mehta", status: "Active", website: "atelierrossi.it", arr: "₹2.8L", contacts: 4, lastActivity: "38m ago" },
  { id: "co4", name: "Kairos Labs", logo: "KL", industry: "Deep Tech", size: "51-200", primary: "Akira Tanaka", openConvos: 2, stage: "Won", owner: "Rohan Mehta", status: "Active", website: "kairos.ai", arr: "₹12.0L", contacts: 9, lastActivity: "1h ago" },
  { id: "co5", name: "Bloom & Co", logo: "BC", industry: "DTC Retail", size: "11-50", primary: "Lila Okafor", openConvos: 1, stage: "Negotiation", owner: "Maya Iyer", status: "Active", website: "bloomandco.shop", arr: "₹3.2L", contacts: 5, lastActivity: "3h ago" },
  { id: "co6", name: "Solare Group", logo: "SG", industry: "Energy", size: "501-1000", primary: "Marco Bianchi", openConvos: 0, stage: "Lost", owner: "Maya Iyer", status: "Inactive", website: "solare.eu", arr: "—", contacts: 11, lastActivity: "1d ago" },
  { id: "co7", name: "Mira Foods", logo: "MF", industry: "Food & Beverage", size: "201-500", primary: "Hana Park", openConvos: 2, stage: "Qualified", owner: "Rohan Mehta", status: "Active", website: "mirafoods.kr", arr: "₹6.6L", contacts: 8, lastActivity: "1d ago" },
  { id: "co8", name: "Vela Travel", logo: "VT", industry: "Travel & Hospitality", size: "51-200", primary: "Diego Alvarez", openConvos: 1, stage: "New", owner: "Maya Iyer", status: "Lead", website: "velatravel.mx", arr: "—", contacts: 3, lastActivity: "2d ago" },
  { id: "co9", name: "Cedar Health", logo: "CH", industry: "Healthcare", size: "51-200", primary: "Yuki Sato", openConvos: 0, stage: "Won", owner: "Ana Souza", status: "Active", website: "cedarhealth.jp", arr: "₹9.8L", contacts: 7, lastActivity: "2d ago" },
  { id: "co10", name: "Orbit Retail", logo: "OR", industry: "Retail", size: "1000+", primary: "Nour Haddad", openConvos: 4, stage: "Proposal", owner: "Maya Iyer", status: "Active", website: "orbitretail.com", arr: "₹24.0L", contacts: 18, lastActivity: "3d ago" },
  { id: "co11", name: "Pixel Forge", logo: "PF", industry: "Game Studio", size: "11-50", primary: "Olivia Bennett", openConvos: 1, stage: "Qualified", owner: "Rohan Mehta", status: "Active", website: "pixelforge.gg", arr: "₹1.6L", contacts: 4, lastActivity: "3d ago" },
  { id: "co12", name: "Nimbus Cloud", logo: "NC", industry: "Cloud Infra", size: "201-500", primary: "Kabir Singh", openConvos: 2, stage: "Negotiation", owner: "Ana Souza", status: "Active", website: "nimbus.cloud", arr: "₹15.2L", contacts: 12, lastActivity: "4d ago" },
];

export const COMPANY_CONTACTS = {
  co1: [
    { id: "ct1", name: "Priya Sharma", role: "Head of Design", email: "priya@lumenstudio.io", primary: true },
    { id: "ct2", name: "Arjun Mehta", role: "Founder", email: "arjun@lumenstudio.io", primary: false },
    { id: "ct3", name: "Riya Kapoor", role: "Ops", email: "riya@lumenstudio.io", primary: false },
  ],
  co2: [
    { id: "ct4", name: "Daniel Chen", role: "VP Sales", email: "daniel@northwind.co", primary: true },
    { id: "ct5", name: "Lisa Park", role: "RevOps", email: "lisa@northwind.co", primary: false },
    { id: "ct6", name: "Sam Wright", role: "Procurement", email: "sam@northwind.co", primary: false },
  ],
};

export const COMPANY_JOURNEY = [
  { id: "j1", stage: "Discovered", time: "Jan 4", status: "done", note: "Inbound via website demo form" },
  { id: "j2", stage: "Qualified", time: "Jan 8", status: "done", note: "Maya completed discovery call" },
  { id: "j3", stage: "Proposal", time: "Feb 1", status: "done", note: "Proposal sent — Growth plan" },
  { id: "j4", stage: "Negotiation", time: "Feb 12", status: "current", note: "Awaiting procurement approval" },
  { id: "j5", stage: "Won", time: "—", status: "upcoming", note: "Target close: Feb 28" },
];
