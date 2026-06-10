"""Tests for the RAG module: tokenizer, classifier, passage splitter."""

from __future__ import annotations


def test_tokenize_produces_cjk_bigrams_and_ascii(isolated_project):
    from mm._rag import _tokenize

    tokens = _tokenize("Kalman 滤波是一种递推估计方法")
    assert "kalman" in tokens
    assert any("滤波" in t or "递推" in t for t in tokens)


def test_split_passages_chunks_long_text(isolated_project):
    from mm._rag import _split_passages

    text = "句一。" * 200
    passages = _split_passages(text)
    assert len(passages) > 1
    # No empty passages
    assert all(p for p in passages)


def test_classify_topic_recognises_known_categories(isolated_project):
    from mm._rag import classify_topic

    assert classify_topic("题目研究最短路径算法和图论应用") == "图网络"
    assert classify_topic("使用 LSTM 和卡尔曼滤波器建立时序模型") == "时序"
    assert classify_topic("整数规划与启发式算法") == "优化"
    assert classify_topic("碳化硅外延层折射率光谱反射测量") == "半导体/光谱"
    assert classify_topic("完全不相关的题目") == "通用"


def _write_paper(project, name, text):
    paper_dir = project / "02_references" / "paper_texts"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / name).write_text(text, encoding="utf-8")


def test_build_index_finds_paper_texts(isolated_project, monkeypatch):
    from mm import _rag

    # Re-point INDEX_SOURCE_DIRS and INDEX_PATH at the temp project.
    paper_dir = isolated_project / "02_references" / "paper_texts"
    paper_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        _rag,
        "INDEX_SOURCE_DIRS",
        [paper_dir],
    )
    index_path = isolated_project / "02_references" / "bm25_index.pkl"
    monkeypatch.setattr(_rag, "INDEX_PATH", index_path)

    _write_paper(
        isolated_project,
        "a.md",
        "卡尔曼滤波是状态估计的递推算法，使用协方差矩阵预测和高斯噪声更新，"
        "广泛用于动态系统状态估计任务，是经典的最优线性估计器。",
    )
    _write_paper(
        isolated_project,
        "b.md",
        "整数规划在路径优化中常使用分支定界和遗传算法求解，"
        "处理大规模 CVRP 时启发式算法效率更高，是工业界常用的组合优化方法之一。",
    )
    out = _rag.build_index(force=True)
    assert out == index_path
    assert index_path.exists()
    payload = _rag._load_index()
    assert len(payload["passages"]) >= 2


def test_build_index_helpful_error_when_no_sources(isolated_project, monkeypatch):
    from mm import _rag

    empty_dir = isolated_project / "02_references" / "paper_texts"
    empty_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_rag, "INDEX_SOURCE_DIRS", [empty_dir])

    import pytest

    with pytest.raises(SystemExit) as exc:
        _rag.build_index(force=True)
    msg = str(exc.value)
    assert "no source text" in msg
    assert "paper_texts" in msg or "ocr_texts" in msg


def test_retrieve_returns_top_match(isolated_project, monkeypatch):
    from mm import _rag

    paper_dir = isolated_project / "02_references" / "paper_texts"
    paper_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_rag, "INDEX_SOURCE_DIRS", [paper_dir])
    monkeypatch.setattr(_rag, "INDEX_PATH", isolated_project / "02_references" / "bm25_index.pkl")

    _write_paper(
        isolated_project,
        "kalman.md",
        "卡尔曼滤波是状态估计的递推方法，使用协方差矩阵更新预测，"
        "广泛应用于动态系统的最优估计与噪声抑制任务，效果稳定。",
    )
    _write_paper(
        isolated_project,
        "optim.md",
        "整数规划处理路径容量约束问题，使用分支定界和遗传算法求解大规模 MILP，"
        "在车辆路径规划与排班调度中广泛应用，可获取近似最优解。",
    )
    _rag.build_index(force=True)
    hits = _rag.retrieve("卡尔曼滤波 状态估计", top_k=2)
    assert hits
    assert "kalman.md" in hits[0]["source"]


def test_command_rag_status_smoke(isolated_project, monkeypatch, capsys):
    """rag-status should run without raising even when nothing is configured."""
    from mm import _rag

    empty_dir = isolated_project / "02_references" / "paper_texts"
    empty_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_rag, "INDEX_SOURCE_DIRS", [empty_dir])
    monkeypatch.setattr(_rag, "INDEX_PATH", isolated_project / "no_index.pkl")

    import argparse

    _rag.command_rag_status(argparse.Namespace())
    captured = capsys.readouterr()
    assert "RAG Status" in captured.out
    assert "not built" in captured.out
