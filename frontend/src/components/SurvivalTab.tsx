import React from 'react';
import { motion } from 'motion/react';
import { TrendingUp, TrendingDown, Activity, Layers, Users, Zap } from 'lucide-react';

function FeatureCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col items-center text-center gap-2">
      <div className={`p-2 rounded-full ${color}`}><Icon className="w-5 h-5"/></div>
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</span>
      <span className="text-sm font-bold text-slate-800">{value}</span>
    </div>
  );
}

export default function SurvivalTab({ data }: any) {
  const isGood = data.survival_prediction?.includes('Good');
  const pct = Math.round((data.probability ?? 0) * 100);

  const { til_density, stromal_ratio, tumour_budding, necrosis } = data.features_extracted || {};

  return (
    <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.3 }} className="space-y-6">

      {/* Prediction Banner */}
      <div className={`relative overflow-hidden rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border ${isGood ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${isGood ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
            {isGood ? <TrendingUp className="w-8 h-8"/> : <TrendingDown className="w-8 h-8"/>}
          </div>
          <div>
            <div className={`text-2xl font-bold tracking-tight ${isGood ? 'text-emerald-800' : 'text-red-800'}`}>
              {isGood ? 'Good Prognosis' : 'Poor Prognosis'}
            </div>
            <div className={`text-sm mt-0.5 ${isGood ? 'text-emerald-700' : 'text-red-700'}`}>
              {data.survival_prediction}
            </div>
          </div>
        </div>
        <div className={`text-5xl font-bold font-mono ${isGood ? 'text-emerald-700' : 'text-red-700'}`}>
          {pct}%
        </div>
      </div>

      {/* Probability Bar */}
      <div>
        <div className="flex justify-between text-xs font-semibold text-slate-500 mb-2">
          <span>Probability of Good Outcome</span>
          <span>{pct}%</span>
        </div>
        <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className={`h-full rounded-full ${pct >= 50 ? 'bg-emerald-500' : 'bg-red-500'}`}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 mt-1">
          <span>Poor (&lt;5yr)</span><span>Good (&gt;5yr)</span>
        </div>
      </div>

      {/* Feature Cards 2x2 */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Extracted Morphological Features</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <FeatureCard icon={Users} label="TIL Density" value={til_density} color="bg-blue-100 text-blue-600"/>
          <FeatureCard icon={Layers} label="Stromal Ratio" value={stromal_ratio} color="bg-purple-100 text-purple-600"/>
          <FeatureCard icon={Activity} label="Tumour Budding" value={tumour_budding} color="bg-amber-100 text-amber-600"/>
          <FeatureCard icon={Zap} label="Necrosis" value={necrosis ? 'Present' : 'Absent'} color={necrosis ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}/>
        </div>
      </div>

      {/* Model Stats */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl px-5 py-4 flex flex-wrap gap-4 items-center justify-between">
        <span className="text-sm font-bold text-slate-700">
          Model Accuracy: <span className="text-blue-700">{data.model_accuracy}</span>
          <span className="mx-2 text-slate-300">|</span>
          AUC: <span className="text-blue-700">{data.model_auc}</span>
          <span className="text-slate-400 font-normal text-xs ml-2">(57 validation cases)</span>
        </span>
      </div>

      {/* Feature Reasoning */}
      {data.feature_reasoning && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Feature Reasoning</h3>
          <div className="bg-blue-50/50 border-l-4 border-blue-400 p-4 rounded-r-xl text-sm leading-relaxed text-slate-700 italic">
            {data.feature_reasoning}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-800 leading-relaxed">
        <span className="font-bold block mb-1">RESEARCH USE ONLY</span>
        {data.model_note} This prediction is based on morphological features only, without clinical staging. Validated on SR386 surgical resection cohort. <strong>Not for clinical use.</strong>
      </div>

    </motion.div>
  );
}
