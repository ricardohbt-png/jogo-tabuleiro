// Slides condicionais no editor de história: carregar/salvar conserva a condição e os slides
// comuns continuam saindo como antes. Roda da raiz: node tools/test_editor_story_condicao.js
const fs = require("fs"), path = require("path"), assert = require("assert");
global.window = {}; global.document = {};
eval(fs.readFileSync(path.join(__dirname, "editor_story.js"), "utf8"));
const E = window.EDITOR_STORY;
let ok = 0; const t = (nome, fn) => { fn(); ok++; console.log("  ✅ " + nome); };

const REQ = { renome_min: 0, nivel_grupo_min: 0, item_id: "anel_garra_negra", fato: "", aventura_id: "" };
const salvo = { slides: [
  { text: "a", fit: "contain" },
  { text: "b", fit: "contain", requisito: REQ, negar: true },
  { text: "c", fit: "contain" }] };

t("roundtrip conserva requisito e negar", () => {
  const out = E.storyToSaved(E.storyFromSaved(salvo));
  assert.deepStrictEqual(out.slides[1].requisito, REQ);
  assert.strictEqual(out.slides[1].negar, true);
  assert.strictEqual("requisito" in out.slides[0], false);
  assert.strictEqual("negar" in out.slides[2], false);
});
t("slide comum sai igual (sem campos novos)", () => {
  const out = E.storyToSaved(E.storyFromSaved({ slides: [{ text: "x", fit: "contain" }, { text: "y" }] }));
  assert.deepStrictEqual(out, { slides: [{ text: "x", fit: "contain" }, { text: "y" }] });
});
t("um slide só-texto continua virando string", () => {
  assert.strictEqual(E.storyToSaved(E.storyFromSaved("oi")), "oi");
});
t("um slide único COM condição não vira string (perderia a condição)", () => {
  const st = E.storyFromSaved({ slides: [{ text: "só com anel", requisito: REQ }] });
  const out = E.storyToSaved(st);
  assert.strictEqual(typeof out, "object");
  assert.deepStrictEqual(out.slides[0].requisito, REQ);
});
t("requisito vazio é descartado", () => {
  const st = E.storyFromSaved({ slides: [{ text: "a" }, { text: "b" }] });
  st.slides[0].requisito = { renome_min: 0, nivel_grupo_min: 0, item_id: "", fato: "", aventura_id: "" };
  assert.strictEqual("requisito" in E.storyToSaved(st).slides[0], false);
});
console.log(`${ok} ok`);
