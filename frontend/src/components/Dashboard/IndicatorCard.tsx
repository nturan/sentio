import { Info } from 'lucide-react';

interface IndicatorCardProps {
    name: string;
    description: string;
    averageRating: number | null;
    latestRating: number | null;
    ratingCount: number;
}

export function IndicatorCard({ name, description, averageRating, latestRating, ratingCount }: IndicatorCardProps) {
    const hasData = ratingCount > 0 && averageRating !== null;

    // Convert rating (1-10) to percentage (10-100%)
    const displayPercent = hasData ? Math.round(averageRating * 10) : null;

    // Get color based on percentage
    const getColor = (percent: number | null) => {
        if (percent === null) return { bg: 'bg-gray-100', text: 'text-gray-400', border: 'border-gray-200' };
        if (percent >= 70) return { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200' };
        if (percent >= 50) return { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' };
        return { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' };
    };

    const colors = getColor(displayPercent);

    return (
        <div className={`rounded-xl border p-4 transition-all ${hasData ? colors.border : 'border-gray-200'} ${hasData ? colors.bg : 'bg-gray-50'}`}>
            <div className="flex items-start justify-between mb-2">
                <h3 className={`text-sm font-semibold truncate ${hasData ? 'text-gray-800' : 'text-gray-400'}`}>
                    {name}
                </h3>
                <div className="group relative">
                    <Info size={14} className={hasData ? 'text-gray-400' : 'text-gray-300'} />
                    <div className="absolute right-0 top-6 w-64 p-3 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                        <p className="text-xs text-gray-600">{description}</p>
                    </div>
                </div>
            </div>

            <div className="text-center py-2">
                {hasData ? (
                    <>
                        <span className={`text-3xl font-bold ${colors.text}`}>
                            {displayPercent}%
                        </span>
                        <p className="text-xs text-gray-500 mt-1">
                            {ratingCount} Bewertung{ratingCount !== 1 ? 'en' : ''}
                        </p>
                    </>
                ) : (
                    <>
                        <span className="text-2xl font-bold text-gray-300">--</span>
                        <p className="text-xs text-gray-400 mt-1">
                            Keine Daten
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}
