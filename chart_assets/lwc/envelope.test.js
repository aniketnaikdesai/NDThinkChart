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

// S-P25-2 (D67.2, P25-T1-AC1): the partial-marker directive's wire shape.
// It annotates one candle, so it carries no series and no cols; the page
// rejects any other shape (AR-P25-3 — one unknown op rejects the envelope).
describe("set_partial directive shape (P25-T1)", () => {
  const directive = (patch) =>
    Object.assign({ op: "set_partial", ts: 1763000000, partial: true }, patch);

  it("accepts {op, ts:int, partial:bool} with no series and no cols", () => {
    const op = directive();
    assert.equal("series" in op, false, "the directive carries no series");
    assert.equal("cols" in op, false, "the directive carries no cols");
    assert.equal(LwEnvelope.validateOp(op), null);
    assert.equal(
      LwEnvelope.validateEnvelope({ v: 1, ops: [op] }).ok,
      true,
      "a set_partial inside {v:1, ops:[...]} validates",
    );
    assert.equal(LwEnvelope.validateOp(directive({ partial: false })), null);
  });

  it("rejects a missing or non-integer ts", () => {
    const missing = directive();
    delete missing.ts;
    for (const bad of [missing, directive({ ts: 1.5 }), directive({ ts: "5" })]) {
      assert.notEqual(LwEnvelope.validateOp(bad), null, JSON.stringify(bad));
    }
  });

  it("rejects a non-boolean partial", () => {
    for (const partial of [1, "yes", null, undefined]) {
      const bad = directive({ partial });
      assert.notEqual(
        LwEnvelope.validateOp(bad),
        null,
        `partial ${JSON.stringify(partial)} must be rejected`,
      );
    }
  });

  it("rejects any series/cols key on the directive", () => {
    assert.notEqual(
      LwEnvelope.validateOp(
        directive({ series: "candles", cols: { ts: [1763000000], open: [1], high: [1], low: [1], close: [1] } }),
      ),
      null,
    );
    assert.notEqual(LwEnvelope.validateOp(directive({ series: "candles" })), null);
    assert.notEqual(LwEnvelope.validateOp(directive({ cols: {} })), null);
  });

  it("an unknown op kind still rejects the whole envelope", () => {
    const env = {
      v: 1,
      ops: [
        { op: "set_bars", series: "candles", cols: { ts: [1000], open: [1], high: [2], low: [0.5], close: [1.5] } },
        { op: "not_a_kind", series: "candles" },
      ],
    };
    assert.equal(LwEnvelope.validateEnvelope(env).ok, false);
  });
});

// S-P25-6 (D70, P25-T4): one whitespace rule for both branches — a row whose
// value slots are null is a placeholder, not a bar. Skipped on a replace,
// deleted (and only deleted) on an upsert; the fold stays replay-stable.
// This mirrors Python's apply_ops_to_bars.
describe("whitespace rows are not bars (P25-T4)", () => {
  const T0 = 1700000000;
  const T1 = T0 + 300;
  const T2 = T0 + 600;
  const realBar = (t, c) => ({ ts: t, open: c - 0.5, high: c + 1, low: c - 1, close: c });
  const wsBar = (t) => ({ ts: t, open: null, high: null, low: null, close: null });
  const candleCols = (rows) => ({
    ts: rows.map((b) => b.ts),
    open: rows.map((b) => b.open),
    high: rows.map((b) => b.high),
    low: rows.map((b) => b.low),
    close: rows.map((b) => b.close),
  });
  const times = (rows) => rows.map((r) => r.time);

  it("set_bars skips a whitespace row", () => {
    const ops = [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), wsBar(T1), realBar(T2, 12)]),
    }];
    assert.deepEqual(times(LwEnvelope.mergeRows([], ops)), [T0, T2]);
  });

  it("update_bar deletes the time a whitespace row names", () => {
    const seeded = LwEnvelope.mergeRows([], [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), realBar(T1, 11)]),
    }]);
    const once = LwEnvelope.mergeRows(seeded, [{
      op: "update_bar", series: "candles", cols: candleCols([wsBar(T1)]),
    }]);
    assert.deepEqual(times(once), [T0], "the existing bar is removed");
    const twice = LwEnvelope.mergeRows(once, [{
      op: "update_bar", series: "candles", cols: candleCols([wsBar(T1)]),
    }]);
    assert.deepEqual(times(twice), [T0], "deleting an absent time is a no-op");
    assert.deepEqual(twice, once, "replay stays stable");
  });

  it("a whitespace update never writes a null-valued row", () => {
    const ops = [{
      op: "update_bar", series: "candles", cols: candleCols([wsBar(T1)]),
    }];
    assert.deepEqual(LwEnvelope.mergeRows([], ops), []);
  });

  it("candles: open null with a real close is whitespace too", () => {
    const openGap = { ts: T1, open: null, high: null, low: null, close: 2.0 };
    const replaced = LwEnvelope.mergeRows([], [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), openGap, realBar(T2, 12)]),
    }]);
    assert.deepEqual(times(replaced), [T0, T2], "skipped on a replace");
    const seeded = LwEnvelope.mergeRows([], [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), realBar(T1, 11)]),
    }]);
    const after = LwEnvelope.mergeRows(seeded, [{
      op: "update_bar", series: "candles", cols: candleCols([openGap]),
    }]);
    assert.deepEqual(times(after), [T0], "deleted on an upsert");
  });

  it("candles: the ESC-127 close-null op is whitespace too", () => {
    // `{open: 1, close: None, high: 2.0, low: 0.5}` — the mirror shape.
    const closeGap = { ts: T1, open: 1.0, high: 2.0, low: 0.5, close: null };
    const replaced = LwEnvelope.mergeRows([], [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), closeGap, realBar(T2, 12)]),
    }]);
    assert.deepEqual(times(replaced), [T0, T2], "skipped on a replace");
    const seeded = LwEnvelope.mergeRows([], [{
      op: "set_bars", series: "candles",
      cols: candleCols([realBar(T0, 10), realBar(T1, 11)]),
    }]);
    const after = LwEnvelope.mergeRows(seeded, [{
      op: "update_bar", series: "candles", cols: candleCols([closeGap]),
    }]);
    assert.deepEqual(times(after), [T0], "deleted on an upsert");
  });

  it("exports the one predicate for chart.js to share (no second copy)", () => {
    assert.equal(typeof LwEnvelope.isWhitespaceRow, "function");
    assert.equal(LwEnvelope.isWhitespaceRow("candles", wsBar(T1)), true);
    assert.equal(
      LwEnvelope.isWhitespaceRow(
        "candles", { ts: T1, open: null, high: null, low: null, close: 2 }),
      true,
      "open null alone makes a candle row whitespace",
    );
    assert.equal(LwEnvelope.isWhitespaceRow("candles", realBar(T1, 10)), false);
    assert.equal(LwEnvelope.isWhitespaceRow("volume", { time: T1, value: null }), true);
  });

  it("volume applies the same rule (null value)", () => {
    const ops = [{
      op: "set_volume", series: "volume",
      cols: { ts: [T0, T1, T2], value: [5, null, 7] },
    }];
    assert.deepEqual(times(LwEnvelope.mergeRows([], ops)), [T0, T2]);
    const seeded = LwEnvelope.mergeRows([], [{
      op: "set_volume", series: "volume",
      cols: { ts: [T0, T1], value: [5, 6] },
    }]);
    const after = LwEnvelope.mergeRows(seeded, [{
      op: "update_bar", series: "volume", cols: { ts: [T1], value: [null] },
    }]);
    assert.deepEqual(times(after), [T0]);
  });
});
