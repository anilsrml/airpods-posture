// node --test widget/tests/*.test.js
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

// logic.js QML'in JS kaynak dosyası; export yok, o yüzden vm ile yüklenir.
const ctx = {};
vm.runInNewContext(
  fs.readFileSync(path.join(__dirname, "../org.anilsrml.durus/contents/ui/logic.js"), "utf8"), ctx);

test("dik duruş yeşil", () => {
  const v = ctx.view({ state: "upright", pitch: 3.2 });
  assert.strictEqual(v.color, "#2ecc71");
  assert.strictEqual(v.label, "Dik");
});

test("her durumun rengi ve etiketi", () => {
  const cases = [
    ["leaning", "#f1c40f", "Eğik"],
    ["slouched", "#e74c3c", "Kambur"],
    ["calibrating", "#95a5a6", "Sıfırlanıyor, dik dur"],
    ["disconnected", "#95a5a6", "AirPods bağlı değil"],
    ["stopped", "#95a5a6", "Durduruldu"],
  ];
  for (const [state, color, label] of cases) {
    const v = ctx.view({ state, pitch: null });
    assert.deepStrictEqual([v.color, v.label], [color, label], state);
  }
});

test("servis yanıt vermiyorsa", () => {
  const v = ctx.view(null);
  assert.strictEqual(v.label, "Servis çalışmıyor");
  assert.strictEqual(v.color, "#95a5a6");
  assert.strictEqual(v.detail, "");
});

test("eğim detayı", () => {
  assert.strictEqual(ctx.view({ state: "leaning", pitch: 17.25 }).detail, "Öne eğim: +17.3°");
  assert.strictEqual(ctx.view({ state: "upright", pitch: -4 }).detail, "Öne eğim: -4.0°");
  assert.strictEqual(ctx.view({ state: "disconnected", pitch: null }).detail, "");
});

test("çalışıyor mu", () => {
  assert.strictEqual(ctx.isRunning(null), false);
  assert.strictEqual(ctx.isRunning({ state: "stopped" }), false);
  assert.strictEqual(ctx.isRunning({ state: "disconnected" }), true);
  assert.strictEqual(ctx.isRunning({ state: "upright" }), true);
});
