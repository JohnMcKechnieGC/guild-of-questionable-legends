# Original portrait production

All 36 portraits were created during development with Codex's built-in `image_gen.imagegen` capability, one distinct generation call for each character. No external card artwork or existing character designs were supplied. The PNG sources are in `assets/portraits/gql-01.png` through `gql-36.png`. The playable versions are center-cropped to 600×800 WebP and stored as actual BLOBs in `data/deck.sqlite3`.

The complete final prompt for portraits 02–36 is the shared prefix below, followed by the corresponding `name`, a period and a space, then the `portrait` field in [deck.json](deck.json):

> Use case: illustration-story. ONE original fantasy character portrait for Guild of Questionable Legends. Playful hand-painted storybook fantasy, expressive face, crisp ink and gouache texture, warm amber light, muted teal shadows, richly colored but readable. Vertical 3:4 portrait, centered waist-up character, visual gag clearly visible, atmospheric simple fantasy backdrop. Single illustration filling canvas. No text, letters, numbers, logos, signatures, watermarks, panels or card borders. Original design. Character:

Portrait 01 used this full prompt:

> Use case: illustration-story. Create ONE original fantasy character portrait for the game Guild of Questionable Legends. Character: Bixby Buttonbane, a fussy green goblin quartermaster with round spectacles, auditing a dragon hoard using an abacus; his overflowing payment purse contains only cursed glowing buttons. Visual gag: a tiny angry button biting his cuff. Style: playful hand-painted storybook fantasy, expressive face, crisp ink and gouache texture, warm amber light, muted teal shadows, richly colored but readable. Consistent composition: vertical 3:4 portrait, centered waist-up character with the gag visible, atmospheric simple fantasy workshop backdrop. Single illustration filling the entire canvas, no text, letters, numbers, logos, signatures, watermarks, panels or card borders. Original design.

Names, biographies, stat values, rules wording and the teal/amber guild presentation were authored for this project. The source manifest is a development artifact; the Deck Editor is the supported way to change the live database without code.
