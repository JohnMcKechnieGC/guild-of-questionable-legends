# Deck audit

36 distinct characters; six integer stats per card, all in 1–100.

| Stat | Min | Max | Mean | Median | Distinct values | Equal pairs / 630 |
|---|---:|---:|---:|---:|---:|---:|
| Weapon Skill | 10 | 100 | 54.9 | 55.0 | 19 | 21 (3.3%) |
| Strength | 15 | 95 | 52.2 | 45.0 | 16 | 27 (4.3%) |
| Toughness | 20 | 100 | 58.9 | 55.0 | 17 | 28 (4.4%) |
| Luck | 25 | 95 | 60.4 | 62.5 | 15 | 31 (4.9%) |
| Charisma | 15 | 95 | 60.6 | 65.0 | 17 | 24 (3.8%) |
| Intelligence | 15 | 100 | 64.9 | 70.0 | 18 | 26 (4.1%) |

These pair frequencies describe the starting deck, not the chance of a tied highest score during play.

| Character | Total / 600 | Best | Weakest |
|---|---:|---|---|
| Magnus the Overqualified | 510 | Weapon Skill 95 | Luck 70 |
| Velvet Vexwing | 485 | Strength 95 | Luck 50 |
| Dandelion Doomhoof | 465 | Charisma 95 | Intelligence 65 |
| Agnes Lastlaugh | 430 | Weapon Skill 100 | Strength 35 |
| Duke Puddleboots | 405 | Charisma 85 | Intelligence 45 |
| Baron Von Breadcrumb | 395 | Charisma 85 | Luck 30 |
| Sister Brickwork | 395 | Toughness 95 | Luck 35 |
| Felix Fineprint | 385 | Intelligence 95 | Weapon Skill 40 |
| Ernest Underbridge | 385 | Intelligence 90 | Charisma 35 |
| Captain Velcrobeard | 380 | Toughness 85 | Intelligence 40 |
| Thistle Quickpockets | 380 | Weapon Skill 85 | Toughness 45 |
| Dame Clatterspoon | 375 | Weapon Skill 90 | Intelligence 35 |
| Quilliam Quarrel | 375 | Weapon Skill 95 | Toughness 40 |
| Sir Trips-a-Lot | 365 | Luck 90 | Intelligence 30 |
| Countess Featherfax | 365 | Charisma 80 | Toughness 45 |
| Gronk the Delicate | 360 | Strength 95 | Intelligence 25 |
| Lady Mouldivine | 360 | Charisma 90 | Weapon Skill 30 |
| Saffron Scorchmitts | 360 | Intelligence 85 | Strength 40 |
| The Socktopus | 360 | Strength 80 | Charisma 25 |
| Madam Kettlehex | 355 | Intelligence 85 | Weapon Skill 35 |
| Polly Poltergeist | 345 | Toughness 75 | Weapon Skill 30 |
| Rattlebones McGee | 340 | Charisma 90 | Strength 30 |
| Nettle Nonesuch | 330 | Intelligence 85 | Strength 30 |
| Pip Pocketweather | 330 | Luck 95 | Strength 20 |
| Oracle Oopsabella | 330 | Intelligence 90 | Weapon Skill 25 |
| Pebble the Unmoved | 325 | Toughness 100 | Charisma 15 |
| Gertrude Geargrumble | 325 | Intelligence 100 | Strength 35 |
| Ambassador Slugworth | 325 | Charisma 95 | Weapon Skill 10 |
| Bogdan Bathwater | 320 | Strength 90 | Charisma 25 |
| Brother Bumbles | 320 | Luck 80 | Strength 20 |
| Marmalade the Dread | 305 | Toughness 90 | Charisma 20 |
| Bixby Buttonbane | 300 | Intelligence 90 | Strength 25 |
| Professor Fizzlewick | 270 | Intelligence 95 | Weapon Skill 20 |
| Wobblewort the Beige | 230 | Intelligence 75 | Weapon Skill 20 |
| Snivel the Almost Brave | 220 | Luck 85 | Weapon Skill 15 |
| Turnip the Unready | 160 | Luck 70 | Weapon Skill 10 |

All 36 unique portrait BLOBs decode successfully at 600×800. The application reads these bytes from SQLite.
