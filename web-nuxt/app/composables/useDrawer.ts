export function useDrawer() {
  const drawerOpen = useState<"left" | "right" | null>("drawer:open", () => null);

  function openDrawer(side: "left" | "right") {
    drawerOpen.value = side;
  }

  function closeDrawer() {
    drawerOpen.value = null;
  }

  return {
    drawerOpen,
    openDrawer,
    closeDrawer,
  };
}
