import { getSidebarData } from "../../utils/content-api";

export default eventHandler(async () => {
  return getSidebarData();
});
