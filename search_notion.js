// Notion 検索（データソース配慮付き）サンプル
// 前提: 環境変数 NOTION_API_KEY に Internal Integration Token (secret_...) を設定

const token = process.env.NOTION_API_KEY;
const keyword = process.argv[2] ?? "北海道"; // タイトルに含めたい語。未指定なら「北海道」
if (!token) {
  console.error("環境変数 NOTION_API_KEY が未設定です。secret_で始まるトークンを設定してください。");
  process.exit(1);
}

(async () => {
  try {
    // 1回目: 通常の検索（クエリ=keyword）
    const res = await fetch("https://api.notion.com/v1/search", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: keyword,
        page_size: 100,
        sort: { direction: "descending", timestamp: "last_edited_time" },
      }),
    });
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status} ${res.statusText} ${errText}`);
    }
    const data = await res.json();
    let results = data.results ?? [];

    const richTextToPlain = (arr) =>
      Array.isArray(arr) ? arr.map(t => t?.plain_text ?? "").join("") : "";

    const titleFromProps = (props = {}) => {
      for (const v of Object.values(props)) {
        if (v?.type === "title") return richTextToPlain(v.title);
      }
      return "";
    };

    // item.object が page 以外（data_source / database）の場合は上位の title を優先
    const titleFromAny = (item) => {
      if (item?.title) return richTextToPlain(item.title);
      return titleFromProps(item?.properties ?? {});
    };

    // 0件だった場合のフォールバック: クエリ空で取得→タイトルにkeywordを含むページだけ抽出
    if (!results.length) {
      const res2 = await fetch("https://api.notion.com/v1/search", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Notion-Version": "2025-09-03",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: "",
          page_size: 100,
          sort: { direction: "descending", timestamp: "last_edited_time" },
        }),
      });
      if (res2.ok) {
        const data2 = await res2.json();
        const all = data2.results ?? [];
        results = all.filter(r => {
          if (r.object !== "page") return false;
          const title = titleFromProps(r.properties);
          return title.includes(keyword);
        });
      }
    }

    const pages = results
      .filter(r => r.object === "page")
      .sort((a, b) => new Date(b.last_edited_time) - new Date(a.last_edited_time))
      .slice(0, 10);

    console.log(`== Pages (更新新しい順・最大10件) | keyword="${keyword}" ==`);
    for (const p of pages) {
      console.log(`${titleFromProps(p.properties)} | ${p.url} | 最終更新: ${p.last_edited_time}`);
    }

    const sources = results
      .filter(r => ["data_source", "database"].includes(r.object))
      .sort((a, b) => new Date(b.last_edited_time) - new Date(a.last_edited_time))
      .slice(0, 10);

    if (sources.length) {
      console.log("\n== Data Sources / Databases ==");
      for (const d of sources) {
        const kind = d.object === "data_source" ? "DATA_SOURCE" : "DATABASE";
        console.log(`${kind} | ${titleFromAny(d)} | URL: ${d.url} | 最終更新: ${d.last_edited_time}`);
        if (d.object === "data_source") console.log(`  data_source_id: ${d.id}`);
      }
    }
  } catch (e) {
    console.error("検索に失敗しました:", e?.message || e);
    process.exit(1);
  }
})();


