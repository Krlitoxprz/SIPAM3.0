import { useState } from "react";
import {
  BrainCircuit, ChartBar, AlertCircle, CheckCircle2,
  XCircle, Loader2, Info,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import api from "../../services/api";

interface PredictRequest {
  promedio: number;
  porcentaje_creditos: number;
  nota_asignatura: number;
  nota_entrevista: number;
  tipo_monitoria: string;
  semestre_asignatura: number;
  creditos_asignatura: number;
  num_postulantes: number;
  num_monitores_requeridos: number;
}

interface ShapFeature {
  feature: string;
  shap_value: number;
}

interface Explanation {
  base_value: number;
  top_features: ShapFeature[];
  model_used: string;
}

interface PredictResponse {
  selected_probability: number;
  prediction: "selected" | "not_selected";
  confidence: "high" | "medium";
  model_used: string;
  puntaje_estimado: number;
  rank_estimado: number;
  selection_ratio: number;
  explanation?: Explanation;
}

interface ModelMetrics {
  test_metrics: Record<string, {
    accuracy: number; f1: number; roc_auc: number; precision: number; recall: number;
  }>;
  best_model: string;
}

const TIPO_OPTIONS = [
  "academica_cursos", "laboratorios", "nee", "investigacion",
  "tic", "permanencia_graduacion", "deportiva", "cultural",
  "biblioteca", "acreditacion", "regimenes_especiales",
  "academica", "administrativa",
];

const MODEL_COLORS: Record<string, string> = {
  RandomForest: "#8D191D",
  XGBoost: "#4E6470",
  NeuralNetwork: "#D8CEA3",
  Stacking: "#2563eb",
};

export default function PredictorMonitor() {
  const [form, setForm] = useState<PredictRequest>({
    promedio: 3.8,
    porcentaje_creditos: 50,
    nota_asignatura: 4.0,
    nota_entrevista: 3.5,
    tipo_monitoria: "academica_cursos",
    semestre_asignatura: 4,
    creditos_asignatura: 3,
    num_postulantes: 6,
    num_monitores_requeridos: 1,
  });

  const [result, setResult] = useState<PredictResponse | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMetrics, setShowMetrics] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "number" ? (parseFloat(value) || 0) : value,
    }));
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post<PredictResponse>("/ia/predecir", form);
      setResult(res.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || "Error connecting to AI service."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!result) return;
    setLoadingExplain(true);
    setError(null);
    try {
      const res = await api.post<PredictResponse>("/ia/explicar", form);
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Error fetching explanation.");
    } finally {
      setLoadingExplain(false);
    }
  };

  const handleLoadMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const res = await api.get<ModelMetrics>("/ia/metricas");
      setMetrics(res.data);
      setShowMetrics(true);
    } catch {
      setError("Could not load model metrics.");
    } finally {
      setLoadingMetrics(false);
    }
  };

  const probPercent = result ? Math.round(result.selected_probability * 100) : 0;
  const isSelected = result?.prediction === "selected";

  const metricsChartData = metrics
    ? Object.entries(metrics.test_metrics).map(([name, m]) => ({
        name,
        accuracy: Math.round(m.accuracy * 100),
        f1: Math.round(m.f1 * 100),
        auc: Math.round(m.roc_auc * 100),
      }))
    : [];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-[#8D191D]/10 rounded-lg">
          <BrainCircuit className="w-6 h-6 text-[#8D191D]" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Monitor Selection Predictor
          </h2>
          <p className="text-sm text-gray-500">
            AI-powered prediction using Random Forest, XGBoost &amp; Neural Network
          </p>
        </div>
        <button
          onClick={handleLoadMetrics}
          disabled={loadingMetrics}
          className="ml-auto flex items-center gap-2 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors mr-2"
        >
          {loadingMetrics ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ChartBar className="w-4 h-4 text-[#4E6470]" />
          )}
          Model Metrics
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input form */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <h3 className="font-semibold text-gray-800 text-sm uppercase tracking-wide">
            Student &amp; Vacancy Data
          </h3>

          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">GPA (promedio)</span>
              <input
                type="number" name="promedio" min={0} max={5} step={0.1}
                value={form.promedio}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Credits % completed</span>
              <input
                type="number" name="porcentaje_creditos" min={0} max={100} step={1}
                value={form.porcentaje_creditos}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Subject grade</span>
              <input
                type="number" name="nota_asignatura" min={0} max={5} step={0.1}
                value={form.nota_asignatura}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Interview score</span>
              <input
                type="number" name="nota_entrevista" min={0} max={5} step={0.1}
                value={form.nota_entrevista}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1 col-span-2">
              <span className="text-xs text-gray-500">Tutoring type</span>
              <select
                name="tipo_monitoria" value={form.tipo_monitoria}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              >
                {TIPO_OPTIONS.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Subject semester</span>
              <input
                type="number" name="semestre_asignatura" min={1} max={12} step={1}
                value={form.semestre_asignatura}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Subject credits</span>
              <input
                type="number" name="creditos_asignatura" min={1} max={10} step={1}
                value={form.creditos_asignatura}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Total applicants</span>
              <input
                type="number" name="num_postulantes" min={1} max={100} step={1}
                value={form.num_postulantes}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Monitors needed</span>
              <input
                type="number" name="num_monitores_requeridos" min={1} max={10} step={1}
                value={form.num_monitores_requeridos}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#8D191D]/30"
              />
            </label>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[#8D191D] hover:bg-[#6B1215] text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-60"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Predicting...</>
            ) : (
              <><BrainCircuit className="w-4 h-4" /> Predict Selection</>
            )}
          </button>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}
        </div>

        {/* Result panel */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col gap-4">
          <h3 className="font-semibold text-gray-800 text-sm uppercase tracking-wide">
            Prediction Result
          </h3>

          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-2 py-8">
              <Info className="w-10 h-10" />
              <span className="text-sm">Fill in the form and click Predict</span>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Verdict */}
              <div className={`flex items-center gap-3 p-4 rounded-xl border-2 ${
                isSelected
                  ? "bg-green-50 border-green-300"
                  : "bg-red-50 border-red-200"
              }`}>
                {isSelected
                  ? <CheckCircle2 className="w-8 h-8 text-green-600 shrink-0" />
                  : <XCircle className="w-8 h-8 text-red-500 shrink-0" />}
                <div>
                  <p className={`font-bold text-lg ${isSelected ? "text-green-700" : "text-red-600"}`}>
                    {isSelected ? "Likely SELECTED" : "Likely NOT selected"}
                  </p>
                  <p className="text-xs text-gray-500">
                    Confidence: <strong>{result.confidence}</strong> · Model: {result.model_used}
                  </p>
                </div>
              </div>

              {/* Probability bar */}
              <div>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Selection probability</span>
                  <span className="font-bold text-gray-800">{probPercent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="h-3 rounded-full transition-all duration-700"
                    style={{
                      width: `${probPercent}%`,
                      backgroundColor: isSelected ? "#16a34a" : "#dc2626",
                    }}
                  />
                </div>
              </div>

              {/* Detail cards */}
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "Est. Score", value: result.puntaje_estimado.toFixed(2) },
                  { label: "Est. Rank", value: `#${result.rank_estimado}` },
                  { label: "Selection ratio", value: `${Math.round(result.selection_ratio * 100)}%` },
                ].map((item) => (
                  <div key={item.label} className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-500">{item.label}</p>
                    <p className="font-bold text-gray-800">{item.value}</p>
                  </div>
                ))}
              </div>

              <p className="text-xs text-gray-400 text-center">
                Formula: score = nota×0.30 + GPA×0.30 + interview×0.40
              </p>
              <button
                onClick={handleExplain}
                disabled={loadingExplain}
                className="w-full flex items-center justify-center gap-2 text-sm border border-usco-vinotinto text-usco-vinotinto hover:bg-usco-vinotinto/5 font-medium py-2 rounded-lg transition-colors disabled:opacity-60"
              >
                {loadingExplain
                  ? <><Loader2 className="w-3 h-3 animate-spin" /> Explaining...</>
                  : <><Info className="w-3 h-3" /> Explain this prediction (SHAP)</>}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* SHAP explanation panel */}
      {result?.explanation && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 text-sm uppercase tracking-wide">
              Why this prediction? (SHAP values)
            </h3>
            <span className="text-xs text-gray-400">
              Base value: {result.explanation.base_value} · Model: {result.explanation.model_used}
            </span>
          </div>
          <div className="space-y-1.5">
            {result.explanation.top_features.map((f) => {
              const isPos = f.shap_value > 0;
              const maxAbs = Math.max(...result.explanation!.top_features.map((x) => Math.abs(x.shap_value)));
              const pct = Math.round((Math.abs(f.shap_value) / maxAbs) * 100);
              return (
                <div key={f.feature} className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-40 truncate" title={f.feature}>
                    {f.feature}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                    <div
                      className="h-2.5 rounded-full transition-all"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: isPos ? "#16a34a" : "#dc2626",
                      }}
                    />
                  </div>
                  <span className={`text-xs font-mono font-bold w-14 text-right ${
                    isPos ? "text-green-600" : "text-red-500"
                  }`}>
                    {isPos ? "+" : ""}{f.shap_value.toFixed(4)}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-400">
            <span className="inline-block w-3 h-2.5 bg-green-500 rounded mr-1" />
            pushes toward selected &nbsp;
            <span className="inline-block w-3 h-2.5 bg-red-500 rounded mr-1 ml-2" />
            pushes toward not selected
          </p>
        </div>
      )}

      {showMetrics && metrics && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 text-sm uppercase tracking-wide">
              Model Comparison (Test Set)
            </h3>
            <span className="text-xs bg-[#8D191D]/10 text-[#8D191D] px-2 py-0.5 rounded-full font-medium">
              Best: {metrics.best_model}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={metricsChartData} barCategoryGap="30%">
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => (typeof v === "number" ? `${v}%` : v)} />
              <Bar dataKey="accuracy" name="Accuracy" radius={[3, 3, 0, 0]}>
                {metricsChartData.map((entry) => (
                  <Cell key={entry.name} fill={MODEL_COLORS[entry.name] ?? "#8D191D"} />
                ))}
              </Bar>
              <Bar dataKey="f1" name="F1" fill="#D8CEA3" radius={[3, 3, 0, 0]} />
              <Bar dataKey="auc" name="AUC" fill="#4E6470" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
