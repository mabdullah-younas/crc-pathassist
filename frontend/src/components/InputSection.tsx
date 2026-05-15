import React, { useRef, useState } from 'react';
import { Upload, X, Image as ImageIcon, Info, AlertTriangle } from 'lucide-react';

export default function InputSection({
  caseId, setCaseId,
  patches, setPatches,
  stage, setStage,
  pT, setPt,
  pN, setPn,
  postNeo, setPostNeo,
  mmr, setMmr,
  kras, setKras,
  nras, setNras,
  braf, setBraf
}: any) {
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      if (files.length > 4) {
        setUploadError(`You selected ${files.length} patches. Gemma 4 4B performs best with up to 4 patches. Exceeding this limit causes context overload and hallucinations. Limit applied to 4 patches.`);
        setPatches(files.slice(0, 4));
      } else {
        setUploadError(null);
        setPatches(files);
      }
    }
  };

  // Optional staging: empty string means "not provided"
  const STAGES = ["", "1", "2", "3", "4"];
  const PT_STAGES = ["", "pT1", "pT2", "pT3", "pT4a", "pT4b", "ypT2", "ypT3", "pTX"];
  const PN_STAGES = ["", "N0", "N1", "N1a", "N1b", "N2", "NX"];
  
  const MMR_OPTIONS = ["NO LOSS", "LOSS MSH2/MSH6", "LOSS MLH1/PMS2", "INDETERMINATE"];
  const MUTATION_OPTIONS = ["WT", "MUTATED", "NOT TESTED"];
  const BRAF_OPTIONS = ["WT", "V600E", "NOT TESTED"];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      
      {/* Case Info */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Case Information</h3>
        
        <div className="space-y-4 flex-1">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Case ID</label>
            <input 
              type="text" 
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              placeholder="e.g. CRC-2024-0042"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">H&E Patch Images</label>
            <input 
              type="file" 
              multiple 
              accept=".png,.jpg,.jpeg" 
              onChange={handleFileChange}
              className="hidden" 
              ref={fileInputRef}
            />
            
            {patches.length > 0 ? (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-slate-600">{patches.length} files selected</span>
                  <button onClick={() => setPatches([])} className="text-slate-400 hover:text-red-500">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {patches.map((file: any, i: number) => (
                    <div key={i} className="flex-shrink-0 w-12 h-12 bg-slate-200 rounded-md flex items-center justify-center text-slate-400 text-[10px] overflow-hidden relative">
                       <ImageIcon className="w-5 h-5 absolute z-0 opacity-20" />
                       <span className="relative z-10 font-medium truncate w-full text-center px-1">{file.name.substring(0,4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-slate-300 bg-slate-50 rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-slate-100 hover:border-blue-400 transition-colors"
              >
                <div className="w-8 h-8 bg-white border border-slate-200 text-slate-500 rounded-full flex items-center justify-center mb-3 shadow-sm">
                  <Upload className="w-4 h-4" />
                </div>
                <p className="text-sm font-semibold text-slate-700">Click to upload patches</p>
                <p className="text-xs text-slate-500 mt-1">Max 4 patches (PNG, JPG)</p>
              </div>
            )}
            
            {uploadError && (
              <div className="mt-3 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-800 leading-tight">{uploadError}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Clinical Staging — OPTIONAL */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
        <div className="flex items-start justify-between mb-1">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Clinical Staging</h3>
          <span className="text-[10px] font-semibold text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full uppercase tracking-wide">Optional</span>
        </div>
        
        {/* Optional helper notice */}
        <div className="flex items-start gap-2 bg-blue-50/60 border border-blue-100 rounded-lg p-2.5 mb-4">
          <Info className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
          <p className="text-[11px] text-blue-700 leading-tight">Leave blank for morphology-only AI assessment without concordance comparison.</p>
        </div>
        
        <div className="space-y-4 flex-1">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Overall Stage
                <span className="text-slate-400 font-normal ml-1">(optional)</span>
              </label>
              <select 
                value={stage} onChange={e => setStage(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="">— Leave blank for AI-only —</option>
                {STAGES.filter(s => s !== "").map(s => <option key={s} value={s}>Stage {s}</option>)}
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                pT Stage
                <span className="text-slate-400 font-normal ml-1">(optional)</span>
              </label>
              <select 
                value={pT} onChange={e => setPt(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="">— AI-only —</option>
                {PT_STAGES.filter(s => s !== "").map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                pN Stage
                <span className="text-slate-400 font-normal ml-1">(optional)</span>
              </label>
              <select 
                value={pN} onChange={e => setPn(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="">— AI-only —</option>
                {PN_STAGES.filter(s => s !== "").map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-3 p-3 border border-slate-200 rounded-lg bg-slate-50/50 cursor-pointer hover:bg-slate-50 transition-colors">
              <input 
                type="checkbox" 
                checked={postNeo}
                onChange={e => setPostNeo(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              />
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-slate-800 tracking-tight">Post-neoadjuvant therapy</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-widest mt-0.5">Applies 'ypT' prefix</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Molecular Profiling */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:col-span-2 lg:col-span-1">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Molecular Profiling</h3>
        
        <div className="space-y-4 flex-1">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">MMR / IHC Status</label>
            <select 
              value={mmr} onChange={e => setMmr(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
            >
              {MMR_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 sm:col-span-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">KRAS</label>
              <select 
                value={kras} onChange={e => setKras(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {MUTATION_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            
            <div className="col-span-2 sm:col-span-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">NRAS</label>
              <select 
                value={nras} onChange={e => setNras(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {MUTATION_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">BRAF</label>
              <select 
                value={braf} onChange={e => setBraf(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {BRAF_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
