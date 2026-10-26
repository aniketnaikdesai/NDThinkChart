// envelope.test.js — node --test contract suite for chart_assets/lwc/ (P6-T04).
// Runs with the repo's node install, no npm deps, no network. CommonJS so
// the file runs both directly and via the directory entry (package.json).
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync, existsSync } = require("node:fs");
const path = require("node:path");

const DIR = __dirname;
const read = (name) => readFileSync(path.join(DIR, name), "utf8");
const LwEnvelope = require("./envelope.js");

describe("vendored runtime pin", () => {
  it("VERSION file matches the vendored header and the asserted pin", () => {
    const pinned = read("VERSION").trim();
    assert.match(pinned, /^\d+\.\d+\.\d+$/, "VERSION must be a full semver pin");
    const header = read("lightweight-charts.standalone.production.js").slice(0, 600);
    assert.ok(
      header.includes(`Lightweight Charts\u2122 v${pinned}`) ||
        header.includes(`Lightweight Charts v${pinned}`),
      `vendored header must declare v${pinned}`,
    );
    assert.equal(pinned, "5.2.1", "this wave pins the v5.2.x tree at 5.2.1");
  });

  it("attribution file is present and names the version", () => {
    assert.ok(existsSync(path.join(DIR, "ATTRIBUTION.md")), "ATTRIBUTION.md must ship");
    assert.ok(read("ATTRIBUTION.md").includes("5.2.1"));
  });
});

describe("offline / no-CDN loader surface", () => {
  for (const name of ["chart.html", "chart.js", "envelope.js"]) {
    it(`${name} has no remote fetch`, () => {
      const src = read(name);
      assert.ok(!/(src|href)\s*=\s*["']https?:\/\//i.test(src), `${name}: no remote src/href`);
      assert.ok(!/\bfrom\s+["']https?:\/\//.test(src), `${name}: no remote import`);
      assert.ok(!/unpkg\.com|cdn\.jsdelivr|cdnjs\.cloudflare/i.test(src), `${name}: no CDN host`);
      assert.ok(!/require\(["'][^./]/.test(src), `${name}: no bare npm require`);
    });
  }

  it("chart.html loads only relative vendored scripts plus the Qt qrc shim", () => {
    const html = read("chart.html");
    const scripts = [...html.matchAll(/<script\s+src="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(scripts.length > 0, "expected script tags");
    for (const s of scripts) {
      assert.ok(
        s.startsWith("./") || s.startsWith("qrc:///"),
        `script must be relative-vendored or qrc shim, got: ${s}`,
      );
    }
  });
});

describe("envelope contract {v:1, ops:[]} with column arrays", () => {
  const bars = (ts0, n) =>
    Array.from({ length: n }, (_, i) => ({
      ts: ts0 + i * 60,
      open: 100 + i,
      high: 101 + i,
      low: 99 + i,
      close: 100.5 + i,
    }));

  const toCols = (rows) => ({
    ts: rows.map((b) => b.ts),
    open: rows.map((b) => b.open),
    high: rows.map((b) => b.high),
    low: rows.map((b) => b.low),
    close: rows.map((b) => b.close),
  });

  it("accepts the exact envelope with column-array ops", () => {
    const env = {
      v: 1,
      ops: [
        { op: "set_bars", series: "candles", cols: toCols(bars(1000, 3)) },
        { op: "update_bar", series: "candles", cols: toCols(bars(1180, 1)) },
        { op: "set_volume", series: "volume", cols: { ts: [1000], value: [42] } },
      ],
    };
    assert.equal(LwEnvelope.validateEnvelope(env).ok, true);
  });

  it("rejects wrong versions, extra keys, scalar cols, ragged columns", () => {
    assert.equal(LwEnvelope.validateEnvelope({ v: 2, ops: [] }).ok, false);
    assert.equal(LwEnvelope.validateEnvelope({ v: 1, ops: [], extra: 1 }).ok, false);
    assert.equal(LwEnvelope.validateEnvelope({ v: 1 }).ok, false);
    assert.equal(LwEnvelope.validateEnvelope({ v: 1, ops: {} }).ok, false);
    const ragged = {
      v: 1,
      ops: [{ op: "set_bars", series: "candles", cols: { ts: [1, 2], open: [1], high: [1, 2], low: [1, 2], close: [1, 2] } }],
    };
    assert.equal(LwEnvelope.validateEnvelope(ragged).ok, false);
    const scalar = { v: 1, ops: [{ op: "update_bar", series: "candles", cols: { ts: 1, open: 1, high: 1, low: 1, close: 1 } }] };
    assert.equal(LwEnvelope.validateEnvelope(scalar).ok, false);
  });

  it("update_bar must carry single-element columns", () => {
    const two = { v: 1, ops: [{ op: "update_bar", series: "candles", cols: toCols(bars(1000, 2)) }] };
    assert.equal(LwEnvelope.validateEnvelope(two).ok, false);
  });

  it("replay is idempotent: mergeRows(log) then mergeRows(log) is stable", () => {
    const full = toCols(bars(1000, 4));
    const ops = [
      { op: "set_bars", series: "candles", cols: full },
      { op: "update_bar", series: "candles", cols: toCols([{ ts: 1240, open: 1, high: 2, low: 0.5, close: 1.5 }]) },
      { op: "update_bar", series: "candles", cols: toCols([{ ts: 1240, open: 1, high: 2.5, low: 0.5, close: 2 }]) },
    ];
    const once = LwEnvelope.mergeRows([], ops);
    const twice = LwEnvelope.mergeRows(once, ops);
    assert.equal(once.length, 5, "4 history bars + 1 forming bar");
    assert.deepEqual(twice, once);
    const times = once.map((r) => r.time);
    assert.deepEqual(times, [...new Set(times)].sort((a, b) => a - b));
    const forming = once[once.length - 1];
    assert.equal(forming.close, 2, "last tick wins on the forming bar");
  });
});
