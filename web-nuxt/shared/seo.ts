import sanitizeHtml from "sanitize-html";

export const SITE_NAME = "Trekky";
export const SITE_TITLE = `${SITE_NAME} - Chia sẻ đam mê, trải nghiệm và góc nhìn riêng`;
export const SITE_DESCRIPTION =
  "Trekky.net là nơi chia sẻ đam mê, trải nghiệm và góc nhìn riêng, kết nối những người sống hết mình và muốn lan tỏa điều tích cực.";
export const SITE_KEYWORDS = [
  "Trekky",
  "mạng xã hội chia sẻ",
  "cộng đồng",
  "bài viết",
  "trải nghiệm",
  "đam mê",
  "góc nhìn riêng",
  "kể chuyện thật",
  "du lịch",
  "khám phá",
];
export const TWITTER_HANDLE = "@trekkynet";
export const DEFAULT_OG_IMAGE = "/opengraph-image";

export type JsonLd = Record<string, unknown>;

export function absoluteUrl(path: string, siteUrl: string) {
  return new URL(path, siteUrl).toString();
}

export function normalizeSiteUrl(siteUrl: string) {
  return siteUrl.endsWith("/") ? siteUrl.slice(0, -1) : siteUrl;
}

export function buildCanonicalUrl(path: string, siteUrl: string) {
  const normalizedSiteUrl = normalizeSiteUrl(siteUrl);
  if (!path || path === "/") return `${normalizedSiteUrl}/`;
  return absoluteUrl(path.startsWith("/") ? path : `/${path}`, normalizedSiteUrl);
}

export function withSiteTitle(title?: string | null) {
  if (!title) return SITE_NAME;
  if (title === SITE_TITLE || title.includes(SITE_NAME)) return title;
  return `${title} | ${SITE_NAME}`;
}

export function toAbsoluteMediaUrl(url?: string | null, apiUrl?: string): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!apiUrl) return url;
  return `${apiUrl}${url}`;
}

export function normalizeMediaUrlsInHtml(html: string, apiUrl: string): string {
  if (!html) return html;

  return html.replace(/\b(src|poster)=["']([^"']+)["']/gi, (_match, attr: string, value: string) => {
    const absolute = toAbsoluteMediaUrl(value, apiUrl) ?? value;
    return `${attr}="${absolute}"`;
  });
}

const SANITIZE_OPTIONS: sanitizeHtml.IOptions = {
  allowedTags: [
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "iframe",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "source",
    "span",
    "strong",
    "sub",
    "sup",
    "u",
    "ul",
    "video",
  ],
  allowedAttributes: {
    a: ["href", "name", "target", "rel"],
    iframe: ["allow", "allowfullscreen", "frameborder", "height", "referrerpolicy", "src", "title", "width"],
    img: ["alt", "height", "src", "title", "width"],
    source: ["src", "type"],
    video: ["controls", "height", "playsinline", "poster", "preload", "src", "width"],
    "*": ["class"],
  },
  allowedSchemes: ["http", "https", "mailto", "tel"],
  allowedSchemesByTag: {
    img: ["http", "https", "data"],
  },
  allowedIframeHostnames: ["www.youtube.com", "youtube.com", "www.youtube-nocookie.com", "youtube-nocookie.com"],
  allowedIframeDomains: ["youtube.com", "youtube-nocookie.com"],
  parser: {
    lowerCaseTags: true,
  },
};

const COMMENT_SANITIZE_OPTIONS: sanitizeHtml.IOptions = {
  allowedTags: ["a", "b", "blockquote", "br", "code", "em", "h2", "h3", "i", "li", "ol", "p", "pre", "s", "span", "strong", "sub", "sup", "u", "ul"],
  allowedAttributes: {
    a: ["href", "name", "target", "rel"],
    "*": ["class"],
  },
  allowedSchemes: ["http", "https", "mailto", "tel"],
  transformTags: {
    a: sanitizeHtml.simpleTransform("a", {
      target: "_blank",
      rel: "nofollow ugc noopener noreferrer",
    }),
  },
  parser: {
    lowerCaseTags: true,
  },
};

