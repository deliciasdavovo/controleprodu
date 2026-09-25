
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.57.4";
import { XMLParser } from "npm:fast-xml-parser@4.5.0";
import forge from "npm:node-forge@1.3.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-nfe-token",
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

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  removeNSPrefix: true,
  parseTagValue: false,
  trimValues: true,
});

const asArray = <T>(value: T | T[] | undefined | null): T[] =>
  value == null ? [] : Array.isArray(value) ? value : [value];

const digits = (value: unknown) => String(value ?? "").replace(/\D/g, "");
const safeProfile = (value: unknown) => {
  const cleaned = String(value || "default").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return cleaned || "default";
};

const num = (value: unknown) => {
  const n = Number(String(value ?? "").replace(",", "."));
  return Number.isFinite(n) ? n : 0;
};

const textValue = (value: unknown) => {
  if (value == null) return "";
  if (typeof value === "object" && value && "#text" in (value as Record<string, unknown>)) {
    return String((value as Record<string, unknown>)["#text"] ?? "");
  }
  return String(value);
};

const sha256Hex = async (value: string) => {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
};

const requireFiscalToken = async (req: Request) => {
  const token = req.headers.get("x-nfe-token")?.trim() || "";
  if (!token) throw new Error("Código fiscal não informado.");

  const { data, error } = await admin
    .from("nfe_settings")
    .select("access_token_hash")
    .eq("id", "default")
    .single();

  if (error || !data?.access_token_hash) throw new Error("Módulo fiscal ainda não foi inicializado.");
  const supplied = await sha256Hex(token);
  if (supplied !== data.access_token_hash) throw new Error("Código fiscal inválido.");
};

const readVaultSecret = async (name: string) => {
  const { data, error } = await admin.rpc("nfe_read_secret", { p_name: name });
  if (error) return "";
  return String(data || "");
};

const storeVaultSecret = async (name: string, value: string, description: string) => {
  const { error } = await admin.rpc("nfe_store_secret", {
    p_name: name,
    p_value: value,
    p_description: description,
  });
  if (error) throw error;
};

const deleteVaultSecret = async (name: string) => {
  const { error } = await admin.rpc("nfe_delete_secret", { p_name: name });
  if (error) throw error;
};

const fiscalConfig = async (profileRaw: unknown = "default") => {
  const profile = safeProfile(profileRaw);
  const prefix = "nfe_" + profile + "_";
  const [vaultPfx, vaultPassword, vaultCnpj, vaultUf, vaultAmb] = await Promise.all([
    readVaultSecret(prefix + "cert_pfx_base64"),
    readVaultSecret(prefix + "cert_password"),
    readVaultSecret(prefix + "cnpj"),
    readVaultSecret(prefix + "uf_code"),
    readVaultSecret(prefix + "tp_amb"),
  ]);

  const useLegacyEnv = profile === "default";
  const environmentRaw = (useLegacyEnv ? Deno.env.get("NFE_TP_AMB") : "") || vaultAmb || "1";
  const environment = Number(environmentRaw) === 2 ? 2 : 1;

  return {
    profile,
    prefix,
    pfxBase64: (useLegacyEnv ? Deno.env.get("NFE_CERT_PFX_BASE64") : "") || vaultPfx || "",
    password: (useLegacyEnv ? Deno.env.get("NFE_CERT_PASSWORD") : "") || vaultPassword || "",
    cnpj: digits((useLegacyEnv ? Deno.env.get("NFE_CNPJ") : "") || vaultCnpj || ""),
    ufCode: digits((useLegacyEnv ? Deno.env.get("NFE_UF_CODE") : "") || vaultUf || "35"),
    environment,
    distUrl:
      (useLegacyEnv ? Deno.env.get("NFE_DIST_URL") : "") ||
      (environment === 2
        ? "https://hom.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
        : "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"),
  };
};

