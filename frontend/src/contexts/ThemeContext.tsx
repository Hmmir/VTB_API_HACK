import { createContext, PropsWithChildren, useContext, useEffect, useMemo, useState } from 'react';

type ThemeMode = 'dawn' | 'nocturne';

type ThemeContextValue = {
  theme: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
};

const STORAGE_KEY = 'financehub:theme';

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider = ({ children }: PropsWithChildren) => {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') {
      return 'dawn';
    }

    try {
      const stored = window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
      if (stored === 'dawn' || stored === 'nocturne') {
        return stored;
      }
    } catch (error) {
      // ignore storage access issues
    }

    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'nocturne' : 'dawn';
  });

  useEffect(() => {
    if (typeof document === 'undefined') return;

    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme === 'nocturne' ? 'dark' : 'light';

    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // storage might be unavailable, fail silently
    }
  }, [theme]);

  const value = useMemo<ThemeContextValue>(() => ({
    theme,
    toggleTheme: () => setTheme((prev) => (prev === 'dawn' ? 'nocturne' : 'dawn')),
    setTheme: (mode: ThemeMode) => setTheme(mode),
  }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

