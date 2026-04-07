type ThemeMode = "light" | "dark" | "system";

const STORAGE_KEY = "trekky-theme";

export function useTheme() {
  const themeCookie = useCookie<ThemeMode | null>(STORAGE_KEY, {
    sameSite: "lax",
    path: "/",
    default: () => null,
  });
  const mode = useState<ThemeMode>("theme-mode", () => themeCookie.value ?? getInitialMode());
  const isDark = useState<boolean>("theme-is-dark", () => getInitialDark(mode.value));
  const initialized = useState<boolean>("theme-initialized", () => false);
  let mediaQuery: MediaQueryList | null = null;
  let mediaListener: ((event: MediaQueryListEvent) => void) | null = null;

  function getInitialMode(): ThemeMode {
    if (themeCookie.value === "light" || themeCookie.value === "dark" || themeCookie.value === "system") {
      return themeCookie.value;
    }
    if (!import.meta.client) return "system";
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") return stored;
    return "system";
  }

  function getInitialDark(nextMode: ThemeMode) {
    if (nextMode === "dark") return true;
    if (nextMode === "light") return false;
    if (import.meta.client) {
      const preset = document.documentElement.dataset.theme;
      if (preset === "dark") return true;
      if (preset === "light") return false;
    }
    return getPreferredDark();
  }

  function getPreferredDark() {
    return import.meta.client ? window.matchMedia("(prefers-color-scheme: dark)").matches : false;
  }

  function resolveDark(nextMode = mode.value) {
    return nextMode === "dark" || (nextMode === "system" && getPreferredDark());
  }

  function applyTheme(nextMode = mode.value) {
    const dark = resolveDark(nextMode);
    isDark.value = dark;
    if (!import.meta.client) return;
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.documentElement.style.colorScheme = dark ? "dark" : "light";
  }

  function persist(nextMode: ThemeMode) {
    themeCookie.value = nextMode;
    if (import.meta.client) {
      window.localStorage.setItem(STORAGE_KEY, nextMode);
    }
  }

  function setMode(nextMode: ThemeMode) {
    mode.value = nextMode;
    persist(nextMode);
    applyTheme(nextMode);
  }

  function toggleTheme() {
    setMode(isDark.value ? "light" : "dark");
  }

  function init() {
    if (!import.meta.client || initialized.value) return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") {
      mode.value = stored;
    }

    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaListener = () => {
      if (mode.value === "system") applyTheme("system");
    };
    mediaQuery.addEventListener("change", mediaListener);
    themeCookie.value = mode.value;
    applyTheme(mode.value);
    initialized.value = true;
  }

  function dispose() {
    if (mediaQuery && mediaListener) mediaQuery.removeEventListener("change", mediaListener);
    mediaListener = null;
    mediaQuery = null;
    initialized.value = false;
  }

  return {
    mode: readonly(mode),
    isDark: readonly(isDark),
    initialized: readonly(initialized),
    init,
    dispose,
    setMode,
    toggleTheme,
  };
}