const configureCertificate = async (body: any) => {
  const profile = safeProfile(body.unit_code);
  const prefix = "nfe_" + profile + "_";
  const pfxBase64 = String(body.pfx_base64 || "").replace(/\s+/g, "");
  const password = String(body.password || "");
  const cnpj = digits(body.cnpj || "");
  const ufCode = digits(body.uf_code || "35");
  const environment = Number(body.environment || 1) === 2 ? "2" : "1";

  if (!pfxBase64) throw new Error("Selecione o certificado A1 (.pfx ou .p12).");
  if (!password) throw new Error("Informe a senha do certificado A1.");
  if (cnpj.length !== 14) throw new Error("Informe o CNPJ com 14 dígitos.");
  if (ufCode.length !== 2) throw new Error("UF inválida.");

  pfxToPem(pfxBase64, password);

  await storeVaultSecret(prefix + "cert_pfx_base64", pfxBase64, "Certificado A1 NF-e do perfil " + profile);
  await storeVaultSecret(prefix + "cert_password", password, "Senha do certificado A1 NF-e do perfil " + profile);
  await storeVaultSecret(prefix + "cnpj", cnpj, "CNPJ consultado no NFeDistribuicaoDFe - " + profile);
  await storeVaultSecret(prefix + "uf_code", ufCode, "Código IBGE UF - " + profile);
  await storeVaultSecret(prefix + "tp_amb", environment, "Ambiente NF-e - " + profile);

  await admin.from("nfe_sync_state").upsert(
    { id: profile, updated_at: new Date().toISOString() },
    { onConflict: "id", ignoreDuplicates: true }
  );

  return {
    configured: true,
    profile,
    cnpjMasked: cnpj.slice(0, 4) + "••••••" + cnpj.slice(-4),
    ufCode,
    environment: Number(environment),
  };
};

const clearCertificate = async (body: any) => {
  const profile = safeProfile(body.unit_code);
  const prefix = "nfe_" + profile + "_";
  await Promise.all([
    deleteVaultSecret(prefix + "cert_pfx_base64"),
    deleteVaultSecret(prefix + "cert_password"),
    deleteVaultSecret(prefix + "cnpj"),
    deleteVaultSecret(prefix + "uf_code"),
    deleteVaultSecret(prefix + "tp_amb"),
  ]);
  return { configured: false, profile };
};

const pfxToPem = (pfxBase64: string, password: string) => {
  const der = forge.util.decode64(pfxBase64.replace(/\s+/g, ""));
  const asn1 = forge.asn1.fromDer(der);
  const p12 = forge.pkcs12.pkcs12FromAsn1(asn1, false, password);

  const keyBags =
    p12.getBags({ bagType: forge.pki.oids.pkcs8ShroudedKeyBag })[
      forge.pki.oids.pkcs8ShroudedKeyBag
    ] ||
    p12.getBags({ bagType: forge.pki.oids.keyBag })[forge.pki.oids.keyBag] ||
    [];
  const certBags =
    p12.getBags({ bagType: forge.pki.oids.certBag })[forge.pki.oids.certBag] || [];

  const privateKey = keyBags.find((b: any) => b.key)?.key;
  if (!privateKey) throw new Error("Não foi possível ler a chave privada do certificado A1.");

  const leaf = certBags.find((b: any) => b.cert)?.cert;
  if (!leaf) throw new Error("Não foi possível ler o certificado A1.");

  const leafPem = forge.pki.certificateToPem(leaf);
  const others = certBags
    .filter((b: any) => b.cert && b.cert !== leaf)
    .map((b: any) => forge.pki.certificateToPem(b.cert))
    .join("");

  return {
    cert: leafPem + others,
    key: forge.pki.privateKeyToPem(privateKey),
  };
};

const findDeep = (node: any, key: string): any => {
  if (!node || typeof node !== "object") return undefined;
  if (Object.prototype.hasOwnProperty.call(node, key)) return node[key];
  for (const value of Object.values(node)) {
    const found = findDeep(value, key);
    if (found !== undefined) return found;
  }
  return undefined;
};

const unzipDoc = async (base64: string) => {
  const cleaned = base64.replace(/\s+/g, "");
  const binary = atob(cleaned);
  const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0));
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
  return await new Response(stream).text();
};

const keyParts = (accessKey: string) => ({
  series: accessKey.length === 44 ? String(Number(accessKey.slice(22, 25))) : "",
  number: accessKey.length === 44 ? String(Number(accessKey.slice(25, 34))) : "",
});

const normalizeUnit = (unit: string) => {
  const u = unit.trim().toUpperCase();
  if (u === "KG") return "kg";
  if (u === "G" || u === "GR") return "g";
  if (u === "L" || u === "LT") return "L";
  if (u === "ML") return "ml";
  if (["UN", "UND", "PC", "PÇ", "PCA", "PÇS"].includes(u)) return "un";
  return unit.trim() || "un";
};

