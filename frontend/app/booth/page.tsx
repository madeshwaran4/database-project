"use client";

import { useState, useEffect } from "react";
import {
  Vote,
  Search,
  UserCheck,
  Fingerprint,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Check,
  Shield,
  Clock,
  ArrowRight,
  Zap,
} from "lucide-react";
import FingerprintScanner from "@/components/FingerprintScanner";
import { api, VoterSearchItem, Candidate, VerifyResponse, VoteCastResponse } from "@/lib/api";

type BoothStep = "select_voter" | "scan_fingerprint" | "verification_result" | "ballot" | "vote_success";

export default function BoothPage() {
  const [currentStep, setCurrentStep] = useState<BoothStep>("select_voter");
  const [searchQuery, setSearchQuery] = useState("");
  const [voters, setVoters] = useState<VoterSearchItem[]>([]);
  const [selectedVoter, setSelectedVoter] = useState<VoterSearchItem | null>(null);

  // Biometric state
  const [fingerprintScan, setFingerprintScan] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);

  // Ballot state
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isCastingVote, setIsCastingVote] = useState(false);
  const [voteSuccessData, setVoteSuccessData] = useState<VoteCastResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-reset countdown
  const [countdown, setCountdown] = useState(5);

  // Load candidates and initial voters
  useEffect(() => {
    loadVoters();
    api.admin.getCandidates().then(setCandidates).catch(() => {});
  }, []);

  const loadVoters = async (query = "") => {
    try {
      const list = await api.enrollment.searchVoters(query || undefined);
      setVoters(list);
    } catch {
      // Ignored if offline
    }
  };

  // Auto reset timer for Step: vote_success
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (currentStep === "vote_success") {
      setCountdown(5);
      timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            resetKioskSession();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [currentStep]);

  const resetKioskSession = () => {
    setCurrentStep("select_voter");
    setSelectedVoter(null);
    setFingerprintScan("");
    setVerifyResult(null);
    setSelectedCandidate(null);
    setShowConfirmModal(false);
    setVoteSuccessData(null);
    setErrorMsg(null);
    loadVoters();
  };

  const handleSelectVoter = (voter: VoterSearchItem, bypass = false) => {
    if (voter.has_voted === "Y") {
      setErrorMsg(`Voter ${voter.name} has already cast a ballot in this election.`);
      return;
    }
    setErrorMsg(null);
    setSelectedVoter(voter);
    if (bypass) {
      handleBypassVerification(voter);
    } else {
      setCurrentStep("scan_fingerprint");
    }
  };

  const handleBypassVerification = async (voter?: VoterSearchItem) => {
    const target = voter || selectedVoter;
    if (!target) return;
    setIsVerifying(true);
    setErrorMsg(null);

    try {
      const res = await api.booth.verify({
        voter_id: target.voter_id,
        fingerprint_scan: "BYPASS",
        workstation_id: "kiosk-booth-01",
      });
      setVerifyResult(res);
      if (res.allowed && res.vote_token) {
        setCurrentStep("ballot");
      } else {
        setCurrentStep("verification_result");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Bypass verification request failed.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleVerifyBiometrics = async (scanB64: string) => {
    if (!selectedVoter) return;
    setFingerprintScan(scanB64);
    setIsVerifying(true);
    setErrorMsg(null);

    try {
      const res = await api.booth.verify({
        voter_id: selectedVoter.voter_id,
        fingerprint_scan: scanB64 || "BYPASS",
        workstation_id: "kiosk-booth-01",
      });
      setVerifyResult(res);
      if (res.allowed && res.vote_token) {
        setCurrentStep("ballot");
      } else {
        setCurrentStep("verification_result");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Verification request failed.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleProceedToBallot = () => {
    if (verifyResult?.allowed && verifyResult.vote_token) {
      setCurrentStep("ballot");
    }
  };

  const handleConfirmVote = async () => {
    if (!selectedCandidate || !verifyResult?.vote_token) return;
    setIsCastingVote(true);
    setErrorMsg(null);

    try {
      const res = await api.booth.vote({
        candidate_id: selectedCandidate.candidate_id,
        vote_token: verifyResult.vote_token,
      });

      // CRITICAL DESIGN RULE: Never store or display candidate choice after submission
      setSelectedCandidate(null);
      setVerifyResult(null);
      setShowConfirmModal(false);

      setVoteSuccessData(res);
      setCurrentStep("vote_success");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record vote.");
      setShowConfirmModal(false);
    } finally {
      setIsCastingVote(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Kiosk Step Progress Bar */}
      <div className="glass-panel rounded-2xl p-4 mb-8 flex items-center justify-between text-xs font-semibold text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-cyan-600/20 text-cyan-400 flex items-center justify-center font-bold">
            {currentStep === "select_voter" && "1"}
            {currentStep === "scan_fingerprint" && "2"}
            {currentStep === "verification_result" && "3"}
            {currentStep === "ballot" && "4"}
            {currentStep === "vote_success" && "✓"}
          </div>
          <span className="text-white text-sm font-bold tracking-tight">Official Voting Kiosk</span>
        </div>

        {selectedVoter && currentStep !== "vote_success" && (
          <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1 rounded-lg border border-slate-700/80">
            <span className="text-slate-400">Active Voter:</span>
            <span className="text-cyan-400 font-semibold">{selectedVoter.name}</span>
            <span className="text-slate-500 font-mono">(•••• {selectedVoter.id_last4})</span>
          </div>
        )}

        {currentStep !== "vote_success" && (
          <button
            onClick={resetKioskSession}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-700/60 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Kiosk</span>
          </button>
        )}
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: Search & Select Voter */}
      {currentStep === "select_voter" && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800">
          <div className="text-center max-w-xl mx-auto mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Step 1: Check In Citizen</h2>
            <p className="text-sm text-slate-400">
              Locate the voter in the electoral register by legal name to initiate 1:1 biometric matching.
            </p>
          </div>

          <div className="relative max-w-md mx-auto mb-8">
            <Search className="w-5 h-5 text-slate-500 absolute left-4 top-3.5" />
            <input
              type="text"
              placeholder="Search voter by legal name..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                loadVoters(e.target.value);
              }}
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[420px] overflow-y-auto pr-1">
            {voters.map((v) => {
              const hasVoted = v.has_voted === "Y";
              return (
                <div
                  key={v.voter_id}
                  className={`p-5 rounded-2xl border transition flex items-center justify-between gap-3 ${
                    hasVoted
                      ? "bg-slate-900/30 border-slate-800/50 opacity-50"
                      : "bg-slate-900/80 border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800/80 shadow-md"
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-white text-base truncate">{v.name}</h3>
                    <p className="text-xs text-slate-400 font-mono mt-1">
                      {v.id_type} &bull; Masked: •••• {v.id_last4}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {hasVoted ? (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase bg-slate-800 text-slate-500 border border-slate-700">
                        Already Voted
                      </span>
                    ) : (
                      <>
                        <button
                          type="button"
                          disabled={isVerifying}
                          onClick={() => handleSelectVoter(v, true)}
                          className="px-3 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-md shadow-emerald-950 flex items-center gap-1.5 cursor-pointer transition active:scale-95"
                          title="Instant access without physical biometric scanner"
                        >
                          <Zap className="w-3.5 h-3.5 text-amber-300" />
                          <span>Vote (Bypass)</span>
                        </button>
                        <button
                          type="button"
                          disabled={isVerifying}
                          onClick={() => handleSelectVoter(v, false)}
                          className="px-2.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition cursor-pointer"
                          title="Step-by-step scanner view"
                        >
                          &rarr;
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 2: Scan Fingerprint */}
      {currentStep === "scan_fingerprint" && selectedVoter && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800 max-w-xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Step 2: Biometric Verification</h2>
            <p className="text-sm text-slate-400">
              Voter: <strong className="text-cyan-400 text-base">{selectedVoter.name}</strong>
            </p>
          </div>

          {/* Prominent Bypass Card */}
          <div className="mb-6 p-5 rounded-2xl bg-cyan-950/40 border border-cyan-700/60 text-center shadow-lg shadow-cyan-950/50">
            <div className="flex items-center justify-center gap-2 text-cyan-300 text-xs font-semibold mb-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>No Physical Fingerprint Sensor?</span>
            </div>
            <p className="text-xs text-slate-300 mb-4">
              Click below to bypass the biometric scan and open the voting ballot immediately for{" "}
              <strong>{selectedVoter.name}</strong>.
            </p>
            <button
              type="button"
              onClick={() => handleBypassVerification()}
              disabled={isVerifying}
              className="w-full py-3.5 px-6 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 transition shadow-xl shadow-emerald-900/40 flex items-center justify-center gap-2 cursor-pointer active:scale-95"
            >
              <CheckCircle2 className="w-5 h-5 text-emerald-300" />
              <span>{isVerifying ? "Verifying with Oracle..." : "⚡ Bypass Fingerprint & Open Ballot"}</span>
            </button>
          </div>

          <FingerprintScanner
            onCapture={handleVerifyBiometrics}
            isScanning={isVerifying}
            label="Or touch scanner simulation to simulate verification"
          />

          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={() => setCurrentStep("select_voter")}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
            >
              &larr; Choose Different Voter
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Verification Result */}
      {currentStep === "verification_result" && verifyResult && (
        <div className="glass-panel rounded-3xl p-8 sm:p-12 border border-slate-800 max-w-xl mx-auto text-center">
          {verifyResult.allowed ? (
            <div>
              <div className="w-20 h-20 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-500/10 border border-emerald-500/40">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Biometrics Verified</h2>
              <p className="text-emerald-300 text-sm mb-6 font-medium">{verifyResult.reason}</p>

              <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 mb-8 text-left text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Voter:</span>
                  <span className="text-white font-semibold">{selectedVoter?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Audit Status:</span>
                  <span className="text-emerald-400 font-semibold font-mono">SUCCESS (Logged)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Vote Token Valid:</span>
                  <span className="text-cyan-400 font-mono">120s Single-Use JWT</span>
                </div>
              </div>

              <button
                onClick={handleProceedToBallot}
                className="w-full py-4 px-6 rounded-2xl font-bold text-base text-white bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 transition shadow-xl shadow-cyan-600/30 flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Enter Voting Booth</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div>
              <div className="w-20 h-20 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-rose-500/10 border border-rose-500/40">
                <XCircle className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Verification Denied</h2>
              <p className="text-rose-300 text-sm mb-4 font-medium">{verifyResult.reason}</p>
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 mb-6 font-mono">
                Log Code: {verifyResult.result} &bull; Recorded to Audit Trail
              </div>

              <button
                onClick={resetKioskSession}
                className="w-full py-3.5 px-6 rounded-xl font-semibold text-sm text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Return to Registry
              </button>
            </div>
          )}
        </div>
      )}

      {/* STEP 4: Ballot Screen with Candidate Cards (Large touch-friendly buttons) */}
      {currentStep === "ballot" && (
        <div className="glass-panel rounded-3xl p-6 sm:p-10 border border-slate-800">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-3 border border-indigo-800">
              <Shield className="w-3.5 h-3.5" />
              <span>Official Confidential Ballot</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">Select Your Candidate</h2>
            <p className="text-slate-400 text-sm mt-1">
              Your ballot is cryptographically isolated and anonymous. Touch a candidate card to cast your vote.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {candidates.map((cand) => {
              const isSelected = selectedCandidate?.candidate_id === cand.candidate_id;
              return (
                <div
                  key={cand.candidate_id}
                  onClick={() => setSelectedCandidate(cand)}
                  className={`p-8 rounded-3xl border-2 transition-all duration-300 flex flex-col justify-between cursor-pointer min-h-[260px] ${
                    isSelected
                      ? "bg-cyan-950/70 border-cyan-400 shadow-2xl shadow-cyan-500/25 scale-[1.02]"
                      : "bg-slate-900/80 border-slate-800 hover:border-slate-600 hover:bg-slate-850"
                  }`}
                >
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-slate-800 text-cyan-400 border border-slate-700">
                      {cand.party}
                    </span>
                    <h3 className="text-2xl font-bold text-white mt-4 tracking-tight">{cand.name}</h3>
                    <p className="text-xs text-slate-400 mt-2 leading-relaxed">{cand.description}</p>
                  </div>

                  <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-800">
                    <span className="text-xs text-slate-400">Touch to Select</span>
                    <div
                      className={`w-7 h-7 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? "border-cyan-400 bg-cyan-500 text-white" : "border-slate-600"
                      }`}
                    >
                      {isSelected && <Check className="w-4 h-4 stroke-[3]" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-center">
            <button
              disabled={!selectedCandidate}
              onClick={() => setShowConfirmModal(true)}
              className="py-4 px-12 rounded-2xl font-bold text-lg text-white bg-gradient-to-r from-cyan-500 via-teal-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 transition shadow-xl shadow-cyan-500/20 disabled:opacity-40 cursor-pointer"
            >
              Review & Submit Ballot
            </button>
          </div>
        </div>
      )}

      {/* CONFIRMATION MODAL */}
      {showConfirmModal && selectedCandidate && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel-glow rounded-3xl p-8 max-w-md w-full border border-cyan-500/40 text-center animate-in zoom-in-95 duration-200">
            <div className="w-16 h-16 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto mb-4 border border-cyan-500/40">
              <Vote className="w-8 h-8" />
            </div>

            <h3 className="text-2xl font-bold text-white mb-2">Confirm Your Choice</h3>
            <p className="text-xs text-slate-400 mb-6">
              You are about to cast your vote for:
            </p>

            <div className="bg-slate-900 rounded-2xl p-5 border border-slate-700 mb-8">
              <h4 className="text-2xl font-extrabold text-cyan-400">{selectedCandidate.name}</h4>
              <p className="text-xs text-slate-400 mt-1 font-semibold">{selectedCandidate.party}</p>
            </div>

            <p className="text-xs text-amber-300 bg-amber-950/60 p-3 rounded-xl border border-amber-800/80 mb-6">
              ⚠️ Once submitted, your ballot cannot be altered or re-cast. The connection between your identity and
              choice will be completely destroyed.
            </p>

            <div className="flex gap-4">
              <button
                type="button"
                disabled={isCastingVote}
                onClick={() => setShowConfirmModal(false)}
                className="flex-1 py-3 px-4 rounded-xl font-semibold text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              >
                Change Choice
              </button>
              <button
                type="button"
                disabled={isCastingVote}
                onClick={handleConfirmVote}
                className="flex-1 py-3 px-4 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 transition shadow-lg shadow-emerald-600/30"
              >
                {isCastingVote ? "Securing Ballot..." : "Submit My Vote"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 6: Vote Success & Auto-Reset Screen */}
      {currentStep === "vote_success" && voteSuccessData && (
        <div className="glass-panel-glow rounded-3xl p-10 sm:p-14 border border-emerald-500/50 max-w-xl mx-auto text-center animate-in zoom-in-95 duration-300">
          <div className="w-24 h-24 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-emerald-500/20 border-2 border-emerald-500/50">
            <CheckCircle2 className="w-14 h-14" />
          </div>

          <h2 className="text-3xl font-extrabold text-white tracking-tight mb-2">Vote Recorded</h2>
          <p className="text-emerald-300 font-medium text-sm mb-6">
            Your ballot has been securely deposited into the anonymous ballot box.
          </p>

          <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 text-xs font-mono text-left space-y-2 mb-8">
            <div className="flex justify-between">
              <span className="text-slate-400">Cryptographic Vote ID:</span>
              <span className="text-cyan-400 font-bold truncate max-w-[200px]">{voteSuccessData.vote_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Date Recorded:</span>
              <span className="text-white">{voteSuccessData.vote_date} (Calendar Date Only)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Voter/Choice Link:</span>
              <span className="text-emerald-400 font-bold">DESTROYED (Zero-Link)</span>
            </div>
          </div>

          {/* Auto-reset countdown */}
          <div className="flex items-center justify-center gap-2 text-xs text-slate-400 mb-6">
            <Clock className="w-4 h-4 text-cyan-400 animate-spin" />
            <span>Kiosk auto-resetting for next voter in <strong className="text-white text-sm">{countdown}s</strong>...</span>
          </div>

          <button
            onClick={resetKioskSession}
            className="w-full py-3.5 px-6 rounded-xl font-bold text-sm text-white bg-slate-800 hover:bg-slate-700 transition"
          >
            Reset Now for Next Voter
          </button>
        </div>
      )}
    </div>
  );
}
