import { useEffect, useState } from 'react';
import { Activity, RefreshCw, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { IndicatorCard } from './IndicatorCard';
import { InsightsSection } from './InsightsSection';
import { getDashboardData, type DashboardData } from '../../services/api';
import { useRefreshSignal } from '../../context/RefreshContext';
import { formatShortDate } from '../../utils/formatting';

interface DashboardContainerProps {
    projectId: string;
}

// Color palette for different indicators
const INDICATOR_COLORS: Record<string, string> = {
    'orientierung_sinn': '#3b82f6',      // blue
    'psychologische_sicherheit': '#10b981', // green
    'empowerment': '#8b5cf6',            // purple
    'partizipation': '#f59e0b',          // amber
    'wertschaetzung': '#ec4899',         // pink
};

export function DashboardContainer({ projectId }: DashboardContainerProps) {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const dashboardRefreshSignal = useRefreshSignal('dashboard');
    const { t } = useTranslation('dashboard');

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getDashboardData(projectId);
            setDashboardData(data);
        } catch (err) {
            console.error('Failed to load dashboard data:', err);
            setError(t('loadFailed'));
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [projectId, dashboardRefreshSignal]);

    const hasAnyData = dashboardData?.indicators.some(i => i.rating_count > 0) ?? false;

    // Transform trend data for chart - convert to percentages
    const chartData = dashboardData?.trend_data.map(point => {
        const transformed: Record<string, string | number> = {
            date: formatShortDate(point.date as string)
        };

        // Convert each indicator rating to percentage
        dashboardData.indicators.forEach(ind => {
            if (point[ind.key] !== undefined) {
                transformed[ind.name] = (point[ind.key] as number) * 10;
            }
        });

        return transformed;
    }) ?? [];

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Activity className="text-blue-600" size={24} />
                        <h1 className="text-2xl font-bold text-gray-800">{t('title')}</h1>
                    </div>
                    <button
                        onClick={loadData}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
                        {t('common:buttons.refresh')}
                    </button>
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center py-20">
                        <RefreshCw size={32} className="text-gray-400 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="text-center py-20 text-gray-500">
                        <p>{error}</p>
                        <button
                            onClick={loadData}
                            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                            {t('common:buttons.retry')}
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Top Panel: 5 Indicator Cards */}
                        <div className="bg-white rounded-2xl border border-gray-200 p-6">
                            <h2 className="text-lg font-semibold text-gray-700 mb-4">{t('indicators.title')}</h2>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                {dashboardData?.indicators.map((indicator) => (
                                    <IndicatorCard
                                        key={indicator.key}
                                        name={indicator.name}
                                        description={indicator.description}
                                        averageRating={indicator.average_rating}
                                        latestRating={indicator.latest_rating}
                                        previousRating={indicator.previous_rating}
                                        ratingCount={indicator.rating_count}
                                    />
                                ))}
                            </div>
                            {!hasAnyData && (
                                <p className="text-sm text-gray-500 mt-4 text-center">
                                    {t('indicators.emptyState')}
                                </p>
                            )}
                        </div>

                        {/* Trend Chart */}
                        <div className="bg-white rounded-2xl border border-gray-200 p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <TrendingUp size={20} className="text-gray-400" />
                                <h2 className="text-lg font-semibold text-gray-700">{t('trend.title')}</h2>
                            </div>

                            {chartData.length > 0 ? (
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 12 }}
                                                stroke="#9ca3af"
                                            />
                                            <YAxis
                                                domain={[0, 100]}
                                                ticks={[0, 25, 50, 75, 100]}
                                                tick={{ fontSize: 12 }}
                                                stroke="#9ca3af"
                                                tickFormatter={(value) => `${value}%`}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'white',
                                                    border: '1px solid #e5e7eb',
                                                    borderRadius: '8px',
                                                    fontSize: '12px'
                                                }}
                                                formatter={(value) => [`${value}%`, '']}
                                            />
                                            <Legend wrapperStyle={{ fontSize: '12px' }} />
                                            {dashboardData?.indicators.map((indicator) => (
                                                <Line
                                                    key={indicator.key}
                                                    type="monotone"
                                                    dataKey={indicator.name}
                                                    stroke={INDICATOR_COLORS[indicator.key] || '#6b7280'}
                                                    strokeWidth={2}
                                                    dot={{ r: 4 }}
                                                    activeDot={{ r: 6 }}
                                                    connectNulls
                                                />
                                            ))}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg">
                                    <div className="text-center text-gray-400">
                                        <TrendingUp size={48} className="mx-auto mb-3 opacity-50" />
                                        <p className="font-medium">{t('trend.emptyTitle')}</p>
                                        <p className="text-sm mt-1">
                                            {t('trend.emptyDescription')}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Insights Section */}
                        <InsightsSection projectId={projectId} />
                    </>
                )}
            </div>
        </div>
    );
}
