import { getPostsWithPagination } from "../utils/content-api";

export default eventHandler(async (event) => {
  const query = getQuery(event);
  const page = Number(query.page ?? 1);
  const pageSize = Number(query.pageSize ?? 10);
  return getPostsWithPagination(
    Number.isFinite(page) ? page : 1,
    Number.isFinite(pageSize) ? pageSize : 10,
    typeof query.category === "string" ? query.category : undefined,
    typeof query.tag === "string" ? query.tag : undefined,
    typeof query.author === "string" ? query.author : undefined,
  );
});
