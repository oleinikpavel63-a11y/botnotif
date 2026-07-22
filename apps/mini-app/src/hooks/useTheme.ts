import { useEffect, useState } from 'react';

import { getColorScheme, onColorSchemeChange } from '../lib/telegram';
import type { ColorScheme } from '../lib/telegram';

/**
 * Keeps a `dark` class on <html> in sync with the Telegram color scheme (or the
 * OS `prefers-color-scheme` in browser-dev fallback). Returns the current scheme.
 */
export function useTheme(): ColorScheme {
  const [scheme, setScheme] = useState<ColorScheme>(() => getColorScheme());

  useEffect(() => {
    const apply = (next: ColorScheme): void => {
      setScheme(next);
      const root = document.documentElement;
      root.classList.toggle('dark', next === 'dark');
    };
    apply(getColorScheme());
    return onColorSchemeChange(apply);
  }, []);

  return scheme;
}
