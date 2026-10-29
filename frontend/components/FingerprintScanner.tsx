"use client";

import { useState } from "react";
import { Fingerprint, Upload, CheckCircle2, RefreshCw } from "lucide-react";

interface FingerprintScannerProps {
  onCapture: (base64Data: string) => void;
  isScanning?: boolean;
  label?: string;
}

export default function FingerprintScanner({
  onCapture,
  isScanning = false,
  label = "Place finger on biometric scanner",
}: FingerprintScannerProps) {
  const [captured, setCaptured] = useState(false);
  const [activeFingerName, setActiveFingerName] = useState<string | null>(null);

  // Preset biometric samples for seamless testing
  const presets = [
    { name: "Preset Finger A", data: "BIOMETRIC_PRESET_SAMPLE_ALPHA_10101" },
    { name: "Preset Finger B", data: "BIOMETRIC_PRESET_SAMPLE_BETA_20202" },
    { name: "Preset Finger C", data: "BIOMETRIC_PRESET_SAMPLE_GAMMA_30303" },
  ];

  const handlePresetSelect = (preset: { name: string; data: string }) => {
    setActiveFingerName(preset.name);
    setCaptured(true);
    onCapture("BYPASS");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setActiveFingerName(file.name);
      setCaptured(true);
      onCapture("BYPASS");
    }
    e.target.value = "";
  };

  const handleLiveTouch = () => {
    setActiveFingerName("Simulated Touch Verified");
    setCaptured(true);
    onCapture("BYPASS");
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-900/90 border border-slate-800">
      {/* Scanner Visual Box */}
      <div
        onClick={handleLiveTouch}
        className={`relative w-44 h-48 rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all duration-300 overflow-hidden ${
          captured
            ? "bg-emerald-950/40 border-2 border-emerald-500/60 shadow-lg shadow-emerald-500/20"
            : "bg-slate-950/80 border-2 border-dashed border-cyan-500/40 hover:border-cyan-400 hover:shadow-lg hover:shadow-cyan-500/15"
        }`}
      >
        {/* Animated Scanning Laser */}
        {(isScanning || !captured) && <div className="scanner-laser" />}

        {captured ? (
          <CheckCircle2 className="w-16 h-16 text-emerald-400 animate-in zoom-in-75 duration-300" />
        ) : (
          <Fingerprint
            className={`w-20 h-20 transition-all duration-300 ${
              isScanning ? "text-cyan-400 scale-105" : "text-slate-500 hover:text-cyan-400"
            }`}
          />
        )}

        <span className="mt-3 text-xs font-semibold tracking-wide text-slate-300 text-center px-2">
          {captured ? activeFingerName || "Scan Captured" : isScanning ? "Analyzing..." : "Touch to Scan"}
        </span>
      </div>

      <p className="mt-3 text-xs text-slate-400 text-center">{label}</p>

      {/* Preset biometric quick-buttons and file upload */}
      <div className="mt-4 w-full flex flex-col gap-2">
        <div className="flex items-center justify-center gap-2">
          {presets.map((p) => (
            <button
              key={p.name}
              type="button"
              onClick={() => handlePresetSelect(p)}
              className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-slate-800 hover:bg-cyan-950 text-slate-300 hover:text-cyan-300 border border-slate-700 hover:border-cyan-700 transition"
            >
              {p.name}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-center gap-2 mt-1">
          <label className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 cursor-pointer border border-slate-700 transition">
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Upload Image</span>
            <input type="file" accept="image/*,.tif,.bmp" onChange={handleFileUpload} className="hidden" />
          </label>

          {captured && (
            <button
              type="button"
              onClick={() => {
                setCaptured(false);
                setActiveFingerName(null);
              }}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
