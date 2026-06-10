"""Tests for the figure lint colour and grid detectors."""

from __future__ import annotations

import pytest

PIL = pytest.importorskip("PIL")


def test_detect_red_returns_high_ratio_for_red_image():
    from PIL import Image

    from mm._figure_lint import _detect_red

    image = Image.new("RGB", (50, 50), color=(220, 20, 20))
    assert _detect_red(image) > 0.5


def test_detect_red_returns_zero_for_blue_image():
    from PIL import Image

    from mm._figure_lint import _detect_red

    image = Image.new("RGB", (50, 50), color=(30, 30, 220))
    assert _detect_red(image) == 0.0


def test_detect_grid_panel_true_for_cross():
    from PIL import Image, ImageDraw

    from mm._figure_lint import _detect_grid_panel

    image = Image.new("L", (200, 200), color=0)
    draw = ImageDraw.Draw(image)
    # Solid white horizontal middle line and vertical middle line.
    draw.line([(0, 100), (200, 100)], fill=255, width=4)
    draw.line([(100, 0), (100, 200)], fill=255, width=4)
    assert _detect_grid_panel(image) is True


def test_detect_grid_panel_false_for_blank_image():
    from PIL import Image

    from mm._figure_lint import _detect_grid_panel

    image = Image.new("L", (200, 200), color=128)
    assert _detect_grid_panel(image) is False
