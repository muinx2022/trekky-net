import { getCategoriesForSitemap, getPagesForSitemap, getPostsForSitemap, getTagsForSitemap } from "../utils/content-api";

export default eventHandler(async (event) => {
  const config = useRuntimeConfig();
  const siteUrl = config.public.siteUrl;
  const [posts, categories, tags, pages] = await Promise.all([
    getPostsForSitemap(),
    getCategoriesForSitemap(),
    getTagsForSitemap(),
    getPagesForSitemap(),
  ]);

  const urls = [
    `${siteUrl}/`,
    ...posts.map((item) => `${siteUrl}/p/${item.slug}--${item.documentId}`),
    ...categories.map((item) => `${siteUrl}/c/${item.slug}`),
    ...tags.map((item) => `${siteUrl}/t/${item.slug}`),
    ...pages.map((item) => `${siteUrl}/page/${item.slug}`),
  ];

  setHeader(event, "content-type", "application/xml; charset=utf-8");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((url) => `  <url><loc>${url}</loc></url>`).join("\n")}
</urlset>`;
});
