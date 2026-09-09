from dataclasses import asdict, dataclass, fields
import json
import hashlib
from .styles import StyleSpec, style_from_dict


OPTIONS = {
    "medium": {"image": "이미지", "video": "영상"},
    "aspect": {"16:9": "16:9", "9:16": "9:16", "1:1": "1:1", "4:3": "4:3", "3:2": "3:2"},
    "scale": {"1:12": "1:12 · 대형 모형", "1:24": "1:24", "1:48": "1:48", "1:87": "1:87 · 철도 모형", "1:160": "1:160 · 초소형"},
    "detail": {"clean": "정돈된 디테일", "balanced": "균형 잡힌 디테일", "intricate": "정밀 디테일"},
    "material": {"mixed": "혼합 모형 재료", "resin": "레진", "wood": "목재", "metal": "금속", "paper": "종이", "clay": "점토"},
    "finish": {"matte": "무광", "satin": "반광", "gloss": "유광"},
    "wear": {"pristine": "새것", "subtle": "미세한 사용감", "aged": "오래된 흔적"},
    "lens": {"macro": "매크로", "tilt": "틸트 시프트", "standard": "표준 렌즈"},
    "focus": {"selective": "주 피사체 선택 초점", "deep": "장면 전체 선명"},
    "angle": {"eye": "모형 눈높이", "three_quarter": "사선 위에서", "top": "수직 탑뷰"},
    "composition": {"center": "중앙 집중", "thirds": "삼분할", "wide": "전체 디오라마"},
    "lighting": {"soft": "부드러운 스튜디오", "daylight": "창가 자연광", "golden": "따뜻한 사광", "night": "야간 실용 조명"},
    "background": {"table": "작업대와 베이스", "seamless": "단색 배경", "environment": "모형 환경 확장"},
    "cue": {"none": "없음", "coin": "동전 1개", "pencil": "연필 1개", "ruler": "눈금 기준물 1개"},
    "movement": {"locked": "고정 카메라", "push": "느린 전진", "slide": "느린 수평 이동", "orbit": "작은 원호 이동"},
    "blend_mode": {"accent": "주 스타일 + 보조 포인트", "split": "캐릭터 / 배경 분리", "fusion": "형태까지 융합"},
    "action_source": {"scene": "현재 장면 기준", "custom": "동작 직접 지정"},
}


