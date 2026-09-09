from dataclasses import asdict, fields
import os
from pathlib import Path
import streamlit as st
from modules.templates import OPTIONS, PRESETS, PromptParams, CharacterSpec, dump_project, load_project, action_context
from modules.compiler import build_prompt
from modules.styles import BUILTIN_STYLES, StyleSpec, read_styles, save_style


st.set_page_config(page_title="Hangeul Miniature", page_icon="🔎", layout="wide")


def apply_params(params):
    for field in fields(params):
        if field.name not in {"primary_style", "secondary_style", "characters"}:
            st.session_state[field.name] = getattr(params, field.name)
    for role in ("primary", "secondary"):
        style = getattr(params, f"{role}_style")
        st.session_state[f"{role}_choice"] = style.key if style else "none"
        if style:
            st.session_state.setdefault("imported_styles", {})[style.key] = style
    st.session_state["character_count"] = len(params.characters)
    for i in range(6):
        character = params.characters[i] if i < len(params.characters) else CharacterSpec("")
        for name, value in asdict(character).items():
            st.session_state[f"char_{i}_{name}"] = value


def select(name, label):
    return st.selectbox(label, list(OPTIONS[name]), format_func=OPTIONS[name].get, key=name)


def scene_changed():
    if st.session_state.get("action", "").strip():
        st.session_state["motion_notice"] = "장면 또는 주 피사체가 변경되어 이전 별도 동작을 초기화했습니다."
    st.session_state["action"] = ""
    st.session_state["action_source"] = "scene"
    st.session_state["action_context"] = ""


def bind_action():
    st.session_state["action_context"] = action_context(st.session_state["scene"], st.session_state["subject"])


