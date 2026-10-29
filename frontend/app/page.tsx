import Link from "next/link";
import { Vote, UserCheck, ShieldCheck, Lock, Activity, Users, ArrowRight } from "lucide-react";

export default function Home() {
  const cards = [
    {
      href: "/booth",
      title: "Voting Booth Kiosk",
      desc: "Step-by-step biometric verification and confidential ballot casting with automatic session reset.",
      icon: Vote,
      color: "from-cyan-500 to-blue-600",
      cta: "Launch Kiosk Flow",
    },
    {
      href: "/enroll",
      title: "Voter Enrollment",
      desc: "Register eligible voters with salted ID hashing, 1:N duplicate person deduplication, and encrypted minutiae templates.",
      icon: UserCheck,
      color: "from-emerald-500 to-teal-600",
      cta: "Enroll Citizen",
    },
    {
      href: "/admin",
      title: "Admin & Results",
      desc: "Manage candidate slates, toggle polling states, inspect real-time audit logs, and view finalized election tallies.",
      icon: ShieldCheck,
      color: "from-indigo-500 to-purple-600",
      cta: "Open Admin Dashboard",
    },
  ];

  const rules = [
    {
      title: "Zero-Link Decoupling",
      desc: "VOTE records contain NO voter ID, foreign key, or fine timestamp.",
    },
    {
      title: "Atomic Row-Level Flip",
      desc: "UPDATE has_voted and INSERT vote occur in the same transaction.",
    },
    {
      title: "Biometric Template AES Encryption",
      desc: "Minutiae encrypted before database persistence with application keys.",
    },
    {
      title: "Salted ID Hashing",
      desc: "Only the last 4 digits plus SHA-256 salted hash stored for verification.",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/70 border border-cyan-800/80 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-6">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>Duplicate-Vote Prevention System</span>
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-6">
          Cryptographically Guaranteed{" "}
          <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
            Election Integrity
          </span>
        </h1>
        <p className="text-lg text-slate-300 leading-relaxed">
          SecureVote eliminates double voting and ballot stuffing through biometric 1:1 fingerprint verification,
          application-level template encryption, and absolute structural decoupling between voters and cast votes.
        </p>
      </div>

      {/* Main Module Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group glass-panel rounded-2xl p-8 hover:border-cyan-500/40 transition-all duration-300 flex flex-col justify-between hover:-translate-y-1 hover:shadow-2xl hover:shadow-cyan-500/10"
            >
              <div>
                <div
                  className={`w-14 h-14 rounded-2xl bg-gradient-to-tr ${card.color} flex items-center justify-center text-white mb-6 shadow-lg group-hover:scale-105 transition`}
                >
                  <Icon className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-white mb-3 group-hover:text-cyan-300 transition">
                  {card.title}
                </h2>
                <p className="text-sm text-slate-400 leading-relaxed mb-6">{card.desc}</p>
              </div>

              <div className="flex items-center gap-2 text-sm font-semibold text-cyan-400 group-hover:text-cyan-300">
                <span>{card.cta}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Non-Negotiable Architecture Rules Section */}
      <div className="glass-panel rounded-3xl p-8 sm:p-12 border border-slate-800">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-white mb-3">Architectural Non-Negotiables</h2>
          <p className="text-sm text-slate-400">
            Formally codified in AGENTS.md to make voter identification and ballot correlation mathematically impossible.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {rules.map((rule, idx) => (
            <div key={idx} className="bg-slate-900/60 rounded-xl p-5 border border-slate-800/80">
              <div className="w-7 h-7 rounded-lg bg-cyan-950 text-cyan-400 flex items-center justify-center text-xs font-bold mb-3 border border-cyan-800/50">
                0{idx + 1}
              </div>
              <h3 className="text-sm font-semibold text-white mb-2">{rule.title}</h3>
              <p className="text-xs text-slate-400 leading-normal">{rule.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
