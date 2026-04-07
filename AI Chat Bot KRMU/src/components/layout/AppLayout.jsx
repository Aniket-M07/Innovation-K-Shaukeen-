import { useState } from "react";
import { motion } from "framer-motion";
import Navbar from "./Navbar";
import SidebarNav from "./SidebarNav";

function AppLayout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <Navbar onMenuClick={() => setMobileOpen(true)} />
      <main className="mx-auto flex w-full max-w-7xl gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <SidebarNav mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <motion.section
          className="min-w-0 flex-1"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {children}
        </motion.section>
      </main>
    </div>
  );
}

export default AppLayout;