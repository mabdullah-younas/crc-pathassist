import React from 'react';
import { motion } from 'motion/react';

function StatCard({ val, label, color = 'text-slate-900' }: any) {
  return (
    <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl text-center">
      <div className={`text-3xl font-serif mb-1 ${color}`}>{val}</div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
    </div>
  );
}

export default function ResearchTab() {
  return (
    <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.3 }} className="space-y-8">

      {/* Section 1 — Project Overview */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="bg-gradient-to-r from-blue-600 to-teal-600 px-6 py-4">
          <h2 className="text-white font-bold text-lg">Project Overview</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-slate-700 leading-relaxed">
            <strong>CRC-PathAssist</strong> is a dual-output AI pathology assistant using <strong>Gemma 4 26B-A4B</strong> on H&E patches from the <strong>SurGen SR386 dataset</strong> (427 colorectal cancer cases, open access, BioImage Archive). It delivers two parallel outputs from each case: (1) a CAP-aligned synoptic pathology report with concordance checking against user-provided staging, and (2) a 5-year survival prediction using a Logistic Regression classifier trained on Gemma 4-extracted morphological features.
          </p>
        </div>
      </section>

      {/* Section 2 — Smart Report Workflow */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">How the Smart Report Works</h2>
        </div>
        <div className="p-6">
          <div className="flex flex-wrap gap-2 items-center text-sm font-medium text-slate-700 mb-4">
            {['H&E Patches','→','Gemma 4 26B Visual Assessment','→','Morphological Findings','→','Compare vs. User Staging','→','Concordance / Discordance Flags','→','CAP Synoptic Report + PDF'].map((s, i) => (
              s === '→'
                ? <span key={i} className="text-blue-400 font-bold text-lg">›</span>
                : <span key={i} className="bg-blue-50 border border-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold">{s}</span>
            ))}
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            Gemma 4 first independently assesses all H&E patches to extract morphological features (grade, pT estimate, budding, stroma ratio, TIL, LVI, PNI). It then compares its estimates against user-provided pT/pN staging, flagging <span className="text-emerald-700 font-bold">CONCORDANT</span> or <span className="text-red-700 font-bold">DISCORDANT</span> findings. If staging fields are left blank, no comparison is made — the model reports its findings directly. Output is a complete CAP-aligned synoptic report with risk tier and exportable PDF.
          </p>
        </div>
      </section>

      {/* Section 3 — Survival Prediction Workflow */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">How Survival Prediction Works</h2>
        </div>
        <div className="p-6">
          <div className="flex flex-wrap gap-2 items-center text-sm font-medium text-slate-700 mb-4">
            {['H&E Patches','→','Gemma 4 26B Feature Extraction (TIL · Stroma · Budding · Necrosis)','→','Logistic Regression Classifier (SR386-trained)','→','5-Year Survival Prediction + Probability'].map((s, i) => (
              s === '→'
                ? <span key={i} className="text-purple-400 font-bold text-lg">›</span>
                : <span key={i} className="bg-purple-50 border border-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-semibold">{s}</span>
            ))}
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            Gemma 4 extracts 4 numeric feature scores from the H&E patches (TIL density, stroma ratio, tumour budding grade, necrosis). These feed into a pre-trained Logistic Regression classifier (validated on 57 held-out SR386 cases) to produce a Good/Poor 5-year survival prediction with probability score. No clinical staging or molecular data is used in this pipeline.
          </p>
        </div>
      </section>

      {/* Section 4 — Model Evaluation Results */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">Model Evaluation Results</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard val="57" label="Test Cases"/>
            <StatCard val="61.4%" label="Best Accuracy" color="text-emerald-600"/>
            <StatCard val="0.605" label="Best AUC" color="text-blue-600"/>
            <StatCard val="26B+LR" label="Best Pipeline" color="text-purple-600"/>
          </div>
          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="font-semibold p-3">Approach</th>
                  <th className="font-semibold p-3">Model</th>
                  <th className="font-semibold p-3 text-center">AUC</th>
                  <th className="font-semibold p-3 text-center">Accuracy</th>
                  <th className="font-semibold p-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="p-3 text-slate-700">End-to-end prediction</td>
                  <td className="p-3 text-slate-600 font-mono text-xs">Gemma 4 E4B (4B, local)</td>
                  <td className="p-3 text-center text-red-600 font-mono font-bold">0.409</td>
                  <td className="p-3 text-center text-red-600 font-mono font-bold">30.4%</td>
                  <td className="p-3 text-slate-500">Systematic bias toward Poor</td>
                </tr>
                <tr>
                  <td className="p-3 text-slate-700">End-to-end prediction</td>
                  <td className="p-3 text-slate-600 font-mono text-xs">Gemma 4 26B-A4B (API)</td>
                  <td className="p-3 text-center text-amber-600 font-mono font-bold">0.500</td>
                  <td className="p-3 text-center text-amber-600 font-mono font-bold">38.6%</td>
                  <td className="p-3 text-slate-500">Random chance baseline</td>
                </tr>
                <tr className="bg-blue-50/50">
                  <td className="p-3 font-bold text-blue-700">Gemma features + LR</td>
                  <td className="p-3 font-mono text-xs text-blue-700 font-bold">Gemma 4 26B + Logistic Regression</td>
                  <td className="p-3 text-center font-bold text-blue-700 font-mono">0.605</td>
                  <td className="p-3 text-center font-bold text-blue-700 font-mono">61.4%</td>
                  <td className="p-3 font-medium text-blue-600">✓ Best result — current system</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Section 5 — Synoptic Report Accuracy */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">Synoptic Report Accuracy</h2>
          <p className="text-xs text-slate-500 mt-1">Evaluated on 10 demo cases from SR386 dataset</p>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="font-semibold p-3">Metric</th>
                  <th className="font-semibold p-3 text-center">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[
                  ['pT stage accuracy', '8/10 demo cases'],
                  ['pN stage accuracy', '10/10 demo cases'],
                  ['MMR status accuracy', '10/10 demo cases'],
                  ['KRAS status accuracy', '10/10 demo cases'],
                  ['Overall 6-field score', '9/10 cases at 6/6'],
                ].map(([metric, score]) => (
                  <tr key={metric}>
                    <td className="p-3 text-slate-700">{metric}</td>
                    <td className="p-3 text-center font-bold text-emerald-700">{score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Section 6 — Dataset */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">Dataset</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-slate-700 leading-relaxed">
            <strong>SurGen SR386</strong> — 427 H&E WSIs, CZI format, 40× magnification. Annotations include KRAS/NRAS/BRAF mutations, MMR/IHC status, pT/pN staging, and 5-year survival (426 cases). Open access via BioImage Archive.{' '}
            <a href="https://doi.org/10.6019/S-BIAD1285" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-mono text-xs">doi:10.6019/S-BIAD1285</a>
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            <StatCard val="427" label="WSIs"/>
            <StatCard val="CZI" label="Format"/>
            <StatCard val="40×" label="Magnification"/>
            <StatCard val="426" label="Survival Cases"/>
          </div>
        </div>
      </section>

      {/* Section 7 — Key Finding Callout */}
      <section className="border-2 border-blue-200 rounded-2xl overflow-hidden shadow-sm bg-blue-50">
        <div className="px-6 py-4 border-b border-blue-200 bg-blue-600">
          <h2 className="text-lg font-bold text-white">Key Finding</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-blue-900 leading-relaxed">
            Gemma 4 cannot reliably perform end-to-end survival prediction from patch-level morphology alone (AUC 0.500). However, when used as a <strong>structured visual feature extractor</strong> feeding a logistic regression classifier, AUC improves to <strong>0.605</strong>. This establishes Gemma 4's role as a <em>morphological feature encoder</em> — the right tool for feature extraction, not direct prognostication.
          </p>
        </div>
      </section>

      {/* Section 8 — Technical Stack */}
      <section className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm bg-white">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">Technical Stack</h2>
        </div>
        <div className="p-6">
          <div className="flex flex-wrap gap-2">
            {[
              'Gemma 4 E4B via Local Ollama',
              'pylibCZIrw for CZI patch extraction',
              'SurGen SR386 dataset',
              'scikit-learn LogisticRegression',
              'React frontend',
              'Python / FastAPI backend',
              'Fully offline execution',
            ].map(t => (
              <span key={t} className="bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded-full">{t}</span>
            ))}
          </div>
        </div>
      </section>

    </motion.div>
  );
}
