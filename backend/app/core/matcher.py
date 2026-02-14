"""Smart major-to-competition matching — ported from paqu/app.py."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.core.models import Competition

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "计算机与AI": [
        "计算机", "软件", "编程", "程序", "算法", "人工智能", "ai",
        "信息安全", "网络安全", "数据", "系统", "物联网",
    ],
    "电子与通信": [
        "电子", "通信", "ict", "芯片", "集成电路", "嵌入式", "光电", "电路",
    ],
    "机械与自动化": [
        "机械", "机器人", "自动化", "智能制造", "机电",
    ],
    "土木与建筑": [
        "结构", "土木", "建筑", "bim", "水利", "测绘", "建造",
    ],
    "化工与材料": [
        "化工", "化学", "材料", "金相", "实验", "能源",
    ],
    "医学与生命": [
        "医学", "生命", "生物", "医", "药",
    ],
    "经管与商科": [
        "金融", "财会", "税收", "市场", "物流", "商业", "电子商务", "经营", "创业",
    ],
    "设计与艺术": [
        "设计", "艺术", "广告", "创意", "数字媒体", "工业设计",
    ],
    "外语与人文": [
        "外语", "英语", "演讲", "跨文化", "诵写",
    ],
    "理科基础": [
        "数学", "建模", "物理", "力学", "统计", "地质",
    ],
    "农业与环境": [
        "农业", "节能减排", "环境",
    ],
}

STATUS_OPEN = "报名中"


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _char_ngrams(text: str, min_n: int = 2, max_n: int = 4) -> Counter:
    normalized = re.sub(r"\s+", "", text.lower())
    grams: list[str] = []
    for n in range(min_n, max_n + 1):
        if len(normalized) < n:
            continue
        grams.extend(normalized[i : i + n] for i in range(len(normalized) - n + 1))
    if not grams and normalized:
        grams = list(normalized)
    return Counter(grams)


def _build_tfidf_vectors(
    texts: list[str],
) -> tuple[list[dict[str, float]], list[float], dict[str, float]]:
    tokenized = [_char_ngrams(t) for t in texts]
    doc_count = len(tokenized)

    df: Counter = Counter()
    for counter in tokenized:
        for token in counter:
            df[token] += 1

    idf = {
        token: math.log((1 + doc_count) / (1 + freq)) + 1
        for token, freq in df.items()
    }

    vectors: list[dict[str, float]] = []
    norms: list[float] = []
    for counter in tokenized:
        vec: dict[str, float] = {}
        norm_sq = 0.0
        for token, tf in counter.items():
            w = tf * idf.get(token, 1.0)
            vec[token] = w
            norm_sq += w * w
        vectors.append(vec)
        norms.append(math.sqrt(norm_sq) if norm_sq > 0 else 1e-9)

    return vectors, norms, idf


def _cosine(
    a: dict[str, float], a_norm: float,
    b: dict[str, float], b_norm: float,
) -> float:
    if len(a) > len(b):
        a, b = b, a
        a_norm, b_norm = b_norm, a_norm
    dot = sum(w * b.get(t, 0.0) for t, w in a.items())
    return dot / (a_norm * b_norm)


def _infer_domain_weights(text: str) -> dict[str, float]:
    lowered = re.sub(r"\s+", "", text.lower())
    raw: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in lowered)
        if hits:
            raw[domain] = hits
    if not raw:
        return {}
    total = sum(raw.values())
    return {d: s / total for d, s in raw.items()}


def _extract_major_keywords(major: str) -> list[str]:
    major = _normalize_space(major)
    keywords: list[str] = [major] if major else []

    for token in re.split(r"[、,，/\\\s\-()（）]+", major):
        token = token.strip()
        if len(token) >= 2:
            keywords.append(token)

    lowered = major.lower()
    for domain_kws in DOMAIN_KEYWORDS.values():
        if any(kw in lowered for kw in domain_kws):
            keywords.extend(domain_kws)

    seen: set[str] = set()
    deduped: list[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)
    return deduped[:30]


def score_matches(
    major: str,
    competitions: list[Competition],
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Return top-k competitions matched to the given major."""
    docs = [f"{c.title} {c.description or ''}" for c in competitions]
    vectors, norms, idf = _build_tfidf_vectors(docs)

    query_counter = _char_ngrams(major)
    query_vec: dict[str, float] = {}
    query_norm_sq = 0.0
    fallback_idf = math.log(1 + len(docs)) + 1
    for token, tf in query_counter.items():
        w = tf * idf.get(token, fallback_idf)
        query_vec[token] = w
        query_norm_sq += w * w
    query_norm = math.sqrt(query_norm_sq) if query_norm_sq > 0 else 1e-9

    major_keywords = _extract_major_keywords(major)
    major_domain = _infer_domain_weights(major)

    scored: list[dict[str, Any]] = []
    for idx, comp in enumerate(competitions):
        comp_text = f"{comp.title} {comp.description or ''}".lower()

        semantic = _cosine(query_vec, query_norm, vectors[idx], norms[idx])

        overlaps = [kw for kw in major_keywords if len(kw) >= 2 and kw.lower() in comp_text][:4]
        keyword_score = min(len(overlaps) / 4.0, 1.0)

        comp_domain = _infer_domain_weights(comp_text)
        domain_score = 0.0
        if major_domain and comp_domain:
            for d, w in major_domain.items():
                if d in comp_domain:
                    domain_score += w
            domain_score = min(domain_score, 1.0)

        status_bonus = 0.05 if comp.crawl_status == STATUS_OPEN else 0.0
        final = min(semantic * 0.7 + keyword_score * 0.2 + domain_score * 0.1 + status_bonus, 1.0)

        reason = "语义相似度匹配"
        if overlaps:
            reason = f"关键词匹配：{'、'.join(overlaps[:3])}"
        elif major_domain:
            common = [d for d in major_domain if d in comp_domain]
            if common:
                reason = f"领域匹配：{common[0]}"

        scored.append({
            "id": comp.id,
            "name": comp.title,
            "url": comp.url or "",
            "intro": comp.description or "",
            "deadline_date": comp.signup_end.isoformat() if comp.signup_end else None,
            "crawl_status": comp.crawl_status or "",
            "status": comp.status,
            "score": round(final * 100, 2),
            "reason": reason,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def match_by_major(db: Session, major: str, top_k: int = 8) -> list[dict[str, Any]]:
    """Public entry point for matching competitions to a major."""
    comps = db.query(Competition).filter(Competition.status == "published").all()
    return score_matches(major, comps, top_k=top_k)
