# EFCLib v1 engineering briefing: source

Source for [`../EFCLib_v1_Engineering_Briefing.pptx`](../EFCLib_v1_Engineering_Briefing.pptx), a 26-slide deck for engineers on the EFCLib v1 styles, symbols, device templates, value and loop templates, and dynamic windows. Each slide has detailed speaker notes.

| File | What it is |
|---|---|
| `build_deck.js` | pptxgenjs script that builds the deck |
| `notes.json` | Speaker notes, keyed by slide number |
| `img/` | Dynamic-window and screen-shell renders of the `steward/previews/` mockups, plus symbol crops from `docs/previews/templates/_Demo.png` |

The template images come straight from `docs/previews/` and `steward/previews/renders/`, so re-render those first if the templates change.

Rebuild (needs Node and `pptxgenjs`):

```bash
cd docs/presentations/efclib-v1-source
node build_deck.js          # writes ../EFCLib_v1_Engineering_Briefing.pptx
```

Set `APPLY_THEME` to the pptx skill's `scripts/apply_theme.js` to write the EFC theme colors into the file; without it the theme keeps Office's default colors (slide colors set directly are unaffected).

Some dynamic-window images show the approved mockups, which are ahead of the build in places (bypass duration presets, trend pause/live, process-value shelving). The slides and the CHECK paragraphs in the notes say which parts are built.