def main():
    defaults = PromptParams()
    for field in fields(defaults):
        st.session_state.setdefault(field.name, getattr(defaults, field.name))
    st.session_state.setdefault("primary_choice", "none")
    st.session_state.setdefault("secondary_choice", "none")
    st.session_state.setdefault("character_count", 0)
    st.session_state.setdefault("imported_styles", {})
    style_folder = Path(os.environ.get("MINI1_STYLE_DIR", str(Path(__file__).parent / "data" / "styles")))

    with st.sidebar:
        st.subheader("작업")
        preset = st.selectbox("장면 프리셋", list(PRESETS))
        st.button("프리셋 적용", on_click=apply_params, args=(PRESETS[preset],), use_container_width=True)
        st.button("새 작업", on_click=apply_params, args=(PromptParams(),), use_container_width=True)
        uploaded = st.file_uploader("저장한 작업 파일", type=["json"])
        if st.button("작업 불러오기", disabled=uploaded is None, use_container_width=True):
            try:
                apply_params(load_project(uploaded.getvalue()))
                st.success("작업을 불러왔습니다.")
            except ValueError as exc:
                st.error(str(exc))
        with st.expander("내 스타일 추가"):
            with st.form("new_style", clear_on_submit=False):
                name = st.text_input("스타일 이름", max_chars=80, key="new_style_name")
                form = st.text_area("형태·비율", max_chars=1000, key="new_style_form")
                palette = st.text_area("색감", max_chars=1000, key="new_style_palette")
                costume = st.text_area("의상·소품", max_chars=1000, key="new_style_costume")
                environment = st.text_area("배경 특징", max_chars=1000, key="new_style_environment")
                mood = st.text_area("분위기·감정", max_chars=1000, key="new_style_mood")
                if st.form_submit_button("내 스타일 저장"):
                    try:
                        style = StyleSpec(name.strip(), form.strip(), palette.strip(), costume.strip(), environment.strip(), mood.strip())
                        save_style(style_folder, style)
                        st.success("스타일을 저장했습니다.")
                    except (ValueError, OSError) as exc:
                        st.error(f"저장하지 못했습니다: {exc}")

    custom, errors = read_styles(style_folder)
    catalog = {style.key: style for style in (*BUILTIN_STYLES, *custom, *st.session_state["imported_styles"].values())}
    for error in errors:
        st.sidebar.warning(f"읽지 못한 스타일 파일: {error}")

    st.title("Hangeul Miniature")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.subheader("장면 설정")
        a, b = st.columns(2)
        with a:
            select("medium", "출력 유형")
        with b:
            select("aspect", "화면 비율")
        st.text_area("장면", key="scene", height=130, max_chars=6000, placeholder="공간, 배경, 소품과 주 피사체의 관계", on_change=scene_changed)
        st.text_input("주 피사체", key="subject", max_chars=500, placeholder="선명하게 보여야 하는 대상", on_change=scene_changed)
        motion_notice = st.empty()
        if "motion_notice" in st.session_state:
            motion_notice.info(st.session_state.pop("motion_notice"))
        st.selectbox("영상 동작 기준", list(OPTIONS["action_source"]), format_func=OPTIONS["action_source"].get, key="action_source", disabled=st.session_state.medium != "video", on_change=bind_action)
        st.subheader("스타일 조합")
        a, b = st.columns(2)
        labels = {"none": "없음", **{key: style.name for key, style in catalog.items()}}
        with a:
            st.selectbox("주 스타일", list(labels), format_func=labels.get, key="primary_choice")
        with b:
            secondary_labels = {key: label for key, label in labels.items() if key == "none" or key != st.session_state.primary_choice}
            if st.session_state.primary_choice == "none" or st.session_state.secondary_choice not in secondary_labels:
                st.session_state.secondary_choice = "none"
            st.selectbox("보조 스타일", list(secondary_labels), format_func=secondary_labels.get, key="secondary_choice", disabled=st.session_state.primary_choice == "none")
        select("blend_mode", "혼합 방식")
        st.slider("보조 스타일 비중 (%)", 10, 50, key="secondary_weight", disabled=st.session_state.secondary_choice == "none" or st.session_state.blend_mode == "split")
        with st.expander("선택한 스타일 구성"):
            for role, key in (("주 스타일", st.session_state.primary_choice), ("보조 스타일", st.session_state.secondary_choice)):
                if key in catalog:
                    style = catalog[key]
                    st.markdown(f"**{role}: {style.name}**")
                    st.text(f"형태: {style.form}\n색감: {style.palette}\n의상: {style.costume}\n배경: {style.environment}\n분위기: {style.mood}")
        cast, basic, optics, motion = st.tabs(["캐릭터", "모형·재질", "촬영·조명", "영상"])
        characters = []
        with cast:
            count = st.number_input("주요 캐릭터 수", min_value=0, max_value=6, step=1, key="character_count")
            for i in range(count):
                with st.expander(f"캐릭터 {i + 1}", expanded=True):
                    values = {}
                    for field, label in {"identity": "이름·역할", "appearance": "외형·의상·고유 색상", "expression": "표정·시선", "pose": "포즈", "accessory": "소지품", "placement": "위치·다른 캐릭터와의 관계"}.items():
                        key = f"char_{i}_{field}"
                        st.session_state.setdefault(key, "")
                        values[field] = st.text_input(label, key=key, max_chars=800)
                    characters.append(CharacterSpec(**values))
        with basic:
            a, b = st.columns(2)
            with a:
                select("scale", "축척")
                select("material", "주 재질")
                select("wear", "표면 상태")
            with b:
                select("detail", "디테일 밀도")
                select("finish", "표면 마감")
                select("cue", "실제 크기 기준물")
        with optics:
            a, b = st.columns(2)
            with a:
                select("lens", "렌즈 표현")
                select("angle", "카메라 각도")
                select("lighting", "조명")
            with b:
                select("focus", "초점 범위")
                select("composition", "구도")
                select("background", "배경")
        with motion:
            disabled = st.session_state.medium != "video"
            st.selectbox("카메라 이동", list(OPTIONS["movement"]), format_func=OPTIONS["movement"].get, key="movement", disabled=disabled)
            st.slider("길이 (초)", 2, 30, key="duration", disabled=disabled)
            st.text_area("피사체 동작", key="action", max_chars=2000, disabled=disabled or st.session_state.action_source != "custom", on_change=bind_action)
        with st.expander("추가 지시·제외 조건"):
            st.text_area("추가 지시", key="extra", max_chars=3000)
            st.text_area("제외 조건", key="negative", max_chars=2000)
        params = PromptParams(**{f.name: st.session_state[f.name] for f in fields(PromptParams) if f.name not in {"primary_style", "secondary_style", "characters"}}, primary_style=catalog.get(st.session_state.primary_choice), secondary_style=catalog.get(st.session_state.secondary_choice), characters=tuple(characters))
        if st.button("프롬프트 생성", type="primary", use_container_width=True):
            try:
                result = build_prompt(params)
                st.session_state["generated"] = (params, result)
            except ValueError as exc:
                st.error(str(exc))
        try:
            current_project = dump_project(params)
        except ValueError:
            current_project = None
        st.download_button("현재 작업 저장", current_project or "", "miniature_work.json", "application/json", disabled=current_project is None, use_container_width=True)

    with right:
        st.subheader("생성 결과")
        generated = st.session_state.get("generated")
        if generated:
            saved, result = generated
            if saved != params:
                st.warning("설정이 변경되었습니다. 프롬프트 결과는 마지막 생성 시점 기준입니다.")
            st.caption(f"{OPTIONS['medium'][saved.medium]} · {saved.aspect} · {saved.scale} · {len(result.combined):,}자")
            combined, positive, negative = st.tabs(["전체", "본문", "제외 조건"])
            with combined:
                st.code(result.combined, language=None, wrap_lines=True)
            with positive:
                st.code(result.positive, language=None, wrap_lines=True)
            with negative:
                st.code(result.negative, language=None, wrap_lines=True)
            st.download_button("프롬프트 TXT", result.combined, "miniature_prompt.txt", "text/plain", use_container_width=True)
            for note in result.notes:
                st.caption(note)
        else:
            st.info("아직 생성된 프롬프트가 없습니다.")


if __name__ == "__main__":
    main()
