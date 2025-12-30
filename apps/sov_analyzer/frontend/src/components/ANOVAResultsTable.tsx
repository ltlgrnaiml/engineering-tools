/**
 * ANOVAResultsTable - Reusable ANOVA results table component
 * 
 * Per ADR-0025: Consumes typed contracts from backend
 */
import { CheckCircle2 } from 'lucide-react'
import type { ANOVATableRow } from '../types'

interface ANOVAResultsTableProps {
  rows: ANOVATableRow[];
  responseColumn: string;
  rSquared: number;
  showVarianceColumn?: boolean;
  highlightSignificant?: boolean;
}

export function ANOVAResultsTable({
  rows,
  responseColumn,
  rSquared,
  showVarianceColumn = true,
  highlightSignificant = true,
}: ANOVAResultsTableProps) {
  const formatPValue = (p: number | null): string => {
    if (p === null) return '-';
    if (p < 0.001) return '<0.001';
    if (p < 0.01) return p.toFixed(3);
    return p.toFixed(4);
  };

  const formatNumber = (n: number | null, decimals = 4): string => {
    if (n === null) return '-';
    return n.toFixed(decimals);
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <h3 className="font-medium text-slate-900">
          ANOVA Table: {responseColumn}
        </h3>
        <div className="text-sm text-slate-600">
          R² = <span className="font-medium">{(rSquared * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-slate-600">Source</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">DF</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">Sum Sq</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">Mean Sq</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">F</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">P-value</th>
              {showVarianceColumn && (
                <th className="text-right px-4 py-2 font-medium text-slate-600">% Var</th>
              )}
              <th className="text-center px-4 py-2 font-medium text-slate-600">Sig</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isSignificant = row.significant && highlightSignificant;
              return (
                <tr 
                  key={row.source} 
                  className={`border-t border-slate-100 ${isSignificant ? 'bg-green-50' : ''}`}
                >
                  <td className="px-4 py-2 font-medium text-slate-900">{row.source}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{row.df}</td>
                  <td className="px-4 py-2 text-right text-slate-600">
                    {formatNumber(row.sum_squares)}
                  </td>
                  <td className="px-4 py-2 text-right text-slate-600">
                    {formatNumber(row.mean_square)}
                  </td>
                  <td className="px-4 py-2 text-right text-slate-600">
                    {formatNumber(row.f_statistic, 2)}
                  </td>
                  <td className={`px-4 py-2 text-right ${
                    row.p_value !== null && row.p_value < 0.05 
                      ? 'text-purple-600 font-medium' 
                      : 'text-slate-600'
                  }`}>
                    {formatPValue(row.p_value)}
                  </td>
                  {showVarianceColumn && (
                    <td className="px-4 py-2 text-right text-slate-600">
                      {row.variance_pct.toFixed(1)}%
                    </td>
                  )}
                  <td className="px-4 py-2 text-center">
                    {row.significant ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500 inline" />
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
