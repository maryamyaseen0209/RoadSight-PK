import React from 'react';
import { BookOpen, CheckCircle2, Code2, Database, Globe2, ShieldCheck } from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">About RoadSight-PK</h1>
        <p className="text-slate-400 text-sm mt-1">
          Pavement Defect Detection System for Pakistani Roads & RDD2022 Benchmark.
        </p>
      </div>

      {/* Mission & Problem Statement */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Globe2 className="w-5 h-5 text-emerald-400" />
          The Challenge: Cross-Country Road Domain Shift
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed">
          Deep learning models trained on road condition datasets from Japan, Norway, or the United States exhibit sharp accuracy degradation when deployed on Pakistani roads due to distinct asphalt textures, intense sunlight and shadow patterns, lane irregularity, unpaved shoulders, and unique pothole morphologies.
        </p>
        <p className="text-slate-300 text-sm leading-relaxed">
          RoadSight-PK establishes a rigorous benchmark to evaluate domain gap effects using the RDD2022 dataset and measures transfer learning efficiency on locally curated Pakistani pavement data.
        </p>
      </div>

      {/* 4-Class Taxonomy */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Standardized 4-Class Defect Taxonomy
        </h2>
        <p className="text-slate-400 text-xs">
          Strictly following the official Crowdsensing-based Road Damage Detection Challenge (RDD2022):
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              Class 0: Longitudinal Crack [D00]
            </div>
            <p className="text-xs text-slate-400">
              Cracks running parallel to the direction of vehicular traffic travel, often along construction joints.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              Class 1: Transverse Crack [D10]
            </div>
            <p className="text-xs text-slate-400">
              Cracks extending perpendicular to the road centerline caused by thermal shrinkage and subgrade movement.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              Class 2: Alligator Crack [D20]
            </div>
            <p className="text-xs text-slate-400">
              Interconnected pattern resembling reptile skin, indicating severe base layer fatigue and load failure.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
              Class 3: Pothole [D40]
            </div>
            <p className="text-xs text-slate-400">
              Bowl-shaped depressions caused by structural pavement breakdown under moisture infiltration and traffic.
            </p>
          </div>
        </div>
      </div>

      {/* Tech Stack Details */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Code2 className="w-5 h-5 text-emerald-400" />
          Technical Stack & Architectural Foundations
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-300">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <span className="font-semibold text-white block">Backend</span>
            <p className="text-slate-400">FastAPI, Python 3.13, Pydantic V2, SQLAlchemy, SQLite</p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <span className="font-semibold text-white block">Frontend</span>
            <p className="text-slate-400">React 18, Vite, Tailwind CSS, React Router v6, Recharts, Axios</p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <span className="font-semibold text-white block">Machine Learning</span>
            <p className="text-slate-400">Ultralytics YOLO26/11, PyTorch TorchVision Faster R-CNN, TorchMetrics</p>
          </div>
        </div>
      </div>
    </div>
  );
}
