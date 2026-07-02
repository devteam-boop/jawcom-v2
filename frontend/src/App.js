import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "@/layouts/AppLayout";
import Dashboard from "@/pages/Dashboard";
<<<<<<< HEAD
import Inbox from "@/pages/Inbox";
import Campaigns from "@/pages/Campaigns";
import Journeys from "@/pages/Journeys";
import JourneyDetail from "@/pages/JourneyDetail";
import Assistant from "@/pages/Assistant";
import Templates from "@/pages/Templates";
import Reports from "@/pages/Reports";
=======
import Conversations from "@/pages/Conversations";
import Contacts from "@/pages/Contacts";
import Campaigns from "@/pages/Campaigns";
import JourneyMonitor from "@/pages/JourneyMonitor";
import Automation from "@/pages/Automation";
import AutomationBuilder from "@/pages/AutomationBuilder";
import Assistant from "@/pages/Assistant";
import Templates from "@/pages/Templates";
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
import Knowledge from "@/pages/Knowledge";
import Integrations from "@/pages/Integrations";
import Developers from "@/pages/Developers";
import Settings from "@/pages/Settings";
import SearchPage from "@/pages/Search";
import { ThemeProvider } from "@/hooks/use-theme";
import { Toaster } from "@/components/ui/sonner";
import "@/App.css";

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
<<<<<<< HEAD
            <Route path="/inbox" element={<Inbox />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/journeys" element={<Journeys />} />
            <Route path="/journeys/:id" element={<JourneyDetail />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/knowledge" element={<Knowledge />} />
=======
            <Route path="/conversations" element={<Conversations />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/customers" element={<Navigate to="/contacts" replace />} />
            <Route path="/companies" element={<Navigate to="/contacts" replace />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/journeys" element={<JourneyMonitor />} />
            <Route path="/automation" element={<Automation />} />
            <Route path="/automation/builder" element={<AutomationBuilder />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/followups" element={<Navigate to="/journeys" replace />} />
            <Route path="/reports" element={<Navigate to="/" replace />} />
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/developers" element={<Developers />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" />
    </ThemeProvider>
  );
}

export default App;
