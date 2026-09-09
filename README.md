# Hangeul Miniature

플랫폼 구분 없는 미니어처 이미지·영상 프롬프트 제작기입니다. 외부 API나 API 키 없이 로컬에서 규칙 기반으로 생성합니다. 자유 입력은 자동 번역하지 않고 원문 그대로 포함하며, 공통 촬영 지시는 영어로 출력합니다.

미니어처 캐릭터, 스타일 혼합, 실제 축척, 재질, 촬영 설정을 조합하여 프롬프트를 작성하는 Streamlit 앱입니다. 이미지·영상 자체를 생성하는 프로그램은 아닙니다.

저장소: https://github.com/rgb0rgb/hangeul-miniature

## 설치 및 실행

Python 3.10 이상과 **Streamlit 1.38 이상**이 필요합니다. 최소 지원 버전 1.38과 최신 지원 범위를 CI에서 각각 검사합니다.

```bash
git clone https://github.com/rgb0rgb/hangeul-miniature.git
cd hangeul-miniature
```

### Windows

Windows에서 `run.bat`을 실행합니다. Python 공식 Windows 런처인 `py`를 사용해 가상환경을 만들므로 Microsoft Store의 `python` 실행 별칭과 충돌하지 않습니다. 최초 실행은 Python과 패키지 다운로드 연결이 필요합니다. 설치 이후에는 `run_no_install.bat`으로 실행할 수 있습니다.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

기본 접속 주소는 `http://localhost:8501`입니다.

## 구성

- 장면과 주 피사체 필수 입력, 이미지·영상 출력, 화면 비율 선택
- 실제 축척, 재질, 마감, 표면 상태, 디테일 밀도, 크기 기준물
- 렌즈, 초점, 각도, 구도, 조명, 배경 설정
- 영상 전용 카메라 이동, 길이, 피사체 동작, 시간적 일관성 지시
- 전체 프롬프트·본문·제외 조건 구분, 코드 블록 복사, TXT 다운로드
- 캐릭터별 이름·외형·표정·포즈·소지품·상호 위치 설정 (최대 6명)
- 기본 스타일과 사용자 스타일, 주/보조 스타일 혼합
- 현재 작업 저장·불러오기 JSON

영상 동작은 기본적으로 현재 장면에 적힌 사건 순서를 따릅니다. `동작 직접 지정`을 선택한 경우 별도 동작을 사용하며, 작성 당시 장면·주 피사체에 연결됩니다. 장면이나 주 피사체를 편집하면 이전 별도 동작을 초기화합니다.

사용자 스타일은 `data/styles`에 저장되어 재실행해도 유지됩니다. 스타일 파일명은 내용 기반 SHA-256 키를 사용하고 완성된 파일을 원자적으로 저장합니다. 테스트용 저장 위치는 `MINI1_STYLE_DIR` 환경변수로 지정할 수 있습니다.

## 대상 생성 모델

이 앱은 특정 플랫폼 전용 문법으로 변환하지 않고 구조화된 장문 자연어 프롬프트를 출력합니다. 따라서 **Veo, Sora, ChatGPT/Gemini 계열처럼 장문 자연어 지시를 해석하는 모델을 주 사용 대상으로 권장**합니다. Midjourney나 CLIP 기반 Stable Diffusion 계열에서는 긴 지시가 절삭되거나 일부 조건의 영향이 약해질 수 있습니다.

스타일 이름은 시각적 참고이며 인기도 순위를 뜻하지 않습니다. 프롬프트에서는 명시한 캐릭터 정체성, 장면, 재질·축척·촬영 설정을 스타일보다 우선하도록 지시합니다. 자유 문장 사이의 의미 충돌까지 자동 검출하지는 않습니다.

## 검증

```bash
python -m unittest discover -s tests -v
```

GitHub Actions는 두 환경을 검사합니다.

- `minimum-streamlit`: Streamlit 1.38.0 고정 + 전체 단위 테스트 + 실제 프롬프트 생성 버튼 AppTest
- `supported-latest`: requirements 범위의 최신 Streamlit + 전체 단위 테스트 + 연속 AppTest 실행

## 라이선스

개인·비상업적 사용을 허용하는 **Hangeul Miniature Personal Non-Commercial License 1.0**을 적용합니다. 상업적 사용에는 저작권자의 사전 서면 허가가 필요합니다. 자세한 조건은 `LICENSE`를 확인하세요. 이 라이선스는 OSI 승인 오픈소스 라이선스가 아닙니다.

## 파일 구성

```text
app.py                    Streamlit 화면과 입력 상태 관리
modules/templates.py      설정, 장면 예시, 작업 파일 저장·복원
modules/styles.py         기본 스타일과 사용자 스타일 저장
modules/compiler.py       프롬프트 생성과 동작 연결 검사
tests/                    자동 검증
.github/workflows/tests.yml 최소/최신 Streamlit CI
requirements.txt          실행 의존성
run.bat                   Windows 설치·실행
run_no_install.bat        Windows 재실행
LICENSE                   개인·비상업 라이선스
```

가상환경, 캐시, 비밀 설정 파일 및 `data/`의 개인 스타일 파일은 Git 추적 대상에서 제외합니다.
