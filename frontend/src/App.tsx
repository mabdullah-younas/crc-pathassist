/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { FileText, Activity, Microscope, AlertTriangle, Cpu, Cloud } from 'lucide-react';
import { motion } from 'motion/react';
import InputSection from './components/InputSection';
import OutputSection from './components/OutputSection';

export default function App() {
  const [caseId, setCaseId] = useState('DEMO_001');
  const [patches, setPatches] = useState<File[]>([]);

  // Staging — all optional (empty = not provided)
  const [stage, setStage] = useState('');
  const [pT, setPt] = useState('');
  const [pN, setPn] = useState('');
  const [postNeo, setPostNeo] = useState(false);

  // Molecular
  const [mmr, setMmr] = useState('NO LOSS');
  const [kras, setKras] = useState('WT');
  const [nras, setNras] = useState('WT');
  const [braf, setBraf] = useState('NOT TESTED');

  const [activeTab, setActiveTab] = useState<'report' | 'survival' | 'research'>('report');

  const [reportData, setReportData] = useState<any>(null);
  const [survivalData, setSurvivalData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'ok' | 'down'>('unknown');

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.ok ? setBackendStatus('ok') : setBackendStatus('down'))
      .catch(() => setBackendStatus('down'));
  }, []);

  const handleGenerate = async () => {
    setIsLoading(true);

    try {
      const formData = new FormData();
      patches.forEach(f => formData.append('files', f));
      formData.append('case_id', caseId);
      formData.append('pT', pT);
      formData.append('pN', pN);
      formData.append('stage', stage);
      formData.append('kras', kras);
      formData.append('nras', nras);
      formData.append('braf', braf);
      formData.append('mmr', mmr);
      formData.append('post_neo', postNeo ? 'True' : 'False');

      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to generate report');
      }

      const data = await response.json();
      setReportData(data.report);
      setSurvivalData(data.survival);
      setActiveTab('report');
    } catch (error: any) {
      console.error(error);
      alert(`Error: ${error.message}\n\nMake sure the backend is running:\n  cd backend\n  python api.py`);
    } finally {
      setIsLoading(false);
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-blue-100">
      <header className="bg-white border-b border-slate-200 px-8 h-16 flex items-center justify-between flex-shrink-0 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold shadow-sm">
            <Microscope className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold text-lg tracking-tight text-slate-800">
              CRC-PathAssist <span className="text-blue-600">Engine</span>
            </span>
            <div className="hidden sm:flex items-center px-2.5 py-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-md shadow-sm">
              <span className="text-[11px] font-bold tracking-wider text-white uppercase">Powered by Gemma4</span>
            </div>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-2">
          {backendStatus === 'down' && (
            <span className="px-2.5 py-1 text-xs font-semibold bg-red-50 text-red-700 border border-red-200 rounded-full flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3"/>Backend Offline
            </span>
          )}
          {backendStatus === 'ok' && (
            <span className="px-2.5 py-1 text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-100 rounded-full flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"/>Backend Online
            </span>
          )}
          <span className="px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200 rounded-full">AJCC 8th Ed.</span>
          <span className="px-2.5 py-1 text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-full">Research Only</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {/* INPUT SECTION */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Case Parameters</h2>
            <p className="text-sm text-slate-500 hidden sm:block">Staging fields are optional — leave blank for morphology-only AI assessment.</p>
          </div>

          <InputSection
            caseId={caseId} setCaseId={setCaseId}
            patches={patches} setPatches={setPatches}
            stage={stage} setStage={setStage}
            pT={pT} setPt={setPt}
            pN={pN} setPn={setPn}
            postNeo={postNeo} setPostNeo={setPostNeo}
            mmr={mmr} setMmr={setMmr}
            kras={kras} setKras={setKras}
            nras={nras} setNras={setNras}
            braf={braf} setBraf={setBraf}
          />
        </section>

        {/* SINGLE ACTION BUTTON */}
        <section className="bg-white border border-slate-200 p-6 rounded-2xl shadow-lg ring-4 ring-slate-100 flex flex-col sm:flex-row gap-4 items-center justify-between overflow-hidden">
          <div className="text-sm text-slate-500 max-w-sm">
            <p className="font-semibold text-slate-700 mb-0.5">Generates two outputs simultaneously:</p>
            <p>Unified Smart Report (synoptic + concordance) <em>and</em> Survival Prediction — in parallel.</p>
          </div>
          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="w-full sm:w-auto px-10 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-md active:scale-95 flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? <Activity className="w-5 h-5 animate-pulse"/> : <FileText className="w-5 h-5"/>}
            {isLoading ? 'Analysing (Smart Report + Survival)…' : 'Generate Comprehensive Report'}
          </button>
        </section>

        {/* OUTPUT SECTION */}
        <section className="scroll-mt-24" id="results-section">
          <motion.div
            initial={{ opacity:0, y:20 }}
            animate={{ opacity:1, y:0 }}
            transition={{ duration:0.4, ease:'easeOut' }}
          >
            <OutputSection
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              reportData={reportData}
              survivalData={survivalData}
              caseId={caseId}
            />
          </motion.div>
        </section>

      </main>
    </div>
  );
}
