import { getPageBySlug } from "../../../utils/content-api";

export default eventHandler(async (event) => {
  const slug = getRouterParam(event, "slug");
  return slug ? getPageBySlug(slug) : null;
});
