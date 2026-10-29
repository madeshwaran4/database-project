"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ShieldCheck, Vote, UserCheck, Settings, LogIn, LogOut, Radio } from "lucide-react";
import { api, authStorage } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [pollingOpen, setPollingOpen] = useState<boolean | null>(null);
  const [user, setUser] = useState<{ username: string | null; role: string | null }>({ username: null, role: null });

  useEffect(() => {
    // Check user auth state
    const current = authStorage.getUser();
    setUser({ username: current.username, role: current.role });

    // Fetch polling status
    const fetchStatus = async () => {
      try {
        const res = await api.admin.getPollingStatus();
        setPollingOpen(res.is_open);
      } catch {
        // Backend might be starting or not connected
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, [pathname]);

  const handleLogout = () => {
    authStorage.clear();
    setUser({ username: null, role: null });
    router.push("/login");
  };

  const navLinks = [
    { href: "/booth", label: "Voting Booth", icon: Vote },
    { href: "/enroll", label: "Voter Enrollment", icon: UserCheck },
    { href: "/admin", label: "Admin & Results", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
              SecureVote
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              Zero-Link Core
            </span>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Polling Live Badge & User Profile */}
        <div className="flex items-center gap-4">
          {/* Polling Status Indicator */}
          {pollingOpen !== null && (
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
                pollingOpen
                  ? "bg-emerald-950/80 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/20"
                  : "bg-amber-950/60 text-amber-400 border-amber-500/40"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  pollingOpen ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                }`}
              />
              <span className="hidden sm:inline">{pollingOpen ? "Polling Open" : "Polling Closed"}</span>
              <span className="sm:hidden">{pollingOpen ? "Open" : "Closed"}</span>
            </div>
          )}

          {/* User controls */}
          {user.username ? (
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex flex-col text-right">
                <span className="text-xs font-semibold text-slate-200">{user.username}</span>
                <span className="text-[10px] text-cyan-400 uppercase tracking-wider font-mono">{user.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-rose-950/80 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-800 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white shadow-md shadow-cyan-600/20 transition"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Login</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
