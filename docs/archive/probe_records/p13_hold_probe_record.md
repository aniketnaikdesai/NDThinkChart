# P13 hold-count verification record (D49.5 probe — P13-T5)

Offscreen lifecycle probe (`tests/test_p13_hold_probe.py`,
`QT_QPA_PLATFORM=offscreen`): main-chart load, main-chart
same-symbol reload, pop-out attach, pop-out close, and a zero-owner
case. Hold count is `TickerSession._rt_holders`; active owners are
the session's attached views plus the alarm monitor when it holds
the session. No production file was modified by this probe.

## Step counts

| step | hold count | active owners | holds − owners | note |
| --- | --- | --- | --- | --- |
| initial-load | 1 | 1 | 0 | main chart only |
| same-symbol-reload | 1 | 1 | 0 | coalesced into running wave |
| popout-attach | 2 | 2 | 0 | main chart + one pop-out |
| popout-close | 1 | 1 | 0 | main chart only again |
| zero-owner | 0 | 0 | 0 | session torn down |

## Verdict

Verdict: no lasting effect

The hold count tracked the active-owner count at every live step
and the zero-owner case returned the count to zero, so no excess
outlives the step that created it.
