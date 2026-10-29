"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Power,
  Users,
  Vote,
  AlertOctagon,
  TrendingUp,
  FileText,
  Plus,
  Trash2,
  Edit2,
  Lock,
  Unlock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Award,
} from "lucide-react";
import {
  api,
  ElectionStats,
  PollingStatusResponse,
  Candidate,
  ElectionResults,
  PaginatedLogsResponse,
  authStorage,
} from "@/lib/api";

export default function AdminPage() {
  const [stats, setStats] = useState<ElectionStats | null>(null);
  const [pollingStatus, setPollingStatus] = useState<PollingStatusResponse | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [results, setResults] = useState<ElectionResults | null>(null);
  const [logsData, setLogsData] = useState<PaginatedLogsResponse | null>(null);

  // Filters
  const [logFilterResult, setLogFilterResult] = useState("");
  const [logPage, setLogPage] = useState(1);

  // Modals & form state
  const [showAddCandidate, setShowAddCandidate] = useState(false);
  const [newCandName, setNewCandName] = useState("");
  const [newCandParty, setNewCandParty] = useState("");
  const [newCandDesc, setNewCandDesc] = useState("");

  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    refreshAllData();
  }, [logPage, logFilterResult]);

  const refreshAllData = async () => {
    try {
      const [statsRes, pollingRes, candRes] = await Promise.all([
        api.admin.getStats().catch(() => null),
        api.admin.getPollingStatus().catch(() => null),
        api.admin.getCandidates().catch(() => []),
      ]);

      if (statsRes) setStats(statsRes);
      if (pollingRes) setPollingStatus(pollingRes);
      if (candRes) setCandidates(candRes);

      // Attempt loading results (will fail with 403 if polling is open)
      try {
        const resData = await api.admin.getResults();
        setResults(resData);
      } catch {
        setResults(null);
      }

      // Load logs
      try {
        const logsRes = await api.admin.getLogs({
          result: logFilterResult || undefined,
          page: logPage,
          page_size: 10,
        });
        setLogsData(logsRes);
      } catch (logErr: any) {
        console.warn("Could not fetch verification logs:", logErr.message);
      }
    } catch (e: any) {
      console.error("Error refreshing admin data", e);
    }
  };

  const handleTogglePolling = async () => {
    if (!pollingStatus) return;
    setLoading(true);
    setActionMsg(null);
    try {
      if (pollingStatus.is_open) {
        const res = await api.admin.closePolling();
        setPollingStatus(res);
        setActionMsg({ type: "success", text: "Polling officially CLOSED. Results are now unsealed and viewable." });
      } else {
        const res = await api.admin.openPolling();
        setPollingStatus(res);
        setActionMsg({ type: "success", text: "Polling officially OPENED. Voter enrollment & candidate modifications are locked." });
      }
      refreshAllData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message || "Failed to toggle polling state." });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.admin.createCandidate({
        name: newCandName,
        party: newCandParty,
        description: newCandDesc,
      });
      setShowAddCandidate(false);
      setNewCandName("");
      setNewCandParty("");
      setNewCandDesc("");
      setActionMsg({ type: "success", text: "Candidate successfully registered." });
      refreshAllData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message || "Failed to create candidate." });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCandidate = async (id: string) => {
    if (!confirm("Are you sure you want to delete this candidate?")) return;
    try {
      await api.admin.deleteCandidate(id);
      setActionMsg({ type: "success", text: "Candidate deleted." });
      refreshAllData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message || "Failed to delete candidate." });
    }
  };

  const isPollingOpen = pollingStatus?.is_open ?? false;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Header & Polling Controls */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <ShieldCheck className="w-4 h-4" />
            <span>Administrative Command Center</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Election Management & Audit</h1>
          <p className="text-slate-400 text-sm mt-1">
            Control the election lifecycle, inspect verification telemetry, and view finalized tallies.
          </p>
        </div>

        {/* Polling Switch */}
        <div className="flex items-center gap-4 bg-slate-900/90 p-3 rounded-2xl border border-slate-800">
          <div className="text-right">
            <span className="text-[11px] text-slate-400 block font-semibold uppercase">Election State</span>
            <span
              className={`text-sm font-bold uppercase tracking-wider ${
                isPollingOpen ? "text-emerald-400" : "text-amber-400"
              }`}
            >
              {isPollingOpen ? "Polling Open" : "Polling Closed"}
            </span>
          </div>

          <button
            onClick={handleTogglePolling}
            disabled={loading}
            className={`py-3 px-5 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition cursor-pointer shadow-lg ${
              isPollingOpen
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30"
            }`}
          >
            <Power className="w-4 h-4" />
            <span>{isPollingOpen ? "Close Polling" : "Open Polling"}</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div
          className={`p-4 rounded-2xl border text-sm flex items-center justify-between ${
            actionMsg.type === "success"
              ? "bg-emerald-950/80 border-emerald-600/80 text-emerald-200"
              : "bg-rose-950/80 border-rose-600/80 text-rose-200"
          }`}
        >
          <span>{actionMsg.text}</span>
          <button onClick={() => setActionMsg(null)} className="text-xs text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/80 text-cyan-400 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase">Enrolled Citizens</span>
            <span className="text-2xl font-extrabold text-white">{stats?.enrolled_voters ?? 0}</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-950/80 border border-emerald-800/80 text-emerald-400 flex items-center justify-center">
            <Vote className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase">Votes Deposited</span>
            <span className="text-2xl font-extrabold text-white">{stats?.votes_cast ?? 0}</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-950/80 border border-indigo-800/80 text-indigo-400 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase">Turnout Percentage</span>
            <span className="text-2xl font-extrabold text-white">{stats?.turnout_percentage ?? 0}%</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-rose-950/80 border border-rose-800/80 text-rose-400 flex items-center justify-center">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase">Denied Attempts</span>
            <span className="text-2xl font-extrabold text-white">{stats?.denied_attempts ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Candidate Slate Management */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Candidate Slate</h2>
            <p className="text-xs text-slate-400 mt-1">
              Registered candidates on the electronic ballot. Modifications are prohibited while polling is open.
            </p>
          </div>

          <button
            onClick={() => setShowAddCandidate(true)}
            disabled={isPollingOpen}
            className="py-2 px-4 rounded-xl font-semibold text-xs text-white bg-cyan-600 hover:bg-cyan-500 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Add Candidate</span>
          </button>
        </div>

        {isPollingOpen && (
          <div className="mb-4 p-3 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-300 flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            <span>Candidate slate is locked during active polling.</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {candidates.map((c) => (
            <div
              key={c.candidate_id}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between"
            >
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-700">
                  {c.party}
                </span>
                <h3 className="text-lg font-bold text-white mt-3">{c.name}</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{c.description}</p>
              </div>

              {!isPollingOpen && (
                <div className="mt-4 pt-3 border-t border-slate-800 flex justify-end">
                  <button
                    onClick={() => handleDeleteCandidate(c.candidate_id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 transition"
                    title="Delete Candidate"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ADD CANDIDATE MODAL */}
      {showAddCandidate && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel rounded-3xl p-6 max-w-md w-full border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4">Register New Candidate</h3>
            <form onSubmit={handleCreateCandidate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                  Candidate Name
                </label>
                <input
                  type="text"
                  required
                  value={newCandName}
                  onChange={(e) => setNewCandName(e.target.value)}
                  placeholder="e.g. Dr. Julian Croft"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                  Party / Coalition
                </label>
                <input
                  type="text"
                  required
                  value={newCandParty}
                  onChange={(e) => setNewCandParty(e.target.value)}
                  placeholder="e.g. Freedom & Unity Movement"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                  Description / Platform
                </label>
                <textarea
                  rows={3}
                  value={newCandDesc}
                  onChange={(e) => setNewCandDesc(e.target.value)}
                  placeholder="Summary of candidate platform..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddCandidate(false)}
                  className="flex-1 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white"
                >
                  Add Candidate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ELECTION RESULTS SECTION */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Finalized Election Results</h2>
            <p className="text-xs text-slate-400 mt-1">
              Official ballot counts per candidate. Access is restricted until polling officially closes.
            </p>
          </div>
        </div>

        {isPollingOpen ? (
          <div className="p-8 rounded-2xl bg-slate-900/90 border border-amber-600/50 text-center max-w-xl mx-auto">
            <div className="w-14 h-14 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-4 border border-amber-500/30">
              <Lock className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Results Sealed During Active Polling</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              In accordance with election privacy laws and Phase 6 specifications, the tally endpoint (GET /api/results)
              is cryptographically sealed with HTTP 403 Forbidden until an administrator closes the polling session.
            </p>
          </div>
        ) : results ? (
          <div>
            <div className="mb-6 flex items-center justify-between bg-slate-900/90 p-4 rounded-2xl border border-slate-800">
              <div>
                <span className="text-xs text-slate-400 block font-semibold uppercase">Total Ballots Cast</span>
                <span className="text-3xl font-extrabold text-white">{results.total_votes}</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold bg-emerald-950/80 px-3 py-1.5 rounded-xl border border-emerald-800/80">
                <CheckCircle2 className="w-4 h-4" />
                <span>Results Certified</span>
              </div>
            </div>

            <div className="space-y-4">
              {results.results.map((r, idx) => (
                <div key={r.candidate_id} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      {idx === 0 && <Award className="w-5 h-5 text-amber-400" />}
                      <div>
                        <h4 className="font-bold text-white text-base">{r.name}</h4>
                        <span className="text-xs text-slate-400">{r.party}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-extrabold text-white">{r.vote_count} votes</span>
                      <span className="text-xs text-cyan-400 block font-semibold">{r.percentage}%</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        idx === 0 ? "bg-gradient-to-r from-amber-400 to-orange-500" : "bg-gradient-to-r from-cyan-500 to-indigo-500"
                      }`}
                      style={{ width: `${r.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500 text-xs">No ballot results available yet.</div>
        )}
      </div>

      {/* VERIFICATION AUDIT LOGS TABLE */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Biometric Verification Audit Trail</h2>
            <p className="text-xs text-slate-400 mt-1">
              Immutable logging of every booth verification attempt (AGENTS.md Rule 6).
            </p>
          </div>

          {/* Filter dropdown */}
          <div className="flex items-center gap-3">
            <select
              value={logFilterResult}
              onChange={(e) => {
                setLogFilterResult(e.target.value);
                setLogPage(1);
              }}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none"
            >
              <option value="">All Verification Results</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="DUPLICATE_ATTEMPT">DUPLICATE_ATTEMPT</option>
              <option value="BIOMETRIC_MISMATCH">BIOMETRIC_MISMATCH</option>
              <option value="LOCKED_OUT">LOCKED_OUT</option>
              <option value="POLLING_CLOSED">POLLING_CLOSED</option>
            </select>

            <button
              onClick={refreshAllData}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Result</th>
                <th className="py-3 px-4">Audit Reason</th>
                <th className="py-3 px-4">Workstation</th>
                <th className="py-3 px-4">Log UUID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {!logsData || logsData.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500 font-sans">
                    No verification log entries found matching filters.
                  </td>
                </tr>
              ) : (
                logsData.items.map((log) => {
                  const isSuccess = log.result === "SUCCESS";
                  const isDuplicate = log.result === "DUPLICATE_ATTEMPT";
                  return (
                    <tr key={log.log_id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-4 text-slate-300">{log.attempted_at.replace("T", " ").substring(0, 19)}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            isSuccess
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : isDuplicate
                              ? "bg-rose-950 text-rose-400 border border-rose-800"
                              : "bg-amber-950 text-amber-400 border border-amber-800"
                          }`}
                        >
                          {log.result}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-sans max-w-xs truncate">{log.reason}</td>
                      <td className="py-3 px-4 text-slate-400">{log.workstation_id}</td>
                      <td className="py-3 px-4 text-slate-500 text-[10px] truncate max-w-[120px]">{log.log_id}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {logsData && logsData.total_pages > 1 && (
          <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing Page {logsData.page} of {logsData.total_pages} ({logsData.total} logs)
            </span>
            <div className="flex gap-2">
              <button
                disabled={logPage <= 1}
                onClick={() => setLogPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={logPage >= logsData.total_pages}
                onClick={() => setLogPage((p) => p + 1)}
                className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
