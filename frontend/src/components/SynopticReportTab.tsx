import React, { useState } from 'react';
import { Download, AlertTriangle, ChevronDown, ChevronUp, CheckCircle } from 'lucide-react';
import { motion } from 'motion/react';

function ConcordanceBadge({ value }: { value: string | null }) {
  if (!value) return null;
  if (value === 'CONCORDANT') {
    return <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100 border border-emerald-200 px-2.5 py-0.5 rounded-full"><CheckCircle className="w-3 h-3"/>CONCORDANT</span>;
  }
  if (value.startsWith('DISCORDANT')) {
    const detail = value.replace('DISCORDANT — ', '');
    return (
      <span className="inline-flex items-center gap-1 text-xs font-bold text-red-700 bg-red-100 border border-red-200 px-2.5 py-0.5 rounded-full">
        <AlertTriangle className="w-3 h-3"/>DISCORDANT
        {detail && <span className="font-normal ml-1 text-red-600">({detail})</span>}
      </span>
    );
  }
  return null;
}

function generatePdf(data: any, caseId: string) {
  const mmrLost = data.mmr_proteins_lost?.length ? data.mmr_proteins_lost.join(', ') : 'None';
  const ptComp = data.pT_comparison || '';
  const pnComp = data.pN_comparison || '';
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"/>
  <title>CRC-PathAssist Smart Report — ${caseId}</title>
  <style>
    body{font-family:Georgia,serif;color:#1e293b;background:#fff;padding:40px 48px;font-size:13px;line-height:1.6}
    h1{font-size:22px;font-weight:700;margin-bottom:2px}
    .subtitle{color:#64748b;font-size:12px;margin-bottom:24px}
    .warning{background:#fefce8;border:1px solid #fde047;border-left:4px solid #f59e0b;padding:10px 14px;border-radius:4px;margin-bottom:16px;font-size:12px;color:#92400e;font-weight:600}
    .section-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#94a3b8;margin-bottom:8px;margin-top:20px}
    table{width:100%;border-collapse:collapse;margin-bottom:8px}
    td{padding:7px 10px;border-bottom:1px solid #f1f5f9;font-size:12.5px}
    td:first-child{color:#64748b;font-weight:500;width:45%}
    td:last-child{font-weight:700;text-align:right}
    .concordant{color:#15803d;background:#f0fdf4;padding:2px 8px;border-radius:20px;font-size:11px}
    .discordant{color:#b91c1c;background:#fef2f2;padding:2px 8px;border-radius:20px;font-size:11px}
    .summary{background:#eff6ff;border-left:4px solid #3b82f6;padding:14px 16px;border-radius:0 8px 8px 0;font-size:12.5px;margin-top:20px}
    .reasoning{background:#f8fafc;border:1px solid #e2e8f0;padding:12px 16px;border-radius:6px;font-size:12px;margin-top:8px;color:#475569;font-style:italic}
    .footer{margin-top:32px;font-size:10px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:12px}
  </style></head><body>
  <h1>CRC-PathAssist Unified Smart Report</h1>
  <div class="subtitle">Case ID: ${caseId} &nbsp;·&nbsp; ${new Date().toLocaleString()} &nbsp;·&nbsp; AJCC 8th Edition / CAP Protocol</div>
  ${data.flag_for_review ? '<div class="warning">⚠ This case has been flagged for senior pathologist review</div>' : ''}
  <div class="section-title">Risk &amp; Confidence</div>
  <table>
    <tr><td>Risk Tier</td><td>${data.risk_tier} RISK</td></tr>
    <tr><td>Confidence</td><td>${data.confidence}</td></tr>
  </table>
  <div class="section-title">Tumour Characteristics</div>
  <table>
    <tr><td>Tumour Type</td><td>${data.tumour_type}</td></tr>
    <tr><td>Differentiation</td><td>${data.differentiation_grade}</td></tr>
    <tr><td>Tumour Budding</td><td>${data.tumour_budding}</td></tr>
    <tr><td>Tumour-Stroma Ratio</td><td>${data.tumour_stroma_ratio}</td></tr>
    <tr><td>TIL Density</td><td>${data.til_density}</td></tr>
    <tr><td>Necrosis</td><td>${data.necrosis ? 'Present' : 'Absent'}</td></tr>
    <tr><td>Mucinous Component</td><td>${data.mucinous_component}</td></tr>
    <tr><td>Lymphovascular Invasion</td><td>${data.lymphovascular_invasion}</td></tr>
    <tr><td>Perineural Invasion</td><td>${data.perineural_invasion}</td></tr>
  </table>
  <div class="section-title">Pathologic Staging + Concordance</div>
  <table>
    <tr><td>pT (Morphological Estimate)</td><td>${data.morphological_pT_estimate}</td></tr>
    <tr><td>pT Concordance</td><td><span class="${ptComp === 'CONCORDANT' ? 'concordant' : (ptComp.startsWith('DISCORDANT') ? 'discordant' : '')}">${ptComp || '—'}</span></td></tr>
    <tr><td>pN Note</td><td>${data.morphological_pN_note}</td></tr>
    <tr><td>pN Concordance</td><td><span class="${pnComp === 'CONCORDANT' ? 'concordant' : (pnComp.startsWith('DISCORDANT') ? 'discordant' : '')}">${pnComp || '—'}</span></td></tr>
  </table>
  <div class="section-title">Molecular Profile</div>
  <table>
    <tr><td>MMR Status</td><td>${data.mmr_status}</td></tr>
    <tr><td>MMR Proteins Lost</td><td>${mmrLost}</td></tr>
    <tr><td>KRAS</td><td>${data.kras_status} (${data.kras_codon})</td></tr>
    <tr><td>NRAS</td><td>${data.nras_status}</td></tr>
    <tr><td>BRAF</td><td>${data.braf_status}</td></tr>
  </table>
  <div class="section-title">Clinical Summary</div>
  <div class="summary">${data.clinical_summary}</div>
  <div class="section-title">Model Reasoning</div>
  <div class="reasoning">${data.morphological_reasoning}</div>
  <div class="footer">CRC-PathAssist · Research Use Only · Not for clinical diagnosis</div>
  </body></html>`;
  const win = window.open('', '_blank');
  if (!win) { alert('Pop-up blocked. Please allow pop-ups.'); return; }
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => win.print(), 400);
}

export default function SynopticReportTab({ data, caseId }: any) {
  const [reasoningOpen, setReasoningOpen] = useState(false);

  const getRiskStyles = (tier: string) => {
    switch(tier?.toLowerCase()) {
      case 'low': return 'bg-green-50 border-green-200 text-green-800 before:from-green-500';
      case 'intermediate': return 'bg-amber-50 border-amber-200 text-amber-800 before:from-amber-500';
      case 'high': return 'bg-orange-50 border-orange-200 text-orange-800 before:from-orange-500';
      case 'very high': return 'bg-red-50 border-red-200 text-red-800 before:from-red-500';
      default: return 'bg-slate-50 border-slate-200 text-slate-800 before:from-slate-500';
    }
  };

  return (
    <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.3 }} className="space-y-6">

      {/* Flag banner */}
      {data.flag_for_review && (
        <div className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-300 rounded-xl text-yellow-800">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0"/>
          <span className="text-sm font-semibold">This case has been flagged for senior pathologist review</span>
        </div>
      )}

      {/* Risk Banner */}
      <div className={`relative overflow-hidden border rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${getRiskStyles(data.risk_tier)} before:absolute before:left-0 before:top-0 before:h-full before:w-1.5 before:bg-gradient-to-b`}>
        <div className="pl-2">
          <div className="font-bold text-lg tracking-tight">{data.risk_tier?.toUpperCase()} RISK</div>
          <div className="text-sm opacity-80 mt-0.5 font-medium">AJCC 8th Edition · CAP Protocol</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-white/60 px-4 py-2 rounded-lg text-sm font-bold border border-white/40 shadow-sm backdrop-blur-sm">
            Confidence: {data.confidence}
          </div>
          <button
            onClick={() => generatePdf(data, caseId)}
            className="flex items-center gap-1.5 text-xs font-semibold bg-white/70 hover:bg-white px-3 py-2 rounded-lg border border-white/40 shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5"/>PDF
          </button>
        </div>
      </div>

      {/* Tumour Characteristics */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Tumour Characteristics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-y-1 gap-x-6 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
          <DataRow label="Type" value={data.tumour_type}/>
          <DataRow label="Grade" value={data.differentiation_grade}/>
          <DataRow label="Tumour Budding" value={data.tumour_budding}/>
          <DataRow label="Stroma Ratio" value={data.tumour_stroma_ratio}/>
          <DataRow label="TIL Density" value={data.til_density}/>
          <DataRow label="Necrosis" value={data.necrosis ? 'Present' : 'Absent'}/>
          <DataRow label="Mucinous Component" value={data.mucinous_component}/>
          <DataRow label="Lymphovascular Invasion" value={data.lymphovascular_invasion}/>
          <DataRow label="Perineural Invasion" value={data.perineural_invasion}/>
        </div>
      </div>

      {/* Staging + Concordance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Pathologic Staging</h3>
          <div className="space-y-2 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            <StagingRow label="pT Estimate" value={data.morphological_pT_estimate} badge={<ConcordanceBadge value={data.pT_comparison}/>}/>
            <StagingRow label="pN Note" value={data.morphological_pN_note} badge={<ConcordanceBadge value={data.pN_comparison}/>}/>
          </div>
        </div>
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Molecular Profile</h3>
          <div className="space-y-1 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            <div className="flex justify-between py-2 border-b border-slate-200/60"><span className="text-sm font-medium text-slate-500">MMR Status</span><span className="text-sm font-semibold text-slate-800">{data.mmr_status}</span></div>
            <div className="flex justify-between py-2 border-b border-slate-200/60"><span className="text-sm font-medium text-slate-500">Proteins Lost</span><span className="text-sm font-semibold text-slate-800">{data.mmr_proteins_lost?.length ? data.mmr_proteins_lost.join(', ') : 'None'}</span></div>
            <div className="flex justify-between py-2 border-b border-slate-200/60"><span className="text-sm font-medium text-slate-500">KRAS</span><span className="text-sm font-semibold text-slate-800">{data.kras_status} <span className="font-mono text-xs text-slate-500 bg-slate-100 px-1 rounded">{data.kras_codon}</span></span></div>
            <div className="flex justify-between py-2 border-b border-slate-200/60"><span className="text-sm font-medium text-slate-500">NRAS</span><span className="text-sm font-semibold text-slate-800">{data.nras_status}</span></div>
            <div className="flex justify-between py-2"><span className="text-sm font-medium text-slate-500">BRAF</span><span className="text-sm font-semibold text-slate-800">{data.braf_status}</span></div>
          </div>
        </div>
      </div>

      {/* Clinical Summary */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Clinical Summary</h3>
        <div className="bg-blue-50/50 border-l-4 border-blue-500 p-4 rounded-r-xl text-sm leading-relaxed text-slate-700 font-medium">
          {data.clinical_summary}
        </div>
      </div>

      {/* Model Reasoning — collapsible */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setReasoningOpen(o => !o)}
          className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
        >
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Model Reasoning</span>
          {reasoningOpen ? <ChevronUp className="w-4 h-4 text-slate-400"/> : <ChevronDown className="w-4 h-4 text-slate-400"/>}
        </button>
        {reasoningOpen && (
          <div className="px-4 py-3 text-sm text-slate-600 leading-relaxed italic bg-white border-t border-slate-100">
            {data.morphological_reasoning}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function DataRow({ label, value }: any) {
  return (
    <div className="flex flex-col py-2 border-b border-slate-100 last:border-0">
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function StagingRow({ label, value, badge }: any) {
  return (
    <div className="flex flex-col gap-1 py-2 border-b border-slate-100 last:border-0">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        {badge}
      </div>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}