export function sanitizeRichHtml(html: string, apiUrl: string): string {
  if (!html) return html;
  return normalizeMediaUrlsInHtml(sanitizeHtml(html, SANITIZE_OPTIONS), apiUrl);
}

export function sanitizeCommentHtml(html: string): string {
  if (!html) return html;
  return sanitizeHtml(html, COMMENT_SANITIZE_OPTIONS);
}

export function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

export function truncate(text: string, max = 160): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}...`;
}

export function extractFirstImageFromHtml(html: string, apiUrl: string): string | undefined {
  const match = html.match(/<img[^>]+src=["']([^"']+)["']/i);
  if (!match) return undefined;
  const src = match[1];
  return src.startsWith("http") ? src : `${apiUrl}${src}`;
}

export type HtmlImage = {
  src: string;
  alt?: string;
};

function decodeHtmlAttribute(value: string): string {
  return value
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function extractHtmlAttribute(tag: string, attribute: string): string | undefined {
  const pattern = new RegExp(`\\b${attribute}\\s*=\\s*["']([^"']*)["']`, "i");
  const match = tag.match(pattern);
  return match?.[1] ? decodeHtmlAttribute(match[1]) : undefined;
}

export function extractImagesFromHtml(html: string, apiUrl: string): HtmlImage[] {
  if (!html) return [];

  const images: HtmlImage[] = [];
  const seen = new Set<string>();

  for (const match of html.matchAll(/<img\b[^>]*>/gi)) {
    const tag = match[0];
    const rawSrc = extractHtmlAttribute(tag, "src");
    if (!rawSrc) continue;
    const src = toAbsoluteMediaUrl(rawSrc, apiUrl) ?? rawSrc;
    if (seen.has(src)) continue;
    seen.add(src);
    images.push({
      src,
      alt: extractHtmlAttribute(tag, "alt"),
    });
  }

  return images;
}

export function stripImagesFromHtml(html: string): string {
  if (!html) return html;

  return html
    .replace(/<figure\b[^>]*>[\s\S]*?<img\b[\s\S]*?<\/figure>/gi, "")
    .replace(/<img\b[^>]*>/gi, "")
    .replace(/<p>\s*(?:&nbsp;|\s|<br\s*\/?>)*<\/p>/gi, "")
    .trim();
}

export function buildOgImages(imageUrl: string | null | undefined, siteUrl: string, alt?: string | null) {
  const resolvedUrl = imageUrl ?? absoluteUrl(DEFAULT_OG_IMAGE, siteUrl);
  return [{ url: resolvedUrl, width: 1200, height: 630, alt: alt ?? SITE_NAME }];
}

export function buildOrganizationSchema(siteUrl: string): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: SITE_NAME,
    url: normalizeSiteUrl(siteUrl),
    logo: absoluteUrl("/favicon.ico", siteUrl),
    sameAs: [normalizeSiteUrl(siteUrl)],
  };
}

export function buildWebsiteSchema(siteUrl: string): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: normalizeSiteUrl(siteUrl),
    description: SITE_DESCRIPTION,
    potentialAction: {
      "@type": "SearchAction",
      target: `${normalizeSiteUrl(siteUrl)}/search?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}

export function buildBreadcrumbSchema(items: Array<{ name: string; item: string }>): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((entry, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: entry.name,
      item: entry.item,
    })),
  };
}

type ArticleSchemaInput = {
  title: string;
  description: string;
  canonicalUrl: string;
  image?: string | null;
  publishedTime?: string | null;
  modifiedTime?: string | null;
  authorName?: string | null;
};

export function buildArticleSchema(input: ArticleSchemaInput): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: input.title,
    description: input.description,
    mainEntityOfPage: input.canonicalUrl,
    image: input.image ? [input.image] : undefined,
    datePublished: input.publishedTime ?? undefined,
    dateModified: input.modifiedTime ?? input.publishedTime ?? undefined,
    author: input.authorName
      ? {
          "@type": "Person",
          name: input.authorName,
        }
      : undefined,
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      logo: {
        "@type": "ImageObject",
        url: absoluteUrl("/favicon.ico", input.canonicalUrl),
      },
    },
  };
}
