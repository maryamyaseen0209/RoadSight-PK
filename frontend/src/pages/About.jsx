import React from 'react';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Code2,
  Cpu,
  Database,
  Globe2,
  HelpCircle,
  Scale,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Research Methodology & Project Architecture</h1>
        <p className="text-slate-400 text-sm mt-1">
          Automated Pavement Defect Assessment for Pakistani Roads & RDD2022 Benchmark.
        </p>
      </div>

      {/* 1. Research Overview */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <Globe2 className="w-5 h-5 text-emerald-400" />
          Research Problem & Motivation
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed">
          Deep convolutional and transformer-based defect detection models trained on road condition datasets from Japan, Norway, or the United States encounter severe performance degradation when evaluated on Pakistani roadways. This phenomenon—<strong>cross-domain covariate shift</strong>—is driven by distinctive asphalt aggregate textures, intense sunlight and dynamic shadow patterns, unpaved or irregular shoulders, non-standardized lane markings, and unique pothole geometries.
        </p>
        <p className="text-slate-300 text-sm leading-relaxed">
          RoadSight-PK establishes an empirical benchmark evaluating cross-domain transferability using the Crowdsensing-based Road Damage Dataset 2022 (RDD2022) and demonstrates data-efficient transfer learning with localized Pakistani road imagery.
        </p>
      </div>

      {/* 2. Research Questions (RQ1 - RQ4) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <HelpCircle className="w-5 h-5 text-emerald-400" />
          Formal Research Questions (RQ1 – RQ4)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <span className="text-xs font-mono text-emerald-400 uppercase font-semibold">RQ1 • Cross-Domain Generalization</span>
            <p className="text-xs text-slate-300 leading-relaxed">
              How severely does detection accuracy degrade when a deep learning model trained on international multi-country datasets (RDD2022) is evaluated zero-shot on Pakistani road pavement?
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <span className="text-xs font-mono text-blue-400 uppercase font-semibold">RQ2 • Defect-Specific Domain Shift</span>
            <p className="text-xs text-slate-300 leading-relaxed">
              Which specific pavement distress categories (Longitudinal, Transverse, Alligator Cracks, or Potholes) suffer the largest domain gap drop under Pakistani driving and lighting conditions?
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <span className="text-xs font-mono text-amber-400 uppercase font-semibold">RQ3 • Transfer Learning Efficiency</span>
            <p className="text-xs text-slate-300 leading-relaxed">
              What minimum proportion of annotated local Pakistani road data (10%, 25%, 50%, or 100%) is needed to recover and exceed international baseline detection precision?
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <span className="text-xs font-mono text-purple-400 uppercase font-semibold">RQ4 • Speed vs Accuracy Pareto Frontier</span>
            <p className="text-xs text-slate-300 leading-relaxed">
              How do modern one-stage detectors (Ultralytics YOLO26n/YOLO11n) trade off detection mAP against real-time throughput (FPS) compared to two-stage architectures (Faster R-CNN ResNet-50)?
            </p>
          </div>
        </div>
      </div>

      {/* 3. Official 4-Class Taxonomy Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Official RDD2022 4-Class Taxonomy
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Class ID</th>
                <th className="px-4 py-3">RDD Code</th>
                <th className="px-4 py-3">Defect Category</th>
                <th className="px-4 py-3">Structural Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-white">0</td>
                <td className="px-4 py-3 font-mono text-blue-400 font-bold">D00</td>
                <td className="px-4 py-3 font-medium text-white">Longitudinal Crack</td>
                <td className="px-4 py-3 text-slate-400">Cracks parallel to road centerline, often along construction joints.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-white">1</td>
                <td className="px-4 py-3 font-mono text-emerald-400 font-bold">D10</td>
                <td className="px-4 py-3 font-medium text-white">Transverse Crack</td>
                <td className="px-4 py-3 text-slate-400">Cracks perpendicular to road direction from thermal contraction.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-white">2</td>
                <td className="px-4 py-3 font-mono text-amber-400 font-bold">D20</td>
                <td className="px-4 py-3 font-medium text-white">Alligator Crack</td>
                <td className="px-4 py-3 text-slate-400">Interconnected polygonal distress resembling reptile skin from structural fatigue.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-white">3</td>
                <td className="px-4 py-3 font-mono text-red-400 font-bold">D40</td>
                <td className="px-4 py-3 font-medium text-white">Pothole</td>
                <td className="px-4 py-3 text-slate-400">Bowl-shaped cavity resulting from pavement disintegration under moisture and traffic.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Architectural Comparison */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <Cpu className="w-5 h-5 text-emerald-400" />
          Model Architecture Comparison
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="font-bold text-emerald-400 text-sm block">Ultralytics YOLO26n / YOLO11n</span>
            <p className="text-slate-300">
              Single-stage dense anchor-free object detector optimized for embedded and edge inference. Utilizes CSPDarknet backbone with PANet feature aggregation.
            </p>
            <ul className="text-slate-400 space-y-1 list-disc list-inside pt-1">
              <li>Inference Latency: 8.5 ms (Tesla T4) / ~65 FPS</li>
              <li>Parameter Size: ~3.2M parameters (5.4 MB weights)</li>
              <li>Export Support: ONNX, TensorRT, CoreML</li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="font-bold text-blue-400 text-sm block">Faster R-CNN ResNet-50 FPN V2</span>
            <p className="text-slate-300">
              Two-stage detector with Region Proposal Network (RPN) and RoIAlign head. Excels in dense bounding box localization precision.
            </p>
            <ul className="text-slate-400 space-y-1 list-disc list-inside pt-1">
              <li>Inference Latency: 42.0 ms (Tesla T4) / ~15 FPS</li>
              <li>Parameter Size: ~41.5M parameters (173 MB weights)</li>
              <li>Loss Function: Smooth L1 + Cross-Entropy</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 5. Evaluation Formulas */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <Scale className="w-5 h-5 text-emerald-400" />
          Mathematical Evaluation Formulas
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="font-bold text-white block">Domain Gap Metric</span>
            <code className="text-emerald-400 font-mono block bg-slate-900 p-2 rounded">
              Domain Gap (%) = ((in_domain - cross_domain) / in_domain) * 100
            </code>
            <p className="text-slate-400">
              Quantifies percentage loss in mAP@0.5 when testing on an unseen geographic road domain.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="font-bold text-white block">Fine-Tuning Improvement Metric</span>
            <code className="text-emerald-400 font-mono block bg-slate-900 p-2 rounded">
              Gain (%) = ((fine_tuned - zero_shot) / zero_shot) * 100
            </code>
            <p className="text-slate-400">
              Measures relative accuracy recovery achieved through local transfer learning on Pakistani roads.
            </p>
          </div>
        </div>
      </div>

      {/* 6. Licensing & Disclaimer */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          Academic Citation, Licensing & Limitations
        </h2>
        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <p>
            <strong>License Disclosures:</strong> This project uses the Ultralytics framework (AGPL-3.0) and the Crowdsensing-based Road Damage Detection Challenge dataset (RDD2022, CC BY-SA 4.0).
          </p>
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
            <strong>Important Research Disclaimer:</strong> RoadSight-PK is an academic research prototype designed to evaluate cross-domain computer vision generalization. Bounding-box detection identifies visible surface distress patterns but does not measure structural sub-base depth, volumetric asphalt loss, or pavement structural integrity indices (PCI).
          </div>
        </div>
      </div>
    </div>
  );
}
