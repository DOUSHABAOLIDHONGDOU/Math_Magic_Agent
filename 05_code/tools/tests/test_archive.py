"""Tests for stale-topic keyword scoring and artifact archival."""

from __future__ import annotations


def test_keyword_evidence_score_ignores_stopwords(isolated_project):
    from mm._archive import keyword_evidence_score

    # `问题` is in TOPIC_KEYWORD_STOPWORDS; should not score.
    score = keyword_evidence_score("某文档提到 问题 字样", ["问题"])
    assert score == 0


def test_keyword_evidence_score_handles_chinese(isolated_project):
    from mm._archive import keyword_evidence_score

    text = "本文档关于碳化硅外延层厚度测量"
    score = keyword_evidence_score(text.lower(), ["碳化硅", "外延", "BMI"])
    # 碳化硅 and 外延 match. BMI does not.
    assert score > 0


def test_artifact_matches_stale_topic_skips_when_current_dominates(isolated_project, tmp_path):
    from mm._archive import artifact_matches_stale_topic

    # File mentions old keyword once but lists many current ones — should be kept.
    text_file = tmp_path / "report.md"
    text_file.write_text(
        "本报告聚焦碳化硅外延层折射率测量，参考方案 B 历史上曾涉及 BMI 与孕周方法。"
        "新方案改用反射率谱估计，已在数据 dict 中登记。",
        encoding="utf-8",
    )
    stale = ["BMI", "孕周"]
    current = ["碳化硅", "外延层", "折射率", "反射率谱", "方案", "数据"]
    assert artifact_matches_stale_topic(text_file, stale, current) is False


def test_title_topic_ngrams_returns_chinese_bigrams(isolated_project):
    from mm._archive import title_topic_ngrams

    result = title_topic_ngrams("碳化硅外延层厚度的确定")
    assert "碳化" in result
    assert "外延" in result
    # Stopword should not appear as standalone ngram.
    assert "问题" not in result


def test_question_from_artifact_path_detects_q_prefix(isolated_project):
    from pathlib import Path

    from mm._archive import question_from_artifact_path

    assert question_from_artifact_path(Path("03_methods/Q1/scheme_B.md")) == "Q1"
    assert question_from_artifact_path(Path("07_paper/sections/model_q3.tex")) == "Q3"
    assert question_from_artifact_path(Path("README.md")) is None
