import { getCommentsForTarget, getPostByRouteId } from "../../../utils/content-api";

export default eventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  if (!id) return [];
  const post = await getPostByRouteId(id);
  if (!post) return [];
  return getCommentsForTarget("post", post.documentId);
});
