/**
 * VarianceBarChart - Reusable variance contribution chart component
 * 
 * Per ADR-0025: Consumes VarianceBarConfig contract from backend
 */
import type { ANOVATableRow, VarianceBarConfig } from '../types'

interface VarianceBarChartProps {
  rows: ANOVATableRow[];
  title?: string;
  config?: Partial<VarianceBarConfig>;
  highlightSignificant?: boolean;
}

interface VarianceItem {
  source: string;
  percent: number;
  significant: boolean;
}

export function VarianceBarChart({
  rows,
  title = 'Variance Contribution',
  config,
  highlightSignificant = true,
}: VarianceBarChartProps) {
  const sortByValue = config?.sort_by_value ?? true;
  const showValues = config?.show_values ?? true;
  const orientation = config?.orientation ?? 'horizontal';
  const useGradient = config?.use_gradient ?? true;

  const items: VarianceItem[] = rows
    .filter(row => row.source !== 'Total')
    .map(row => ({
      source: row.source,
      percent: row.variance_pct,
      significant: row.significant,
    }));

  const sortedItems = sortByValue
    ? [...items].sort((a, b) => b.percent - a.percent)
    : items;

  const maxPercent = Math.max(...items.map(i => i.percent), 1);

  const getBarColor = (item: VarianceItem, index: number): string => {
    if (!highlightSignificant) {
      return useGradient
        ? `hsl(${260 - index * 15}, 60%, 55%)`
        : 'rgb(139, 92, 246)';
    }
    
    if (item.significant) {
      return useGradient
        ? `hsl(${260 - index * 10}, 70%, 50%)`
        : 'rgb(139, 92, 246)';
    }
    
    return 'rgb(203, 213, 225)';
  };

  if (orientation === 'vertical') {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h4 className="text-sm font-medium text-slate-700 mb-4">{title}</h4>
        <div className="flex items-end gap-2 h-48">
          {sortedItems.map((item, index) => (
            <div key={item.source} className="flex-1 flex flex-col items-center">
              <div className="w-full flex justify-center mb-1">
                {showValues && (
                  <span className="text-xs text-slate-600">
                    {item.percent.toFixed(1)}%
                  </span>
                )}
              </div>
              <div 
                className="w-full rounded-t-sm transition-all duration-300"
                style={{
                  height: `${(item.percent / maxPercent) * 100}%`,
                  backgroundColor: getBarColor(item, index),
                  minHeight: '4px',
                }}
              />
              <span className="text-xs text-slate-600 mt-2 text-center truncate w-full">
                {item.source}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h4 className="text-sm font-medium text-slate-700 mb-3">{title}</h4>
      <div className="space-y-2">
        {sortedItems.map((item, index) => (
          <div key={item.source} className="flex items-center gap-3">
            <div className="w-24 text-sm text-slate-600 truncate" title={item.source}>
              {item.source}
            </div>
            <div className="flex-1 h-5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${item.percent}%`,
                  backgroundColor: getBarColor(item, index),
                  minWidth: item.percent > 0 ? '4px' : '0',
                }}
              />
            </div>
            {showValues && (
              <div className="w-16 text-sm text-right text-slate-600">
                {item.percent.toFixed(1)}%
              </div>
            )}
          </div>
        ))}
      </div>
      
      {highlightSignificant && items.some(i => i.significant) && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-purple-500" />
              <span>Significant (p &lt; 0.05)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-slate-300" />
              <span>Not significant</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
