from dataclasses import dataclass

from .templates import PromptParams, action_context


@dataclass(frozen=True)
class PromptResult:
    positive: str
    negative: str
    combined: str
    notes: tuple


def style_blocks(p):
    a, b = p.primary_style, p.secondary_style
    if a is None:
        return []
    reference = f"Primary visual reference: {a.name}."
    if b is None:
        direction = (
            f"Form: {a.form}. Palette: {a.palette}. Costume: {a.costume}. "
            f"Environment: {a.environment}. Mood: {a.mood}."
        )
    else:
        reference += f" Secondary visual reference: {b.name}."
        if p.blend_mode == "split":
            direction = (
                f"CHARACTERS use only the primary reference: form {a.form}; "
                f"palette {a.palette}; costume {a.costume}; acting mood {a.mood}. "
                f"ENVIRONMENT uses only the secondary reference: {b.environment}; "
                f"palette {b.palette}; atmosphere {b.mood}. "
                "Keep character and environment style assignments separate, joined by "
                "the selected lighting and physical miniature scale."
            )
        elif p.blend_mode == "accent":
            direction = (
                f"Primary form is locked: {a.form}. Primary palette: {a.palette}. "
                f"Primary costume construction: {a.costume}. Primary environment: "
                f"{a.environment}. Primary mood: {a.mood}. Use the secondary reference "
                f"only as accents with an approximate {p.secondary_weight}% visual "
                f"emphasis: palette accents {b.palette}; small costume motifs {b.costume}. "
                "Do not change primary anatomy, silhouette, setting or acting style with "
                "the accent reference."
            )
        else:
            direction = (
                f"Unified design with approximately {100 - p.secondary_weight}% primary "
                f"and {p.secondary_weight}% secondary visual influence. Primary silhouette "
                f"and anatomy remain the anchor: {a.form}. Adapt compatible secondary "
                f"shape details: {b.form}. Primary palette {a.palette}; secondary color "
                f"accents {b.palette}. Keep one coherent outfit: primary construction "
                f"{a.costume}; compatible secondary motifs {b.costume}. Preserve the "
                f"primary environment layout {a.environment}; add a few secondary set "
                f"motifs {b.environment}. Primary mood {a.mood}; secondary emotional "
                f"accent {b.mood}. If anatomy or shapes conflict, retain the primary "
                "design. Do not splice two bodies, faces or costumes together."
            )
    return [
        (
            "STYLE DIRECTION",
            reference
            + " "
            + direction
            + " Translate these design traits into the selected physical model materials. "
            "Keep the user's scene and explicit character identity; do not automatically "
            "introduce franchise characters, scenery or props that replace the requested subject.",
        )
    ]


def character_blocks(p):
    if not p.characters:
        return []
    lines = [
        f"Exactly {len(p.characters)} featured miniature characters. Each numbered entry "
        "is one separate figure; no additional featured cast."
    ]
    labels = {
        "appearance": "Identity anchors",
        "expression": "Expression and gaze",
        "pose": "Pose",
        "accessory": "Assigned accessory",
        "placement": "Position and relationship",
    }
    for index, character in enumerate(p.characters, 1):
        lines.append(f"Character {index}: {character.identity.strip()}.")
        for field, label in labels.items():
            value = getattr(character, field).strip()
            if value:
                lines.append(f"  {label}: {value}")
    lines.append(
        "Preserve each character's own face, silhouette, costume colors and assigned "
        "accessories. Style changes must not swap identities, transfer clothing between "
        "figures or change their count. Model all figures at the scene scale; stylized "
        "proportions do not imply life-size people. Keep faces and essential gestures "
        "unobstructed, with clear silhouette separation and supported feet or explicitly "
        "specified support."
    )
    if len(p.characters) > 1:
        lines.append(
            "Arrange featured faces within a shared readable focus region; do not sacrifice "
            "a named character to background blur. Preserve their specified relative "
            "positions and interactions."
        )
    if p.medium == "video":
        lines.append(
            "Across frames, lock each character's facial design, body proportions, costume, "
            "accessory ownership and screen-side relationship. Animate only the requested "
            "action; maintain contact with held objects and avoid limb or face morphing."
        )
    return [("CHARACTER CAST", "\n".join(lines))]


