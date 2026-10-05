import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.57.4";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" },
  });

const serviceKey = () => {
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (raw) {
    const parsed = JSON.parse(raw);
    return parsed.default || Object.values(parsed)[0];
  }
  throw new Error("Chave administrativa do Supabase indisponível.");
};

const admin = createClient(Deno.env.get("SUPABASE_URL")!, serviceKey(), {
  auth: { persistSession: false, autoRefreshToken: false },
});

const cleanCode = (value: unknown) =>
  String(value ?? "").trim().replace(/[^0-9A-Za-z._-]/g, "").slice(0, 64);

const cleanText = (value: unknown, max = 240) =>
  String(value ?? "").replace(/\s+/g, " ").trim().slice(0, max);

type Candidate = {
  name: string;
  brand?: string;
  quantity?: string;
  imageUrl?: string;
  externalUrl?: string;
  source: string;
  sourceLabel: string;
  confidence: number;
};

const uniqueCandidates = (items: Candidate[]) => {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = (item.name + "|" + (item.brand || "")).toLowerCase();
    if (!item.name || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const fromOpenFoodFacts = async (code: string): Promise<Candidate[]> => {
  try {
    const url = "https://world.openfoodfacts.org/api/v2/product/" + encodeURIComponent(code)
      + ".json?fields=code,product_name,product_name_pt,brands,quantity,image_front_url,url";
    const res = await fetch(url, {
      headers: { "User-Agent": "DeliciasDaVovo-ControleProdu/1.0 (product lookup)" },
    });
    if (!res.ok) return [];
    const data = await res.json();
    if (Number(data?.status) !== 1 || !data?.product) return [];
    const p = data.product;
    const name = cleanText(p.product_name_pt || p.product_name || "");
    if (!name) return [];
    return [{
      name,
      brand: cleanText(p.brands || "", 120),
      quantity: cleanText(p.quantity || "", 80),
      imageUrl: cleanText(p.image_front_url || "", 500),
      externalUrl: cleanText(p.url || ("https://world.openfoodfacts.org/product/" + code), 500),
      source: "open_food_facts",
      sourceLabel: "Open Food Facts",
      confidence: 0.98,
    }];
  } catch {
    return [];
  }
};

const fromMercadoLivre = async (code: string): Promise<Candidate[]> => {
  try {
    const url = "https://api.mercadolibre.com/sites/MLB/search?q="
      + encodeURIComponent(code) + "&limit=6";
    const res = await fetch(url, {
      headers: { "User-Agent": "DeliciasDaVovo-ControleProdu/1.0" },
    });
    if (!res.ok) return [];
    const data = await res.json();
    const rows = Array.isArray(data?.results) ? data.results : [];
    return rows.slice(0, 6).map((r: any) => ({
      name: cleanText(r?.title || ""),
      brand: "",
      quantity: "",
      imageUrl: cleanText(r?.thumbnail || "", 500),
      externalUrl: cleanText(r?.permalink || "", 500),
      source: "mercado_livre",
      sourceLabel: "Mercado Livre",
      confidence: 0.55,
    })).filter((x: Candidate) => !!x.name);
  } catch {
    return [];
  }
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Método não permitido." }, 405);

  try {
    const body = await req.json().catch(() => ({}));
    const code = cleanCode(body?.code);
    if (!code || code.length < 3) return json({ error: "Informe um código válido." }, 400);

    const nowIso = new Date().toISOString();
    const { data: cached } = await admin
      .from("product_lookup_cache")
      .select("results,searched_at,expires_at")
      .eq("code", code)
      .gt("expires_at", nowIso)
      .maybeSingle();

    if (cached) {
      return json({
        code,
        results: Array.isArray(cached.results) ? cached.results : [],
        cached: true,
        searchedAt: cached.searched_at,
      });
    }

    const [food, ml] = await Promise.all([
      fromOpenFoodFacts(code),
      fromMercadoLivre(code),
    ]);

    const results = uniqueCandidates([...food, ...ml]).slice(0, 8);
    const ttlDays = results.length ? 30 : 3;
    const expiresAt = new Date(Date.now() + ttlDays * 86400000).toISOString();

    await admin.from("product_lookup_cache").upsert({
      code,
      results,
      searched_at: nowIso,
      expires_at: expiresAt,
    }, { onConflict: "code" });

    return json({ code, results, cached: false, searchedAt: nowIso });
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : "Falha na busca do produto." }, 500);
  }
});
