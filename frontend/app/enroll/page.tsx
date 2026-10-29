"use client";

import { useState, useEffect } from "react";
import { UserPlus, Search, CheckCircle2, AlertTriangle, ShieldCheck, User, CreditCard, Hash } from "lucide-react";
import FingerprintScanner from "@/components/FingerprintScanner";
import { api, VoterEnrollResponse, VoterSearchItem } from "@/lib/api";

export default function EnrollPage() {
  const [name, setName] = useState("");
  const [idType, setIdType] = useState("National Identity Card");
  const [idNumber, setIdNumber] = useState("");
  const [fingerprintImage, setFingerprintImage] = useState("");
  const [loading, setLoading] = useState(false);
  const [pollingOpen, setPollingOpen] = useState(false);
  const [successResult, setSuccessResult] = useState<VoterEnrollResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<VoterSearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    // Check polling status
    api.admin.getPollingStatus().then((s) => setPollingOpen(s.is_open)).catch(() => {});
    loadVoters();
  }, []);

  const loadVoters = async (query = "") => {
    setSearchLoading(true);
    try {
      const items = await api.enrollment.searchVoters(query || undefined);
      setSearchResults(items);
    } catch {
      // Ignore initial search failures if not logged in
    } finally {
      setSearchLoading(false);
    }
  };

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fingerprintImage) {
      setError("Please capture or upload a biometric fingerprint scan before submitting.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await api.enrollment.enroll({
        name,
        id_type: idType,
        id_number: idNumber,
        fingerprint_image: fingerprintImage,
      });
      setSuccessResult(res);
      // Reset form
      setName("");
      setIdNumber("");
      setFingerprintImage("");
      loadVoters();
    } catch (err: any) {
      setError(err.message || "Enrollment failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <UserPlus className="w-4 h-4" />
          <span>Voter Registry</span>
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Citizen Biometric Enrollment</h1>
        <p className="text-slate-400 text-sm mt-1">
          Secure biometric registration with salted identity hashing and 1:N fingerprint deduplication.
        </p>
      </div>

      {pollingOpen && (
        <div className="mb-8 p-4 rounded-2xl bg-amber-950/80 border border-amber-600/80 flex items-start gap-3 text-amber-200">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">Enrollment Blocked: Polling Is Currently Active</h4>
            <p className="text-xs text-amber-300 mt-0.5">
              To prevent voter roll alteration during active elections, new citizen registrations are disabled while
              polling is open.
            </p>
          </div>
        </div>
      )}

      {successResult && (
        <div className="mb-8 p-6 rounded-2xl bg-emerald-950/80 border border-emerald-500/80 text-emerald-100 flex items-start gap-4">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 shrink-0" />
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white">Voter Successfully Enrolled</h3>
            <p className="text-xs text-emerald-300 mt-1">
              Biometric template encrypted with application-layer AES-256 before persistence. Plaintext ID discarded.
            </p>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono bg-emerald-900/40 p-3 rounded-xl border border-emerald-700/50">
              <div>
                <span className="text-emerald-400 block">Citizen Name</span>
                <span className="font-semibold text-white">{successResult.name}</span>
              </div>
              <div>
                <span className="text-emerald-400 block">ID Masked</span>
                <span className="font-semibold text-white">•••• {successResult.id_last4}</span>
              </div>
              <div>
                <span className="text-emerald-400 block">Voter UUID</span>
                <span className="font-semibold text-white truncate block">{successResult.voter_id.substring(0, 13)}...</span>
              </div>
              <div>
                <span className="text-emerald-400 block">Voting Status</span>
                <span className="font-semibold text-white">{successResult.has_voted === "N" ? "Eligible" : "Voted"}</span>
              </div>
            </div>
            <button
              onClick={() => setSuccessResult(null)}
              className="mt-4 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-800 hover:bg-emerald-700 text-white transition"
            >
              Enroll Another Citizen
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-8 p-4 rounded-2xl bg-rose-950/80 border border-rose-700 text-rose-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Enrollment Form */}
        <div className="lg:col-span-7 glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800">
          <form onSubmit={handleEnroll} className="space-y-6">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Full Legal Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  disabled={pollingOpen || loading}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Maria Elena Vance"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  ID Document Type
                </label>
                <div className="relative">
                  <CreditCard className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  <select
                    disabled={pollingOpen || loading}
                    value={idType}
                    onChange={(e) => setIdType(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
                  >
                    <option value="National Identity Card">National Identity Card</option>
                    <option value="Passport">Passport</option>
                    <option value="Driver's License">Driver's License</option>
                    <option value="Voter Card">Voter Card</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  ID Document Number
                </label>
                <div className="relative">
                  <Hash className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  <input
                    type="text"
                    required
                    disabled={pollingOpen || loading}
                    value={idNumber}
                    onChange={(e) => setIdNumber(e.target.value)}
                    placeholder="e.g. NAT-987654321"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Biometric Capture */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Biometric Fingerprint Minutiae Acquisition
              </label>
              <FingerprintScanner
                onCapture={(b64) => {
                  setFingerprintImage(b64);
                  setError(null);
                }}
                label="Touch sensor or select test finger to acquire template"
              />
            </div>

            <button
              type="submit"
              disabled={pollingOpen || loading || !fingerprintImage}
              className="w-full py-3 px-4 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 transition shadow-lg shadow-emerald-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? "Encrypting & Enrolling..." : "Complete Voter Enrollment"}
            </button>
          </form>
        </div>

        {/* Existing Enrolled Voters Preview */}
        <div className="lg:col-span-5 glass-panel rounded-3xl p-6 border border-slate-800 flex flex-col h-full">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-base">Enrolled Voters Registry</h3>
            <span className="text-xs text-slate-400 font-mono">{searchResults.length} enrolled</span>
          </div>

          <div className="relative mb-4">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                loadVoters(e.target.value);
              }}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 max-h-[500px] pr-1">
            {searchResults.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-xs">
                {searchLoading ? "Loading voters..." : "No voters match your search query."}
              </div>
            ) : (
              searchResults.map((voter) => (
                <div
                  key={voter.voter_id}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs"
                >
                  <div>
                    <h4 className="font-semibold text-white">{voter.name}</h4>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {voter.id_type} &bull; •••• {voter.id_last4}
                    </span>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                      voter.has_voted === "Y"
                        ? "bg-slate-800 text-slate-400 border border-slate-700"
                        : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    }`}
                  >
                    {voter.has_voted === "Y" ? "Voted" : "Eligible"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
