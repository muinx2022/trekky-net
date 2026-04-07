import { getPostByRouteId } from "../../../utils/content-api";

export default eventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  return id ? getPostByRouteId(id) : null;
});
