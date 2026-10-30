
// ========================================
// NOVAFACTS - AUTOMATIC RSS NEWS API
// Cloudflare Pages Functions
// Cache: 60 minutes
// Languages: Nepali + English
// ========================================

const FEEDS = [
  { category: "Nepal", query: "नेपाल समाचार", lang: "ne" },
  { category: "Nepal", query: "Nepal news", lang: "en" },

  { category: "World", query: "विश्व समाचार", lang: "ne" },
  { category: "World", query: "world news", lang: "en" },

  { category: "Science", query: "विज्ञान समाचार", lang: "ne" },
  { category: "Science", query: "science news", lang: "en" },

  { category: "Space", query: "अन्तरिक्ष खगोल विज्ञान", lang: "ne" },
  { category: "Space", query: "space astronomy", lang: "en" },

  { category: "AI", query: "कृत्रिम बुद्धिमत्ता", lang: "ne" },
  { category: "AI", query: "artificial intelligence technology", lang: "en" },

  { category: "Environment", query: "वातावरण जलवायु", lang: "ne" },
  { category: "Environment", query: "environment climate", lang: "en" }
];

// Decode XML text safely
function decodeXML(value = "") {
  return value
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]*>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => {
      const code = Number(n);
      return code <= 0x10FFFF
        ? String.fromCodePoint(code)
        : "";
    })
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => {
      const code = parseInt(n, 16);
      return code <= 0x10FFFF
        ? String.fromCodePoint(code)
        : "";
    })
    .trim();
}

// Read XML tag content
function getTag(xml, tag) {
  const regex = new RegExp(
    `<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tag}\\s*>`,
    "i"
  );

  const match = xml.match(regex);
  return match ? decodeXML(match[1]) : "";
}

// Fetch one RSS feed
async function getFeed(feed) {
  const locale = feed.lang === "ne"
    ? "hl=ne&gl=NP&ceid=NP:ne"
    : "hl=en-US&gl=US&ceid=US:en";

  const rssURL =
    "https://news.google.com/rss/search?q=" +
    encodeURIComponent(feed.query) +
    "&" + locale;

  try {
    const response = await fetch(rssURL, {
      headers: {
        "User-Agent": "Mozilla/5.0 NovaFacts RSS Reader",
        "Accept": "application/rss+xml, application/xml, text/xml"
      },
      signal: AbortSignal.timeout(12000)
    });

    if (!response.ok) {
      throw new Error("RSS HTTP " + response.status);
    }

    const xml = await response.text();

    const matches = [
      ...xml.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item\s*>/gi)
    ];

    return matches.slice(0, 8).map(match => {
      const item = match[1];

      const title = getTag(item, "title");
      const link = getTag(item, "link");
      const source = getTag(item, "source");
      const published = getTag(item, "pubDate");
      const description = getTag(item, "description");

      if (!title || !link) return null;

      let safeLink;

      try {
        safeLink = new URL(link);

        if (safeLink.protocol !== "https:") {
          return null;
        }
      } catch {
        return null;
      }

      const date = new Date(published);

      return {
        title,
        summary: description,
        link: safeLink.href,
        source: source || "Google News",
        publishedAt: isNaN(date.getTime())
          ? null
          : date.toISOString(),
        category: feed.category,
        language: feed.lang
      };
    }).filter(Boolean);

  } catch (error) {
    console.error(
      "RSS error:",
      feed.category,
      feed.lang,
      error.message
    );

    return [];
  }
}

// Create complete news response
async function createNews() {
  const results = await Promise.all(
    FEEDS.map(feed => getFeed(feed))
  );

  const allNews = results.flat();
  const unique = new Map();

  for (const item of allNews) {
    if (!unique.has(item.link)) {
      unique.set(item.link, item);
    }
  }

  const items = [...unique.values()]
    .sort((a, b) =>
      new Date(b.publishedAt || 0) -
      new Date(a.publishedAt || 0)
    )
    .slice(0, 80);

  return {
    website: "NovaFacts",
    updatedAt: new Date().toISOString(),
    refreshMinutes: 60,
    language: "both",
    total: items.length,
    items
  };
}

// Cloudflare Pages API endpoint
export async function onRequestGet({ request, waitUntil }) {
  const url = new URL(request.url);

  const forceRefresh =
    url.searchParams.get("refresh") === "1";

  const cache = caches.default;

  const cacheKey = new Request(
    url.origin + "/api/news"
  );

  // Check 60-minute cache
  if (!forceRefresh) {
    const cached = await cache.match(cacheKey);

    if (cached) {
      return cached;
    }
  }

  try {
    const data = await createNews();

    if (data.total === 0) {
      return Response.json(
        {
          error: "RSS feeds did not return news.",
          updatedAt: data.updatedAt,
          total: 0,
          items: []
        },
        {
          status: 502,
          headers: {
            "Cache-Control": "no-store"
          }
        }
      );
    }

    const response = Response.json(data, {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=0, s-maxage=3600"
      }
    });

    if (waitUntil) {
      waitUntil(
        cache.put(cacheKey, response.clone())
      );
    }

    return response;

  } catch (error) {
    console.error("NovaFacts API:", error);

    return Response.json(
      {
        error: "Unable to load news right now.",
        total: 0,
        items: []
      },
      {
        status: 500,
        headers: {
          "Cache-Control": "no-store"
        }
      }
    );
  }
}
