import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { DeliveryReport, JourneyAnalytics, CampaignAnalytics } from "@/modules/reports";

export default function Reports() {
  const [tab, setTab] = useState("delivery");

  return (
    <div data-testid="page-reports">
      <PageHeader
        title="Reports"
        description="Communication analytics and performance metrics."
      />

      <div className="px-4 py-6 md:px-8">
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="delivery" className="text-xs">Delivery Report</TabsTrigger>
            <TabsTrigger value="journeys" className="text-xs">Journey Analytics</TabsTrigger>
            <TabsTrigger value="campaigns" className="text-xs">Campaign Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="delivery">
            <DeliveryReport />
          </TabsContent>

          <TabsContent value="journeys">
            <JourneyAnalytics />
          </TabsContent>

          <TabsContent value="campaigns">
            <CampaignAnalytics />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
