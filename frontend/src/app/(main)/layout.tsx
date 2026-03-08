import { Sidebar } from "@/components/sidebar";
import ProtectedRoute from "@/components/protected-route";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto p-4 pb-16 md:p-6 md:pb-6">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

