import { getTagBySlug } from "../../../utils/content-api";

export default eventHandler(async (event) => {
  const slug = getRouterParam(event, "slug");
  return slug ? getTagBySlug(slug) : null;
});