const applySavedMappings = async (issuerCnpj: string, documentId: string, rows: any[], profile = "default") => {
  if (!issuerCnpj || !rows.length) return rows;
  const { data: mappings } = await admin
    .from("nfe_product_mappings")
    .select("*")
    .eq("source_profile", safeProfile(profile))
    .eq("issuer_cnpj", issuerCnpj);

  const map = new Map((mappings || []).map((m: any) => [m.supplier_product_code, m]));
  return rows.map((row) => {
    const m = map.get(row.supplier_product_code);
    if (!m) return row;
    return {
      ...row,
      document_id: documentId,
      supply_id: m.supply_id || null,
      separated_product_id: m.separated_product_id || null,
      purchase_unit: m.purchase_unit || normalizeUnit(row.commercial_unit),
      purchase_qty: row.qty * (Number(m.qty_multiplier) || 1),
      mapping_status: m.supply_id ? "mapped_supply" : "mapped_resale",
    };
  });
};

const saveFullNfe = async (xml: string, nsu = "", schemaName = "procNFe_v4.00.xsd", profile = "default") => {
  const parsed = parser.parse(xml);
  const proc = parsed.nfeProc || parsed.NFe || parsed;
  const nfe = proc.NFe || parsed.NFe || proc;
  const inf = nfe.infNFe || findDeep(nfe, "infNFe");
  if (!inf) throw new Error("XML recebido não contém infNFe.");

  const ide = inf.ide || {};
  const emit = inf.emit || {};
  const dest = inf.dest || {};
  const total = inf.total?.ICMSTot || {};
  const accessKey = String(inf["@_Id"] || "").replace(/^NFe/, "") || digits(findDeep(parsed, "chNFe"));
  if (accessKey.length !== 44) throw new Error("XML sem chave de acesso válida.");

  const parts = keyParts(accessKey);
  const issueText = textValue(ide.dhEmi || ide.dEmi || "");
  const issueDate = issueText ? issueText.slice(0, 10) : null;
  const issuerCnpj = digits(emit.CNPJ || "");
  const recipientCnpj = digits(dest.CNPJ || "");

  const dets = asArray(inf.det);
  const itemRows = dets.map((det: any, idx: number) => {
    const prod = det.prod || {};
    const vProd = num(prod.vProd);
    const vDesc = num(prod.vDesc);
    const vFrete = num(prod.vFrete);
    const vOutro = num(prod.vOutro);
    return {
      item_number: Number(det["@_nItem"] || idx + 1),
      supplier_product_code: textValue(prod.cProd),
      description: textValue(prod.xProd),
      ncm: textValue(prod.NCM),
      cfop: textValue(prod.CFOP),
      gtin: textValue(prod.cEAN),
      commercial_unit: textValue(prod.uCom),
      qty: num(prod.qCom),
      unit_value: num(prod.vUnCom),
      total_value: Math.max(0, vProd - vDesc + vFrete + vOutro),
      purchase_unit: normalizeUnit(textValue(prod.uCom)),
      mapping_status: "unmapped",
    };
  });

  const docPayload = {
    access_key: accessKey,
    source_profile: safeProfile(profile),
    nsu: nsu || null,
    schema_name: schemaName || "",
    document_kind: "full",
    status: "needs_mapping",
    environment: Number(textValue(ide.tpAmb || "1")) === 2 ? 2 : 1,
    issuer_cnpj: issuerCnpj,
    issuer_name: textValue(emit.xNome),
    recipient_cnpj: recipientCnpj,
    issue_date: issueDate,
    total_value: num(total.vNF),
    nfe_number: textValue(ide.nNF) || parts.number,
    series: textValue(ide.serie) || parts.series,
    raw_xml: xml,
    last_seen_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { data: doc, error: docError } = await admin
    .from("nfe_documents")
    .upsert(docPayload, { onConflict: "access_key" })
    .select("*")
    .single();
  if (docError) throw docError;

  const mappedRows = await applySavedMappings(issuerCnpj, doc.id, itemRows, profile);
  await admin.from("nfe_items").delete().eq("document_id", doc.id);
  if (mappedRows.length) {
    const { error: itemsError } = await admin
      .from("nfe_items")
      .insert(mappedRows.map((r) => ({ ...r, document_id: doc.id })));
    if (itemsError) throw itemsError;
  }

  const allMapped =
    mappedRows.length > 0 &&
    mappedRows.every((r) => r.mapping_status !== "unmapped");
  await admin
    .from("nfe_documents")
    .update({ status: allMapped ? "ready" : "needs_mapping", updated_at: new Date().toISOString() })
    .eq("id", doc.id);

  return { accessKey, kind: "full", items: mappedRows.length };
};

const saveSummary = async (xml: string, nsu = "", schemaName = "resNFe_v1.01.xsd", profile = "default") => {
  const parsed = parser.parse(xml);
  const res = parsed.resNFe || findDeep(parsed, "resNFe");
  if (!res) throw new Error("Resumo de NF-e inválido.");

  const accessKey = digits(textValue(res.chNFe));
  if (accessKey.length !== 44) throw new Error("Resumo sem chave válida.");
  const parts = keyParts(accessKey);
  const issue = textValue(res.dhEmi || "");
  const payload = {
    access_key: accessKey,
    source_profile: safeProfile(profile),
    nsu: nsu || null,
    schema_name: schemaName || "",
    document_kind: "summary",
    status: "awaiting_xml",
    environment: 1,
    issuer_cnpj: digits(res.CNPJ || ""),
    issuer_name: textValue(res.xNome),
    issue_date: issue ? issue.slice(0, 10) : null,
    total_value: num(res.vNF),
    nfe_number: parts.number,
    series: parts.series,
    raw_summary: xml,
    last_seen_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { error } = await admin
    .from("nfe_documents")
    .upsert(payload, { onConflict: "access_key" });
  if (error) throw error;
  return { accessKey, kind: "summary", items: 0 };
};

const processEvent = async (xml: string, profile = "default") => {
  const parsed = parser.parse(xml);
  const chNFe = digits(textValue(findDeep(parsed, "chNFe")));
  const tpEvento = textValue(findDeep(parsed, "tpEvento"));
  if (chNFe.length === 44 && tpEvento === "110111") {
    await admin
      .from("nfe_documents")
      .update({ status: "cancelled", updated_at: new Date().toISOString() })
      .eq("access_key", chNFe)
      .eq("source_profile", safeProfile(profile));
    return { accessKey: chNFe, kind: "cancel_event", items: 0 };
  }
  return { accessKey: chNFe, kind: "event", items: 0 };
};

const processDistributedXml = async (xml: string, nsu = "", schemaName = "", profile = "default") => {
  if (/<(?:\w+:)?resNFe[\s>]/.test(xml)) return await saveSummary(xml, nsu, schemaName, profile);
  if (/<(?:\w+:)?(?:nfeProc|NFe)[\s>]/.test(xml)) return await saveFullNfe(xml, nsu, schemaName, profile);
  if (/<(?:\w+:)?(?:resEvento|procEventoNFe)[\s>]/.test(xml)) return await processEvent(xml, profile);
  return { accessKey: "", kind: "ignored", items: 0 };
};

const doSync = async (profileRaw: unknown = "default") => {
  const cfg = await fiscalConfig(profileRaw);
  if (!cfg.pfxBase64 || !cfg.password || cfg.cnpj.length !== 14 || cfg.ufCode.length !== 2) {
    throw new Error(
      "Certificado ainda não configurado. Faltam NFE_CERT_PFX_BASE64, NFE_CERT_PASSWORD, NFE_CNPJ ou NFE_UF_CODE."
    );
  }

  await admin.from("nfe_sync_state").upsert(
    { id: cfg.profile, updated_at: new Date().toISOString() },
    { onConflict: "id", ignoreDuplicates: true }
  );

  const { data: state, error: stateError } = await admin
    .from("nfe_sync_state")
    .select("*")
    .eq("id", cfg.profile)
    .single();
  if (stateError) throw stateError;

  const ultNSU = String(state.last_nsu || "0").padStart(15, "0");
  const soapBody =
    '<?xml version="1.0" encoding="utf-8"?>' +
    '<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' +
    'xmlns:xsd="http://www.w3.org/2001/XMLSchema" ' +
    'xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">' +
    '<soap12:Body>' +
    '<nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">' +
    '<nfeDadosMsg>' +
    '<distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">' +
    '<tpAmb>' + cfg.environment + '</tpAmb>' +
    '<cUFAutor>' + cfg.ufCode + '</cUFAutor>' +
    '<CNPJ>' + cfg.cnpj + '</CNPJ>' +
    '<distNSU><ultNSU>' + ultNSU + '</ultNSU></distNSU>' +
    '</distDFeInt>' +
    '</nfeDadosMsg>' +
    '</nfeDistDFeInteresse>' +
    '</soap12:Body></soap12:Envelope>';

  const pem = pfxToPem(cfg.pfxBase64, cfg.password);
  const client = Deno.createHttpClient({ cert: pem.cert, key: pem.key });

  let response: Response;
  try {
    response = await fetch(cfg.distUrl, {
      method: "POST",
      headers: {
        "Content-Type": 'application/soap+xml; charset=utf-8; action="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"',
        "Accept": "application/soap+xml, text/xml",
      },
      body: soapBody,
      client,
    } as RequestInit & { client: Deno.HttpClient });
  } finally {
    client.close();
  }

  const responseText = await response.text();
  if (!response.ok) throw new Error("SEFAZ respondeu HTTP " + response.status + ".");

  const parsed = parser.parse(responseText);
  const ret = findDeep(parsed, "retDistDFeInt");
  if (!ret) throw new Error("Resposta da SEFAZ sem retDistDFeInt.");

  const cStat = textValue(ret.cStat);
  const xMotivo = textValue(ret.xMotivo);
  const newUltNSU = textValue(ret.ultNSU || ultNSU).padStart(15, "0");
  const maxNSU = textValue(ret.maxNSU || newUltNSU).padStart(15, "0");

  const processed: any[] = [];
  const lot = ret.loteDistDFeInt || {};
  const docs = asArray(lot.docZip);
  for (const docZip of docs) {
    const base64 = textValue(docZip);
    if (!base64) continue;
    const nsu = textValue(docZip["@_NSU"]);
    const schemaName = textValue(docZip["@_schema"]);
    const xml = await unzipDoc(base64);
    processed.push(await processDistributedXml(xml, nsu, schemaName, cfg.profile));
  }

  await admin
    .from("nfe_sync_state")
    .update({
      last_nsu: newUltNSU,
      max_nsu: maxNSU,
      last_status_code: cStat,
      last_status_message: xMotivo,
      last_sync_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", cfg.profile);

  return {
    profile: cfg.profile,
    cStat,
    message: xMotivo,
    received: processed.length,
    processed,
    lastNSU: newUltNSU,
    maxNSU,
    hasMore: BigInt(newUltNSU || "0") < BigInt(maxNSU || "0"),
  };
};

const listDocuments = async (profileRaw: unknown = "default") => {
  const profile = safeProfile(profileRaw);
  const { data: docs, error } = await admin
    .from("nfe_documents")
    .select("id,access_key,nsu,source_profile,document_kind,status,issuer_cnpj,issuer_name,issue_date,total_value,nfe_number,series,imported_unit_code,imported_at,last_seen_at")
    .eq("source_profile", profile)
    .order("issue_date", { ascending: false, nullsFirst: false })
    .order("created_at", { ascending: false })
    .limit(200);
  if (error) throw error;

  const { data: state } = await admin
    .from("nfe_sync_state")
    .select("*")
    .eq("id", profile)
    .maybeSingle();

  return { profile, documents: docs || [], sync: state || null };
};

const getDocument = async (id: string, profileRaw: unknown = "default") => {
  const profile = safeProfile(profileRaw);
  const { data: doc, error: docError } = await admin
    .from("nfe_documents")
    .select("id,source_profile,access_key,document_kind,status,issuer_cnpj,issuer_name,recipient_cnpj,issue_date,total_value,nfe_number,series,imported_unit_code,imported_at")
    .eq("id", id)
    .eq("source_profile", profile)
    .single();
  if (docError) throw docError;

  const { data: items, error: itemsError } = await admin
    .from("nfe_items")
    .select("id,item_number,supplier_product_code,description,ncm,cfop,gtin,commercial_unit,qty,unit_value,total_value,supply_id,separated_product_id,purchase_qty,purchase_unit,mapping_status")
    .eq("document_id", id)
    .order("item_number");
  if (itemsError) throw itemsError;

  return { document: doc, items: items || [] };
};

const saveMapping = async (body: any) => {
  const profile = safeProfile(body.unit_code);
  const itemId = String(body.item_id || "");
  const kind = String(body.kind || "");
  const targetId = String(body.target_id || "");
  const multiplier = Math.max(0.000001, Number(body.qty_multiplier) || 1);
  const purchaseUnit = String(body.purchase_unit || "");

  if (!itemId) throw new Error("Item da NF-e não informado.");

  const { data: item, error: itemError } = await admin
    .from("nfe_items")
    .select("*, nfe_documents!inner(id,source_profile,issuer_cnpj,status)")
    .eq("id", itemId)
    .single();
  if (itemError) throw itemError;
  if (safeProfile(item.nfe_documents?.source_profile) !== profile) {
    throw new Error("NF-e não pertence à unidade selecionada.");
  }

  if (kind === "ignore") {
    const { error } = await admin
      .from("nfe_items")
      .update({
        supply_id: null,
        separated_product_id: null,
        mapping_status: "ignored",
        updated_at: new Date().toISOString(),
      })
      .eq("id", itemId);
    if (error) throw error;
  } else if (kind === "supply" || kind === "resale") {
    if (!targetId) throw new Error("Escolha o cadastro correspondente.");
    const supplyId = kind === "supply" ? targetId : null;
    const resaleId = kind === "resale" ? targetId : null;
    const mappedStatus = kind === "supply" ? "mapped_supply" : "mapped_resale";
    const normalizedPurchaseUnit = purchaseUnit || normalizeUnit(item.commercial_unit);

    const { error: updateError } = await admin
      .from("nfe_items")
      .update({
        supply_id: supplyId,
        separated_product_id: resaleId,
        purchase_unit: normalizedPurchaseUnit,
        purchase_qty: Number(item.qty) * multiplier,
        mapping_status: mappedStatus,
        updated_at: new Date().toISOString(),
      })
      .eq("id", itemId);
    if (updateError) throw updateError;

    const issuerCnpj = digits(item.nfe_documents?.issuer_cnpj || "");
    if (issuerCnpj && item.supplier_product_code) {
      const { error: mapError } = await admin.from("nfe_product_mappings").upsert(
        {
          source_profile: profile,
          issuer_cnpj: issuerCnpj,
          supplier_product_code: item.supplier_product_code,
          description_hint: item.description || "",
          supply_id: supplyId,
          separated_product_id: resaleId,
          qty_multiplier: multiplier,
          purchase_unit: normalizedPurchaseUnit,
          updated_at: new Date().toISOString(),
        },
        { onConflict: "source_profile,issuer_cnpj,supplier_product_code" }
      );
      if (mapError) throw mapError;
    }
  } else {
    throw new Error("Tipo de vínculo inválido.");
  }

  const documentId = item.document_id;
  const { data: remaining } = await admin
    .from("nfe_items")
    .select("id")
    .eq("document_id", documentId)
    .eq("mapping_status", "unmapped")
    .limit(1);

  await admin
    .from("nfe_documents")
    .update({
      status: remaining?.length ? "needs_mapping" : "ready",
      updated_at: new Date().toISOString(),
    })
    .eq("id", documentId);

  return await getDocument(documentId, profile);
};

const importDocument = async (body: any) => {
  const profile = safeProfile(body.unit_code);
  const id = String(body.document_id || "");
  const unitCode = String(body.unit_code || "");
  if (!id) throw new Error("NF-e não informada.");

  const { data: doc, error: docError } = await admin
    .from("nfe_documents")
    .select("*")
    .eq("id", id)
    .eq("source_profile", profile)
    .single();
  if (docError) throw docError;
  if (doc.status === "imported") return { imported: true, alreadyImported: true };
  if (doc.document_kind !== "full") throw new Error("O XML completo ainda não está disponível.");

  const { data: items, error: itemsError } = await admin
    .from("nfe_items")
    .select("*")
    .eq("document_id", id)
    .order("item_number");
  if (itemsError) throw itemsError;

  const unmapped = (items || []).filter((i: any) => i.mapping_status === "unmapped");
  if (unmapped.length) throw new Error("Ainda existem itens sem vínculo.");

  let imported = 0;
  for (const item of items || []) {
    if (item.mapping_status === "ignored") continue;

    const purchaseUnit = item.purchase_unit || normalizeUnit(item.commercial_unit);
    const multiplierBase = item.qty > 0 && item.purchase_qty
      ? Number(item.purchase_qty) / Number(item.qty)
      : 1;

    if (item.supply_id) {
      const { data: supply, error: supplyError } = await admin
        .from("supplies")
        .select("id,unit")
        .eq("id", item.supply_id)
        .single();
      if (supplyError) throw supplyError;

      let normalizedQty = Number(item.qty) * multiplierBase;
      if (supply.unit === "g" && purchaseUnit.toLowerCase() === "kg") normalizedQty *= 1000;
      if (supply.unit === "ml" && purchaseUnit.toLowerCase() === "l") normalizedQty *= 1000;

      const { error } = await admin.from("supply_purchases").insert({
        supply_id: item.supply_id,
        supplier: doc.issuer_name || "",
        purchase_date: doc.issue_date,
        qty: normalizedQty,
        purchase_unit: purchaseUnit,
        cost: Number(item.total_value) || 0,
        nfe_document_id: id,
        nfe_item_id: item.id,
      });
      if (error && error.code !== "23505") throw error;
      imported += 1;
    } else if (item.separated_product_id) {
      const qty = Number(item.qty) * multiplierBase;
      const { error } = await admin.from("resale_purchases").insert({
        separated_product_id: item.separated_product_id,
        supplier: doc.issuer_name || "",
        purchase_date: doc.issue_date,
        qty,
        purchase_unit: purchaseUnit || "un",
        cost: Number(item.total_value) || 0,
        nfe_document_id: id,
        nfe_item_id: item.id,
      });
      if (error && error.code !== "23505") throw error;
      imported += 1;
    }
  }

  await admin
    .from("nfe_items")
    .update({ mapping_status: "imported", updated_at: new Date().toISOString() })
    .eq("document_id", id)
    .neq("mapping_status", "ignored");

  await admin
    .from("nfe_documents")
    .update({
      status: "imported",
      imported_unit_code: unitCode || null,
      imported_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", id);

  return { imported: true, itemsImported: imported };
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Método não permitido." }, 405);

  try {
    await requireFiscalToken(req);
    const body = await req.json().catch(() => ({}));
    const action = String(body.action || "status");

    if (action === "status") {
      const cfg = await fiscalConfig(body.unit_code);
      const { data: state } = await admin
        .from("nfe_sync_state")
        .select("*")
        .eq("id", cfg.profile)
        .maybeSingle();
      return json({
        ok: true,
        profile: cfg.profile,
        certificateConfigured: !!cfg.pfxBase64 && !!cfg.password,
        cnpjConfigured: cfg.cnpj.length === 14,
        cnpjMasked: cfg.cnpj.length === 14 ? cfg.cnpj.slice(0, 4) + "••••••" + cfg.cnpj.slice(-4) : "",
        ufConfigured: cfg.ufCode.length === 2,
        ufCode: cfg.ufCode,
        environment: cfg.environment,
        sync: state || null,
      });
    }

    if (action === "configure_certificate") {
      return json({ ok: true, ...(await configureCertificate(body)) });
    }
    if (action === "clear_certificate") {
      return json({ ok: true, ...(await clearCertificate(body)) });
    }
    if (action === "sync") return json({ ok: true, ...(await doSync(body.unit_code)) });
    if (action === "list") return json({ ok: true, ...(await listDocuments(body.unit_code)) });
    if (action === "get") return json({ ok: true, ...(await getDocument(String(body.document_id || ""), body.unit_code)) });
    if (action === "save_mapping") return json({ ok: true, ...(await saveMapping(body)) });
    if (action === "import_document") return json({ ok: true, ...(await importDocument(body)) });

    if (action === "import_xml") {
      const xml = String(body.xml || "").trim();
      if (!xml) throw new Error("Cole ou envie o XML da NF-e.");
      const result = await processDistributedXml(xml, "", "manual", safeProfile(body.unit_code));
      return json({ ok: true, result });
    }

    return json({ error: "Ação fiscal desconhecida." }, 400);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return json({ error: message }, 400);
  }
});
