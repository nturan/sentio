import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import German translations
import commonDe from './locales/de/common.json';
import navigationDe from './locales/de/navigation.json';
import onboardingDe from './locales/de/onboarding.json';
import dashboardDe from './locales/de/dashboard.json';
import stakeholderDe from './locales/de/stakeholder.json';
import impulseDe from './locales/de/impulse.json';
import recommendationsDe from './locales/de/recommendations.json';
import settingsDe from './locales/de/settings.json';
import chatDe from './locales/de/chat.json';
import enumsDe from './locales/de/enums.json';

// Import English translations
import commonEn from './locales/en/common.json';
import navigationEn from './locales/en/navigation.json';
import onboardingEn from './locales/en/onboarding.json';
import dashboardEn from './locales/en/dashboard.json';
import stakeholderEn from './locales/en/stakeholder.json';
import impulseEn from './locales/en/impulse.json';
import recommendationsEn from './locales/en/recommendations.json';
import settingsEn from './locales/en/settings.json';
import chatEn from './locales/en/chat.json';
import enumsEn from './locales/en/enums.json';

const resources = {
    de: {
        common: commonDe,
        navigation: navigationDe,
        onboarding: onboardingDe,
        dashboard: dashboardDe,
        stakeholder: stakeholderDe,
        impulse: impulseDe,
        recommendations: recommendationsDe,
        settings: settingsDe,
        chat: chatDe,
        enums: enumsDe,
    },
    en: {
        common: commonEn,
        navigation: navigationEn,
        onboarding: onboardingEn,
        dashboard: dashboardEn,
        stakeholder: stakeholderEn,
        impulse: impulseEn,
        recommendations: recommendationsEn,
        settings: settingsEn,
        chat: chatEn,
        enums: enumsEn,
    },
};

// Get locale from environment variable, default to 'en'
const locale = import.meta.env.VITE_LOCALE || 'en';

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: locale,
        fallbackLng: 'en',
        defaultNS: 'common',
        ns: [
            'common',
            'navigation',
            'onboarding',
            'dashboard',
            'stakeholder',
            'impulse',
            'recommendations',
            'settings',
            'chat',
            'enums',
        ],
        interpolation: {
            escapeValue: false,
        },
        react: {
            useSuspense: false,
        },
    });

export default i18n;