def action_context(scene, subject):
    return hashlib.sha256(json.dumps([scene.strip(), subject.strip()], ensure_ascii=False).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CharacterSpec:
    identity: str
    appearance: str = ""
    expression: str = ""
    pose: str = ""
    accessory: str = ""
    placement: str = ""

    def validate(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, str) or len(value) > 800:
                raise ValueError("캐릭터 항목은 각각 800자 이내여야 합니다.")
        if not self.identity.strip():
            raise ValueError("각 캐릭터의 이름 또는 역할을 입력하세요.")


@dataclass(frozen=True)
class PromptParams:
    scene: str = ""
    subject: str = ""
    medium: str = "image"
    aspect: str = "16:9"
    scale: str = "1:87"
    detail: str = "balanced"
    material: str = "mixed"
    finish: str = "matte"
    wear: str = "subtle"
    lens: str = "macro"
    focus: str = "selective"
    angle: str = "three_quarter"
    composition: str = "thirds"
    lighting: str = "soft"
    background: str = "table"
    cue: str = "none"
    movement: str = "locked"
    duration: int = 6
    action: str = ""
    action_source: str = "scene"
    action_context: str = ""
    extra: str = ""
    negative: str = ""
    primary_style: StyleSpec | None = None
    secondary_style: StyleSpec | None = None
    blend_mode: str = "accent"
    secondary_weight: int = 30
    characters: tuple[CharacterSpec, ...] = ()

    def validate(self):
        if not isinstance(self.action_context, str) or (self.action_context and (len(self.action_context) != 64 or any(c not in "0123456789abcdef" for c in self.action_context))):
            raise ValueError("동작과 장면의 연결 정보가 올바르지 않습니다.")
        for style in (self.primary_style, self.secondary_style):
            if style is not None:
                if not isinstance(style, StyleSpec):
                    raise ValueError("올바른 스타일 설정이 아닙니다.")
                style.validate()
        if self.secondary_style and (not self.primary_style or self.secondary_style == self.primary_style):
            raise ValueError("보조 스타일은 주 스타일과 다른 스타일을 선택하세요.")
        if type(self.secondary_weight) is not int or not 10 <= self.secondary_weight <= 50:
            raise ValueError("보조 스타일 비중은 10~50의 정수여야 합니다.")
        if not isinstance(self.characters, tuple) or len(self.characters) > 6:
            raise ValueError("캐릭터는 최대 6개까지 설정할 수 있습니다.")
        for character in self.characters:
            if not isinstance(character, CharacterSpec):
                raise ValueError("올바른 캐릭터 설정이 아닙니다.")
            character.validate()
        for name, choices in OPTIONS.items():
            value = getattr(self, name)
            if not isinstance(value, str) or value not in choices:
                raise ValueError(f"{name}: 허용되지 않는 설정입니다.")
        for name, limit in {"scene": 6000, "subject": 500, "action": 2000, "extra": 3000, "negative": 2000}.items():
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError(f"{name}: 텍스트는 {limit}자 이내여야 합니다.")
        if type(self.duration) is not int or not 2 <= self.duration <= 30:
            raise ValueError("영상 길이는 2~30초 정수여야 합니다.")
        if not self.scene.strip() or not self.subject.strip():
            raise ValueError("장면과 주 피사체를 모두 입력하세요.")


def dump_project(params):
    params.validate()
    return json.dumps({"version": 4, "params": asdict(params)}, ensure_ascii=False, indent=2)


def load_project(raw):
    if len(raw) > 500_000:
        raise ValueError("작업 파일은 500KB 이하여야 합니다.")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("올바른 UTF-8 JSON 파일이 아닙니다.") from exc
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] not in (2, 3, 4):
        raise ValueError("지원하지 않는 프로젝트 형식입니다.")
    values = data.get("params")
    expected = {f.name for f in fields(PromptParams)}
    if data["version"] < 4:
        expected -= {"action_source", "action_context"}
    if data["version"] == 2:
        expected -= {"primary_style", "secondary_style", "blend_mode", "secondary_weight", "characters"}
    if not isinstance(values, dict) or set(values) != expected:
        raise ValueError("프로젝트 설정이 누락되었거나 알 수 없는 항목이 있습니다.")
    if data["version"] >= 3:
        for key in ("primary_style", "secondary_style"):
            if values[key] is not None:
                values[key] = style_from_dict(values[key])
        rows = values["characters"]
        if not isinstance(rows, list) or len(rows) > 6:
            raise ValueError("올바른 캐릭터 목록이 아닙니다.")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {f.name for f in fields(CharacterSpec)}:
                raise ValueError("캐릭터 설정이 누락되었거나 올바르지 않습니다.")
        values["characters"] = tuple(CharacterSpec(**row) for row in rows)
    params = PromptParams(**values)
    params.validate()
    return params


PRESETS = {
    "철도 디오라마": PromptParams(scene="작업대 위 산악 철도 디오라마. 작은 기차가 석조 터널 입구에 있고 선로 옆에 이끼와 자갈이 보인다.", subject="터널 입구의 소형 증기 기관차", material="mixed", scale="1:87"),
    "골목 상점": PromptParams(scene="작은 꽃집이 있는 골목 디오라마. 창가 화분과 나무 문, 작은 벽돌 바닥이 정교하게 배치되어 있다.", subject="꽃집 입구와 작은 화분", scale="1:24", lighting="golden", detail="intricate"),
    "목조 공방": PromptParams(scene="작은 목조 공방의 실내 모형. 작업대에 도구와 깎은 나무 조각이 정돈되어 있다.", subject="공방 중앙의 나무 작업대", scale="1:12", material="wood", background="environment", lighting="daylight"),
    "야간 도시": PromptParams(scene="야간 도시 블록의 미니어처. 작은 건물 창문에서 빛이 새어 나오고 도로에는 모형 자동차가 놓여 있다.", subject="조명이 켜진 모퉁이 건물", scale="1:160", lighting="night", composition="wide"),
}
