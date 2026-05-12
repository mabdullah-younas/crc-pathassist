import React from 'react';
import { FileText, TrendingUp, BarChart2, Activity, CheckCircle } from 'lucide-react';
import { motion } from 'motion/react';
import SynopticReportTab from './SynopticReportTab';
import SurvivalTab from './SurvivalTab';
import ResearchTab from './ResearchTab';

function EmptyState({ icon, title, desc }: any) {
  return (
    <motion.div
      initial={{ opacity:0, scale:0.95 }}
      animate={{ opacity:1, scale:1 }}
      transition={{ duration:0.3 }}
      className="h-full min-h-[300px] flex flex-col items-center justify-center text-center px-4"
    >
      <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-4 shadow-sm border border-slate-100">
        {icon}
      </div>
      <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm">{desc}</p>
    </motion.div>
  );
}

type Tab = 'report' | 'survival' | 'research';

export default function OutputSection({ activeTab, setActiveTab, reportData, survivalData, caseId }: any) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'report',   label: 'Synoptic Report',    icon: <FileText className="w-4 h-4"/> },
    { id: 'survival', label: 'Survival Prediction', icon: <TrendingUp className="w-4 h-4"/> },
    { id: 'research', label: 'Research Findings',   icon: <BarChart2 className="w-4 h-4"/> },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-[420px]">

      {/* Tab nav */}
      <div className="flex items-center border-b border-slate-200 px-6 sm:px-8 mt-2 gap-6">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`pb-4 px-1 text-sm transition-colors border-b-2 flex items-center gap-1.5 ${
              activeTab === t.id
                ? 'font-semibold border-blue-600 text-blue-600'
                : 'font-medium text-slate-500 hover:text-slate-800 border-transparent'
            }`}
          >
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      <div className="p-6 md:p-8">
        {activeTab === 'report' && (
          reportData
            ? <SynopticReportTab data={reportData} caseId={caseId}/>
            : <EmptyState icon={<FileText className="w-10 h-10"/>} title="Synoptic Report Ready" desc="Enter case parameters above and click 'Generate Comprehensive Report' to produce a CAP-aligned synoptic report with concordance checking."/>
        )}

        {activeTab === 'survival' && (
          survivalData
            ? <SurvivalTab data={survivalData}/>
            : <EmptyState icon={<Activity className="w-10 h-10"/>} title="Survival Prediction" desc="Click 'Generate Comprehensive Report' — survival prediction runs automatically in parallel and results will appear here."/>
        )}

        {activeTab === 'research' && <ResearchTab/>}
      </div>
    </div>
  );
}
