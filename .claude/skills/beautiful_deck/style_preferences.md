# Beautiful Deck Style Preferences

These are user-specific stylistic defaults, not rhetorical rules. Rhetorical choices still come from `rhetoric_of_decks.md`, audience, and content. Apply these preferences unless they conflict with the deck's audience-specific design or the user explicitly asks for a different style.

## Principle: Form From Function

Prefer visual elements that do a job. Decoration is welcome only when it also improves orientation, hierarchy, pacing, or comprehension.

## Progress Rule Under Frame Titles

Every content slide should have a thin horizontal separator between the assertion title and the slide body. Make it functional by turning it into a quiet progress indicator:

- Draw a low-opacity baseline across the full usable slide width.
- Overlay the same line at full opacity from left to right according to deck progress.
- At the start of the deck, only the low-opacity baseline is visible.
- At slide `NN/2`, roughly the left half is fully opaque.
- Near the end, almost the full line is fully opaque.
- Inherit color from the deck's core accent or frame-title color.
- Keep the treatment subtle; it should orient the speaker and audience without competing with content.

For Beamer, implement this in the frame-title template or a shared slide-header macro so it is automatic and consistent. Prefer a computed width such as `\insertframenumber/\inserttotalframenumber * \paperwidth` over manually edited per-slide values.

## Edge Accents

If a deck uses vertical bars, side rails, page-edge rules, or other side ornamentation, place those accents in the page gutter rather than at the content origin.

- In Beamer frame-title templates, prefer a negative x-offset from the text area for gutter accents. Page-coordinate overlays can be fragile when frames contain imported images; use page coordinates only after compiling representative image-heavy slides.
- For non-Beamer formats, or for tested Beamer background templates, page coordinates are fine.
- Do not let side ornamentation occupy the same coordinate region as slide body text, captions, code blocks, tables, figures, or wrapped frame titles.
- If the deck's style does not need side ornamentation, omit it. This is a stylistic option, not a required deck feature.

## Header Ornaments

Functional header ornaments should either live outside the content region or reserve the space they need.

- Treat title rules, progress lines, title bars, section indicators, and side accents as layout elements, not overlay decoration.
- If a header ornament sits near the title or slide body, reserve vertical or horizontal clearance for it in the frame-title template, slide header macro, or content margins.
- Do not draw header ornaments over the content coordinate system unless they are guaranteed to stay outside text, figures, tables, and code blocks.

## Screenshot and Image Placeholders

When a slide reserves space for a screenshot, UI capture, or other image, size the placeholder like the eventual image rather than like a text callout.

- If the image is the primary visual in a column, use the full available column width unless the slide's composition clearly calls for a smaller image.
- If vertical space is the binding constraint, use the full available content height and let width follow the image aspect ratio.
- Placeholder text should be secondary. Keep the note readable, but do not let the note determine the size of the image box.
- Make placeholders easy to replace after the user adds real files. Prefer a helper macro or commented line that already shows the intended syntax, such as `\includegraphics[width=\linewidth,height=4cm,keepaspectratio]{figures/example.png}` or, when `\graphicspath{{figures/}}` is set, `\includegraphics[width=\linewidth,height=4cm,keepaspectratio]{example.png}`.
- Add a brief source comment next to each placeholder naming the expected screenshot file or explaining that the user can replace only the filename.
- If the user prefers smaller image treatments, this section can be edited or deleted without changing the core skill.
