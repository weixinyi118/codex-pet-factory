# Adaptive QA Policy

## Deterministic Hard Gates

- Atlas dimensions are `1536x2288`; cell size is `192x208`; final format is v2.
- Used cells are non-empty; unused standard cells are fully transparent.
- Fully transparent pixels contain no RGB residue after the single final despill pass.
- Frame counts match the row contract.
- Look-row pose groups are separated, ordered, registered at one shared scale, and clear of cell edges.

## Visual Hard Gates

- The same identity, face, material, hair, clothing, palette, lighting, props, and body proportions persist across all rows.
- Standard states read correctly at normal pet size.
- No detached effects, shadows, guide pixels, text, logos, or scenery remain.
- Up, screen-right, down, and screen-left are unmistakable without labels.
- The 16 directions form a clockwise loop without reversal or a visible row-boundary identity jump.

## Automatic Consistency Thresholds

Treat the consistency script as a triage gate, not a substitute for visual review.

- Fail rows 9 and 10 when median subject height differs by more than 12%.
- Fail rows 9 and 10 when median luminance differs by more than 14 points or mean RGB distance exceeds 18.
- Warn when a look row differs from idle by more than 12 luminance points or 15 RGB-distance points.
- Warn when any row's within-row luminance spread exceeds 24 points.
- Review warnings against the contact sheet; accept only when caused by intentional pose exposure rather than identity or grade drift.

## Blind Review Escalation

Fast mode starts with one blind cardinal reviewer. Escalate to three isolated reviewers when:

- any cardinal is ambiguous or wrong;
- labeled review and blind review disagree;
- a diagonal appears in the wrong quadrant;
- the loop appears to reverse;
- a repair changed direction mechanics.

An ambiguous non-cardinal direction may remain a recorded warning when labeled full-loop review confirms the correct quadrant and no reversal. Never override a cardinal failure.

## Repair Scope

- Repair one complete standard row for standard-state failures.
- Repair one complete look row for direction, identity, or continuity failures.
- Do not repair a single look cell.
- Rerun extraction and edge checks for the repaired row, then rerun final assembly, consistency, and visual QA.
