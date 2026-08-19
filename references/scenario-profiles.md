# Scenario Profiles

Use this reference when the brief is broader than a single cinematic frame, local edit, or styleboard. Select one primary `scenario_profile`; let secondary needs appear as constraints instead of stacking several profiles.

## Routing Order

```text
intended use -> audience effect -> primary scenario -> genre family ->
scene archetypes -> aesthetic family -> capture/render method -> quality gate
```

The scenario answers **what the image must accomplish**. It does not determine the style by itself.

## Genre Families

Canonical `genre_family` values are:

- `drama`, `romance`, `comedy`, `thriller`, `horror`, `crime_noir`;
- `action_adventure`, `fantasy_mythic`, `science_fiction`, `historical_period`;
- `documentary`, `children_family`, `commercial_editorial`, `experimental_surreal`;
- `auto`, or `custom` with a required `custom_genre` description.

Genre sets audience and story expectations. It does not select medium, color pipeline, camera, or aesthetic automatically.

## Story and Performance

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `narrative_scene` | film stills, story beats, reactions, decisions | visible event, relationship pressure, frozen moment, viewer task | poster-like simultaneous showcase |
| `character_portrait` | identity, casting, character reveal, profile art | face/body truth, silhouette, gaze, hands, wardrobe hierarchy, background role | generic beauty portrait or costume overload |
| `relationship_performance` | dialogue, distance, power, intimacy, conflict | eyelines, proximity, barriers, touch, shared objects, asymmetric attention | two isolated portraits in one frame |
| `action_choreography` | fights, chases, sports, dance, stunt concepts | geography, action phase, contact proof, screen direction, readable endpoint | chaotic camera and global motion blur |

## Campaign, Brand, and Editorial

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `key_art_campaign` | campaign hero, cover, launch image, title-led promotion | asset hierarchy, focal promise, copy space, crop variants, brand-safe spectacle | story ambiguity or equal-weight montage |
| `brand_identity` | visual systems, packaging families, brand worlds | color ownership, shape language, material family, typography role, repetition | logo pasted onto unrelated imagery |
| `social_content` | feed posts, group cards, thumbnails, vertical campaigns | phone-size hierarchy, concise text, safe margins, one immediate message | tiny text and desktop-only detail |
| `event_experience` | exhibitions, festivals, stage screens, installations | venue scale, viewing distance, environmental integration, wayfinding hierarchy | flat poster logic applied to space |

## Product, Fashion, and Lifestyle

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `product_tabletop` | product hero, catalog, macro, packaging, still life | silhouette, contact shadow, label truth, material response, scale reference | global gloss and floating product |
| `fashion_beauty` | couture, streetwear, beauty close-up, lookbook | garment silhouette, fabric behavior, pose, skin/hair treatment, styling density | e-commerce pose or plastic skin |
| `food_still_life` | menu hero, ingredient story, beverage, culinary editorial | freshness, steam/condensation, cut surface, vessel, appetite light, mess control | fake wetness, plastic texture, impossible food structure |

## Space, Environment, and Designed Worlds

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `architecture_interior` | buildings, interiors, hospitality, retail, spatial concepts | massing, circulation, human scale, daylight path, material junctions | empty render without use or scale |
| `landscape_environment` | natural worlds, cities, terrain, weather, establishing art | geography, biome, depth, weather causality, paths, human trace | random scenic wallpaper |
| `vehicle_mecha` | vehicles, machines, weapons, hard-surface concepts | function, silhouette, articulation, access, wear zones, scale | meaningless panels and decorative greebles |
| `creature_design` | animals, monsters, aliens, mythic beings | anatomy, locomotion, ecology, material/skin system, scale, behavior | collage anatomy or unsupported ornament |
| `game_asset` | key art, environment concepts, props, icons, asset families | gameplay readability, faction language, silhouette, state variants, camera context | promotional detail that fails in actual use |

## Knowledge, History, and Interfaces

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `historical_documentary` | period reconstruction, archive-led scenes, social observation | date/place anchors, source separation, ordinary material truth, uncertainty labels | costume fantasy presented as fact |
| `scientific_educational` | field guides, mechanisms, instructional images, research figures | factual structure, label accuracy, scale, arrows, section hierarchy | decorative science with false relationships |
| `editorial_infographic` | explainers, diagrams, reports, visual essays | information argument, reading order, exact text, restrained palette, whitespace | attractive poster with unusable data |
| `interface_mockup` | app screens, dashboards, diegetic UI, device concepts | information architecture, state, affordance, density, system consistency | concept-art UI without usable structure |

## Experimental

| Profile | Use for | Decisive controls | Common failure |
| --- | --- | --- | --- |
| `experimental_art` | mixed media, abstract systems, projection, scan, generative form | declared transformation rule, material or signal ownership, repetition and variation | random effects with no governing rule |

## Scene Archetypes

`scene_archetypes` is an open list limited to three primary entries. Useful families include:

- intimate interior, public architecture, street/urban layer, landscape/wilderness;
- aerial world, underwater, orbital/space, micro-world;
- studio tabletop, stage/performance, workshop/lab, retail/hospitality;
- archival reconstruction, abstract graphic field, virtual/LED stage, miniature set.

Describe the actual place after selecting the archetype. “Street/urban layer” is not permission to add rain, neon, graffiti, or crowds.

## Scenario Gate

- One profile clearly owns success.
- Delivery context and audience effect are explicit when they change hierarchy.
- Scene archetypes describe spatial function, not decoration.
- The selected aesthetic and capture/render method support the scenario.
- The final prompt includes only scenario-specific controls that can be visually checked.