MATERIAL = {
    "mixed": "Use appropriate model materials per object: painted resin, fine wood and thin metal; preserve their distinct surface responses.",
    "resin": "Primary modeled surfaces are cast resin with fine molded edges and scale-appropriate thickness.",
    "wood": "Primary modeled surfaces are fine-grained wood; keep grain and joinery proportionate to miniature size.",
    "metal": "Primary modeled surfaces are thin formed metal with precise joints and fine machined edges.",
    "paper": "Primary modeled surfaces are layered paper and card with precise folds and thin cut edges.",
    "clay": "Primary modeled surfaces are sculpted clay with fine tool marks and controlled contours.",
}
FINISH = {
    "matte": "Matte finish on painted surfaces; diffuse reflection without flattening glass or bare metal.",
    "satin": "Satin finish on painted surfaces with restrained soft highlights; retain material-specific reflections.",
    "gloss": "Gloss finish on coated surfaces with controlled highlights; uncoated materials retain their own finish.",
}
DETAIL = {
    "clean": "Sparse, deliberate small props and clean readable forms; avoid clutter.",
    "balanced": "Moderate secondary props, fine joints and restrained surface variation; keep the main subject dominant.",
    "intricate": "Precisely constructed joints, layered small props and material-specific microtexture; detail density must not obscure the subject.",
}
WEAR = {
    "pristine": "Pristine newly made surfaces; no dirt, scratches, chips or weathering.",
    "subtle": "Restrained wear only at plausible contact points; no oversized dust or scratches.",
    "aged": "Localized faded paint, fine chips and accumulated wear appropriate to each material; no uniform damage layer.",
}
LENS = {
    "macro": "Close-focus macro photography with controlled perspective.",
    "tilt": "Tilt-shift optics with a deliberate focus plane through the main subject; avoid an arbitrary horizontal blur band.",
    "standard": "Natural standard-lens perspective at miniature working distance, without wide-angle distortion.",
}
FOCUS = {
    "selective": "Selective depth of field: keep essential subject features sharp, with gradual optical falloff into the background.",
    "deep": "Extended depth of field across the modeled scene; retain readable foreground and background, without selective blur.",
}
ANGLE = {
    "eye": "Camera at the modeled subject's eye level.",
    "three_quarter": "Elevated three-quarter view revealing volume and miniature construction.",
    "top": "True overhead view with the camera perpendicular to the base.",
}
COMPOSITION = {
    "center": "Center the primary subject with balanced surrounding space.",
    "thirds": "Place the primary subject near a rule-of-thirds intersection; keep its full defining silhouette inside frame.",
    "wide": "Show the entire modeled arrangement with breathing room around its outer edges.",
}
LIGHTING = {
    "soft": "Large diffused studio source relative to the model; gentle fill, localized contact shadows and controlled highlights.",
    "daylight": "Soft window daylight illuminating the physical model, with coherent directional shadows and neutral material colors.",
    "golden": "Warm low-angle key light with soft neutral fill; preserve surface colors and consistent shadow direction.",
    "night": "Tiny practical lights in the miniature with low-level fill; retain shadow detail, restrained bloom and believable light falloff.",
}
BACKGROUND = {
    "table": "A physical diorama base rests on a tabletop; show a restrained base edge without distracting workshop clutter.",
    "seamless": "A clean seamless neutral studio background, without a visible tabletop edge or additional background props.",
    "environment": "Continue the modeled environment behind the subject at the same scale; no full-size landscape or distant atmospheric haze.",
}
CUE = {
    "none": "No external reference objects, human hands or fingers; communicate miniature scale through construction, textures and optics.",
    "coin": "Exactly one real-size plain unbranded coin near the frame edge, outside the modeled world; no readable inscriptions. Keep it secondary to the model.",
    "pencil": "Exactly one real-size unbranded pencil near the frame edge, outside the modeled world; no lettering. Keep it secondary to the model.",
    "ruler": "Exactly one real-size ruler fragment near the frame edge, outside the modeled world, with tick marks only and no numerals. Keep it secondary to the model.",
}
MOVEMENT = {
    "locked": "Locked camera with no pan, zoom, shake or cuts.",
    "push": "A slow, smooth short forward camera move; preserve the subject's framing.",
    "slide": "A slow, smooth short lateral camera move with gentle parallax.",
    "orbit": "A slow small-arc camera move around the subject, without a full rotation.",
}


