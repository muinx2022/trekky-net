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
    { loc: `${siteUrl}/` },
    ...posts.map((item) => ({
      loc: `${siteUrl}/p/${item.slug}--${item.documentId}`,
      lastmod: item.updatedAt || undefined,
    })),
    ...categories.map((item) => ({
      loc: `${siteUrl}/c/${item.slug}`,
      lastmod: item.updatedAt || undefined,
    })),
    ...tags.map((item) => ({
      loc: `${siteUrl}/t/${item.slug}`,
      lastmod: item.updatedAt || undefined,
    })),
    ...pages.map((item) => ({
      loc: `${siteUrl}/page/${item.slug}`,
      lastmod: item.updatedAt || undefined,
    })),
  ];

  setHeader(event, "content-type", "application/xml; charset=utf-8");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((url) => `  <url><loc>${url.loc}</loc>${url.lastmod ? `<lastmod>${new Date(url.lastmod).toISOString()}</lastmod>` : ""}</url>`).join("\n")}
</urlset>`;
});
