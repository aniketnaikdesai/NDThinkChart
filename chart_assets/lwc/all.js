// all.js — the directory entry point for the node gate.
//
// `node --test chart_assets/lwc/` resolves a directory through this
// package.json's `main`, so before Q-9 that command executed only the
// envelope suite and the core-chart suite was never part of it. This file
// loads every suite in the tree, so the documented command actually runs
// them all; each suite stays runnable on its own file too.
require("./chart.test.js");
require("./envelope.test.js");
require("./volume_scale.test.js");
