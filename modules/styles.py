from dataclasses import asdict, dataclass, fields
import hashlib
import json
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class StyleSpec:
    name: str
    form: str
    palette: str
    costume: str
    environment: str
    mood: str

    def validate(self):
        for field in fields(self):
            value = getattr(self, field.name)
            limit = 80 if field.name == "name" else 1000
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"스타일 {field.name}: 1~{limit}자의 내용을 입력하세요.")

    @property
    def key(self):
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()


def style_from_dict(data):
    if not isinstance(data, dict) or set(data) != {f.name for f in fields(StyleSpec)}:
        raise ValueError("스타일 항목이 누락되었거나 올바르지 않습니다.")
    style = StyleSpec(**data)
    style.validate()
    return style


# Each reference is decomposed into independently assignable visual directions.
BUILTIN_STYLES = (
    StyleSpec("Ghibli · 지브리", "Soft rounded silhouettes, expressive understated faces and carefully observed everyday gestures", "Muted botanical greens, sky blues and warm domestic accents", "Simple layered everyday clothing with small handmade accessories", "Lived-in rural architecture, lush vegetation and intimate domestic details", "Gentle wonder, warmth and quiet companionship"),
    StyleSpec("월레스와 그로밋", "Hand-sculpted rounded forms, prominent brows and highly readable comic expressions", "Warm restrained colors with small bright accents", "Cozy knitted clothing and ingenious small mechanical accessories", "British domestic interiors and eccentric practical inventions", "Affectionate physical comedy and handmade stop-motion charm"),
    StyleSpec("슈퍼 마리오", "Compact rounded bodies, strong silhouette separation and bold readable facial features", "Saturated red, blue, yellow and green with clear color separation", "Simple rounded adventure clothing, caps and bold buttons", "Playful modular platforms, rounded landscape forms and oversized stylized vegetation modeled at miniature scale", "Cheerful energetic adventure and friendly theatrical poses"),
    StyleSpec("어벤져스", "Heroic silhouettes, readable team roles and decisive balanced stances", "Distinct hero-specific accent colors grounded by neutral structural tones", "Layered technical suits and segmented armor with restrained miniature panel detail", "Cinematic city dioramas and small-scale futuristic structures", "Team camaraderie, courage and purposeful heroic action"),
    StyleSpec("픽사", "Appealing three-dimensional stylization, expressive eyes and clear shape language", "Coordinated cinematic colors with a distinct accent per character", "Character-specific everyday outfits with readable material differences", "Story-focused environments with a few meaningful personal objects", "Warm emotional storytelling and expressive physical acting"),
    StyleSpec("레고", "Block-built silhouettes and simple articulated toy-like character forms", "Clean bright plastic colors with discrete color blocking", "Geometric modular outfit shapes and clip-like accessories", "Interlocking brick-built architecture and visible modular construction", "Playful construction-toy adventure"),
    StyleSpec("산리오", "Very simple rounded character shapes, small facial features and soft proportions", "Pastel pink, pale blue, lavender and soft white accents", "Small bows, simple dresses and tiny friendly accessories", "Compact cozy rooms, cafes and softly rounded decor", "Gentle friendship and calm everyday delight"),
    StyleSpec("포켓몬", "Distinct creature silhouettes, simplified anatomy and readable species-specific features", "A limited signature palette for each creature with clear markings", "Minimal creature accessories; trainer-like clothing only for explicitly human characters", "Small adventure habitats, paths and friendly natural landmarks", "Discovery, companionship and playful curiosity"),
    StyleSpec("실바니안 패밀리", "Small soft-looking animal figures with rounded bodies and simple gentle faces", "Soft natural colors with modest pastel fabric accents", "Tiny tailored domestic clothing and miniature household accessories", "Detailed cozy dollhouse rooms, gardens and neighborhood shops", "Nostalgic domestic warmth and family companionship"),
    StyleSpec("한국 동화 마을", "Friendly handmade character shapes and expressive restrained faces", "Balanced natural colors with small traditional multicolor accents", "Simplified hanbok-inspired layers and carefully scaled everyday accessories", "Miniature tiled roofs, low stone walls, courtyards and neighborhood details", "Neighborly warmth, gentle humor and everyday storytelling"),
)


def save_style(folder, style):
    style.validate()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{style.key}.json"
    payload = json.dumps(asdict(style), ensure_ascii=False, indent=2)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=folder,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        # Publish only a complete file so an interrupted write cannot corrupt a saved style.
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def delete_style(folder, style):
    style.validate()
    path = Path(folder) / f"{style.key}.json"
    try:
        path.unlink()
    except FileNotFoundError:
        raise ValueError("삭제할 사용자 스타일 파일을 찾을 수 없습니다.")


def replace_style(folder, old_style, new_style):
    old_style.validate()
    new_style.validate()
    folder = Path(folder)
    old_path = folder / f"{old_style.key}.json"
    if not old_path.is_file():
        raise ValueError("수정할 사용자 스타일 파일을 찾을 수 없습니다.")
    # Write the replacement first; keep the original intact if the new write fails.
    new_path = save_style(folder, new_style)
    if old_path != new_path:
        old_path.unlink()
    return new_path


def read_styles(folder):
    styles, errors = [], []
    for path in sorted(Path(folder).glob("*.json")):
        try:
            if path.stat().st_size > 32_000:
                raise ValueError("파일 크기 초과")
            styles.append(style_from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append(f"{path.name}: {exc}")
    return styles, errors
