export default eventHandler((event) => {
  const config = useRuntimeConfig();
  setHeader(event, "content-type", "text/plain; charset=utf-8");
  return `User-agent: *
Allow: /

Sitemap: ${config.public.siteUrl}/sitemap.xml
`;
});