def build_prompt(params: PromptParams) -> PromptResult:
    p = params
    p.validate()
    use_custom_action = (
        p.action_source == "custom"
        and bool(p.action.strip())
        and p.action_context == action_context(p.scene, p.subject)
    )
    blocks = [
        ("OUTPUT", f"{'Still image' if p.medium == 'image' else 'Video'}, aspect ratio {p.aspect}."),
        (
            "DIRECTION PRIORITY",
            "Preserve the explicit scene, subject and character identity first; then the "
            "selected miniature scale, materials and camera settings; apply style references "
            "only within those constraints. Style references guide visual design rather than "
            "adding an unrelated scene. Omit optional style motifs when they conflict with "
            "explicit requirements.",
        ),
        ("SCENE", p.scene.strip()),
        (
            "PRIMARY SUBJECT",
            p.subject.strip() + ". Preserve the subject's silhouette and recognizable construction.",
        ),
        (
            "SCALE",
            f"A physically built {p.scale} scale miniature diorama, photographed as a small "
            "real object. Keep all modeled architecture, figures, props and surface textures "
            "at this consistent scale. Show fine construction edges and small contact shadows; "
            "do not depict a life-size scene with blur merely added.",
        ),
        ("MATERIAL", MATERIAL[p.material] + " " + FINISH[p.finish]),
        ("DETAIL", DETAIL[p.detail] + " " + WEAR[p.wear]),
        ("CAMERA", LENS[p.lens] + " " + FOCUS[p.focus]),
        ("COMPOSITION", ANGLE[p.angle] + " " + COMPOSITION[p.composition]),
        ("LIGHTING", LIGHTING[p.lighting]),
        ("BACKGROUND", BACKGROUND[p.background]),
        ("SCALE REFERENCE", CUE[p.cue]),
    ]
    blocks[4:4] = character_blocks(p) + style_blocks(p)

    if p.medium == "video":
        default_action = (
            "Follow the events described in SCENE in their stated order, preserving the "
            "specified participants and their actions. Do not substitute actions from an "
            "unrelated scene. If SCENE specifies no action, do not invent one."
        )
        action = p.action.strip() if use_custom_action else default_action
        motion = (
            f"Duration: {p.duration} seconds. One continuous shot. {MOVEMENT[p.movement]} "
            f"Subject action: {action} Keep the camera instructions separate from subject "
            "motion: a locked camera does not freeze the subjects. Maintain geometry, scale, "
            "materials and lighting across every frame; allow entrances, exits and occlusion "
            "required by SCENE without spontaneous duplication. Use continuous physically "
            "coherent motion, with stable focus and no flicker."
        )
        blocks.append(("MOTION", motion))

    if p.extra.strip():
        blocks.append(("ADDITIONAL DIRECTION", p.extra.strip()))

    negatives = []
    if p.use_default_negative:
        negatives.append(
            "Life-size scene, inconsistent miniature scale, oversized surface texture, warped "
            "geometry, duplicated main subjects, floating props, unreadable subject, excessive "
            "blur, blown highlights, watermark, logo, readable lettering, full-size people or hands"
        )
        if p.characters:
            negatives.append(
                "extra featured characters, identity swaps, merged faces or bodies, unintended "
                "extra limbs, detached accessories, obscured featured faces"
            )
        if p.secondary_style:
            negatives.append(
                "unrelated style collage, incompatible anatomy, split-face style fusion"
            )
        if p.wear == "pristine":
            negatives.append("dirt, scratches, chipped paint, weathering")
        if p.focus == "deep":
            negatives.append("shallow depth of field, selective blur")
        if p.medium == "video":
            negatives.append(
                "temporal flicker, morphing, teleportation, frame-to-frame object changes, "
                "jump cuts, focus hunting"
            )
    if p.negative.strip():
        negatives.append(p.negative.strip())

    negative = ", ".join(negatives)
    positive = "\n\n".join(f"{heading}\n{text}" for heading, text in blocks)
    combined = positive + ("\n\nAVOID\n" + negative if negative else "")
    notes = [
        "자유 입력은 원문 그대로 반영됩니다. 자동 번역이나 AI 의미 검증은 수행하지 않습니다."
    ]
    if not p.use_default_negative:
        notes.append(
            "기본 제외 조건을 사용하지 않았습니다. 사용자가 입력한 제외 조건만 적용됩니다."
        )
    if p.medium == "video" and p.action.strip() and not use_custom_action:
        notes.append(
            "현재 장면에 연결되지 않은 별도 동작은 제외하고, 장면에 적힌 사건 순서를 사용했습니다."
        )
    if p.secondary_style and p.blend_mode != "split":
        notes.append(
            "혼합 비중은 시각적 강조 지시이며, 생성 모델의 정확한 수치 재현을 보장하지 않습니다."
        )
    if len(p.characters) > 1 and p.focus == "selective":
        notes.append("다중 캐릭터의 얼굴을 같은 초점 영역에 배치하도록 보완했습니다.")
    if p.characters and p.angle == "top":
        notes.append(
            "수직 탑뷰에서는 얼굴 표정이 덜 보일 수 있습니다. 표정이 중요하면 모형 눈높이나 "
            "사선 구도를 검토하세요."
        )
    if p.extra.strip() or p.negative.strip():
        notes.append(
            "추가 지시와 제외 조건이 선택한 설정 또는 장면 내용과 충돌하지 않는지 확인하세요."
        )
    return PromptResult(positive, negative, combined, tuple(notes))
