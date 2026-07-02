const BASE = "/api/jawis";

export const jawisService = {
  getLead: async (leadId) => {
    const res = await fetch(`${BASE}/leads/${leadId}`);
    if (!res.ok) throw new Error("Failed to fetch lead from JAWIS");
    return res.json();
  },
  getCompany: async (companyId) => {
    const res = await fetch(`${BASE}/companies/${companyId}`);
    if (!res.ok) throw new Error("Failed to fetch company from JAWIS");
    return res.json();
  },
  getLeadStage: async (leadId) => {
    const res = await fetch(`${BASE}/leads/${leadId}/stage`);
    if (!res.ok) throw new Error("Failed to fetch lead stage from JAWIS");
    return res.json();
  },
  searchLeads: async (query) => {
    const res = await fetch(`${BASE}/leads?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("Failed to search leads in JAWIS");
    return res.json();
  },
};
