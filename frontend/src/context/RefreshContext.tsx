import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

/**
 * RefreshContext - Central refresh signal broadcaster
 *
 * Components can:
 * 1. Trigger refreshes after creating/updating data
 * 2. Subscribe to refresh signals to reload their data
 */

interface RefreshSignals {
    insights: number;
    recommendations: number;
    documents: number;
    impulses: number;
    dashboard: number;
}

interface RefreshContextType {
    signals: RefreshSignals;
    triggerRefresh: (type: keyof RefreshSignals | 'all') => void;
}

const RefreshContext = createContext<RefreshContextType | null>(null);

export function RefreshProvider({ children }: { children: ReactNode }) {
    const [signals, setSignals] = useState<RefreshSignals>({
        insights: 0,
        recommendations: 0,
        documents: 0,
        impulses: 0,
        dashboard: 0,
    });

    const triggerRefresh = useCallback((type: keyof RefreshSignals | 'all') => {
        setSignals(prev => {
            if (type === 'all') {
                return {
                    insights: prev.insights + 1,
                    recommendations: prev.recommendations + 1,
                    documents: prev.documents + 1,
                    impulses: prev.impulses + 1,
                    dashboard: prev.dashboard + 1,
                };
            }

            // Also trigger dashboard refresh for data that affects it
            const affectsDashboard = ['insights', 'impulses', 'recommendations'].includes(type);

            return {
                ...prev,
                [type]: prev[type] + 1,
                ...(affectsDashboard ? { dashboard: prev.dashboard + 1 } : {}),
            };
        });
    }, []);

    return (
        <RefreshContext.Provider value={{ signals, triggerRefresh }}>
            {children}
        </RefreshContext.Provider>
    );
}

export function useRefresh() {
    const context = useContext(RefreshContext);
    if (!context) {
        throw new Error('useRefresh must be used within a RefreshProvider');
    }
    return context;
}

// Convenience hook for subscribing to specific refresh signals
export function useRefreshSignal(type: keyof RefreshSignals) {
    const { signals } = useRefresh();
    return signals[type];
}
