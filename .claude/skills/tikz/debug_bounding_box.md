# Pass 6 — Debug Bounding-Box Verification

Dip-in reference. Loaded only when Passes 1–5 (`tikz_rules.md`) flagged collisions but the source-level fix isn't obvious from coordinate math — i.e., when you need to *see* where bounding boxes actually overlap on the page rather than reason about them.

This pass is unique to `/tikz`. It does not appear in `tikz_rules.md` because it is an audit technique, not a generation rule.

## The rule

**Do NOT attempt to visually inspect the PDF by "eyeballing."** Claude cannot reliably see TikZ collisions in rendered PDFs. Instead, force the bounding boxes to be drawn explicitly:

1. **Temporarily add red debug outlines** around every node:
   ```latex
   % DEBUG — add to preamble temporarily, remove before shipping
   \tikzset{every node/.append style={draw=red, very thin}}
   ```

2. **Compile and inspect**: overlapping bounding boxes are now visible as overlapping red rectangles. Collisions become structurally obvious rather than visually estimated.

3. **For each red-box overlap**: go back to the source, fix coordinates or dimensions, recompile.

4. **Remove the debug line** before declaring the audit complete.

This is your last-resort pass. If Passes 1–5 came back clean and a collision is still visible in the rendered PDF, this is how you localize it.
