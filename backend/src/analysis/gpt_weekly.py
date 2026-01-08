from openai import OpenAI
import os
from typing import List, Dict, Optional


# ======================================================
# 공용 헬퍼
# ======================================================

def _get_openai_client() -> Optional[OpenAI]:
    """
    OpenAI Client 생성
    - API Key 없으면 None 반환
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _format_signal_block(signals: List[Dict]) -> str:
    """
    Rule signal 리스트를 GPT 입력용 텍스트로 변환
    """
    if not signals:
        return "- (감지된 시그널 없음)"

    return "\n".join(
        f"- {s.get('rule_id')} | score={s.get('score')} | count={s.get('count')}"
        for s in signals
    )


# ======================================================
# 1️⃣ 주간 운영 보고서 GPT
# ======================================================

def gpt_explain_weekly(
    rule_summary: str,
    signals: List[Dict],
) -> str:
    """
    주간 리포트 전용 GPT 설명
    - DB 저장 ❌
    - UI 응답용 보고서
    """

    client = _get_openai_client()
    if not client:
        # GPT 비활성 시 rule summary 그대로 사용
        return rule_summary

    signal_block = _format_signal_block(signals)

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 백엔드 시스템을 담당하는 시니어 SRE입니다.\n"
                "다음 내용을 바탕으로 **한국어로** 주간 장애 분석 보고서를 작성하세요.\n\n"
                "작성 규칙:\n"
                "- 사실에 근거해 설명할 것\n"
                "- 새로운 장애를 추측하거나 만들어내지 말 것\n"
                "- 운영 관점에서의 의미와 리스크를 설명할 것\n"
                "- 간결하지만 보고서 톤을 유지할 것\n"
            ),
        },
        {
            "role": "user",
            "content": f"""
[룰 기반 요약]
{rule_summary}

[감지된 시그널]
{signal_block}

위 내용을 바탕으로,
1. 어떤 장애 패턴이 관측되었는지
2. 현재 운영 리스크 수준
3. 다음 주에 권장되는 대응 또는 모니터링 포인트

를 포함한 **주간 운영 보고서**를 작성하세요.
""".strip(),
        },
    ]

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.2,
    )

    return res.choices[0].message.content.strip()


# ======================================================
# 2️⃣ 다음 주 장애 리스크 판단 GPT
# ======================================================

def gpt_predict_next_week_risk(
    rule_summary: str,
    signals: List[Dict],
) -> Dict[str, str]:
    """
    다음 주 장애 발생 가능성 예측
    - DB 저장 ❌
    - UI / Slack / 배지용
    """

    client = _get_openai_client()
    if not client:
        return {
            "level": "UNKNOWN",
            "reason": "GPT 비활성화 상태로 리스크 판단 불가",
        }

    signal_block = _format_signal_block(signals)

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 시니어 SRE입니다.\n"
                "최근 7일간의 장애 패턴을 기반으로\n"
                "다음 주 장애 발생 가능성을 평가하세요.\n\n"
                "응답 규칙:\n"
                "- 첫 줄은 반드시: 낮음 / 보통 / 높음 중 하나\n"
                "- 그 다음 줄에 간단한 근거 설명\n"
                "- 불확실한 경우 보통으로 판단\n"
            ),
        },
        {
            "role": "user",
            "content": f"""
[최근 룰 기반 요약]
{rule_summary}

[감지된 시그널]
{signal_block}

다음 주 장애 발생 가능성을 평가하세요.
""".strip(),
        },
    ]

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.2,
    )

    text = res.choices[0].message.content.strip()

    # 기본값
    level = "보통"
    if text.startswith("낮음"):
        level = "낮음"
    elif text.startswith("높음"):
        level = "높음"

    return {
        "level": level,
        "reason": text,
    }

# ======================================================
# 3. 리스크 판단 전용 함수
# ======================================================

def gpt_risk_outlook(
    rule_summary: str,
    signals: List[Dict],
) -> dict:
    """
    다음 주 장애 발생 가능성 판단 (응답 전용)
    - DB 저장 ❌
    - 정해진 레벨만 반환
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "level": "보통",
            "reason": "룰 기반 분석 결과 반복 패턴이 감지되어 기본 리스크 수준으로 평가됨",
        }

    client = OpenAI(api_key=api_key)

    signal_block = "\n".join(
        f"- {s['rule_id']} | score={s.get('score')} | count={s.get('count')}"
        for s in signals
    )

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 사이트 신뢰성 엔지니어(SRE)입니다.\n"
                "주어진 정보만으로 다음 주 장애 발생 가능성을 판단하세요.\n\n"
                "규칙:\n"
                "- 반드시 다음 중 하나만 선택: 낮음 / 보통 / 높음\n"
                "- 새로운 장애를 가정하거나 추측하지 말 것\n"
                "- 판단 근거를 한 문장으로 설명할 것\n\n"
                "응답 형식(JSON):\n"
                "{ \"level\": \"보통\", \"reason\": \"...\" }"
            ),
        },
        {
            "role": "user",
            "content": f"""
[룰 기반 요약]
{rule_summary}

[감지된 시그널]
{signal_block}

다음 주 장애 발생 가능성을 평가하세요.
""".strip(),
        },
    ]

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.1,
    )

    try:
        return eval(res.choices[0].message.content.strip())
    except Exception:
        return {
            "level": "보통",
            "reason": "GPT 응답 파싱 실패로 기본 리스크 수준 적용",
        }