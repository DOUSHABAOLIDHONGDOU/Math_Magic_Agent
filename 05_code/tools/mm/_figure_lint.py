"""Phase 5: figure lint — detect red lines / 2x2 grid panels / oversized figures.

Pillow-only implementation, no OpenCV. Pure WARN output: returns issue strings;
the caller decides whether to fail the build (run_layout_check appends these
to its issue list).
"""

from __future__ import annotations

from pathlib import Path

from ._util import rel


# Red-line detection thresholds. RGB-space: a "red" pixel has high R, low G/B.
RED_R_MIN = 180
RED_GB_MAX = 80
RED_PIXEL_RATIO_THRESHOLD = 0.005  # ≥0.5% of image area = WARN

# Grid panel detection thresholds.
GRID_WHITE_THRESHOLD = 235      # 0-255 grayscale; brighter = "white separator"
GRID_LINE_MIN_RATIO = 0.85      # a row/col must be this fraction white to count
GRID_MIN_VERTICAL_LINES = 1
GRID_MIN_HORIZONTAL_LINES = 1

# Oversized figure: width > 0.76 * page width.
OVERSIZED_WIDTH_RATIO = 0.76


def _detect_red(image) -> float:
    """Return the fraction of pixels that look like a red line/marker."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    if width == 0 or height == 0:
        return 0.0
    pixels = rgb.load()
    red_count = 0
    # Subsample if image is huge to stay fast.
    stride = max(1, (width * height) // 200_000)
    sampled = 0
    for index in range(0, width * height, stride):
        x = index % width
        y = index // width
        r, g, b = pixels[x, y]
        if r >= RED_R_MIN and g <= RED_GB_MAX and b <= RED_GB_MAX:
            red_count += 1
        sampled += 1
    return red_count / sampled if sampled else 0.0


def _detect_grid_panel(image) -> bool:
    """Return True when we see a 2×2 (or denser) grid: at least one nearly-white
    full-width row AND at least one full-height white column near the centre."""
    gray = image.convert("L")
    width, height = gray.size
    if width < 60 or height < 60:
        return False
    pixels = gray.load()

    # Sample a centred horizontal band 30%-70% of the height. A "white row" is
    # a row whose pixel mean exceeds GRID_WHITE_THRESHOLD for at least
    # GRID_LINE_MIN_RATIO of its width.
    horiz_lines = 0
    for y in range(int(height * 0.3), int(height * 0.7)):
        bright = sum(1 for x in range(width) if pixels[x, y] >= GRID_WHITE_THRESHOLD)
        if bright / width >= GRID_LINE_MIN_RATIO:
            horiz_lines += 1
    vert_lines = 0
    for x in range(int(width * 0.3), int(width * 0.7)):
        bright = sum(1 for y in range(height) if pixels[x, y] >= GRID_WHITE_THRESHOLD)
        if bright / height >= GRID_LINE_MIN_RATIO:
            vert_lines += 1
    # We need at least one of each to plausibly be a 2x2 grid.
    return horiz_lines >= GRID_MIN_HORIZONTAL_LINES and vert_lines >= GRID_MIN_VERTICAL_LINES


def run_figure_lint(pdf_path: Path) -> list[str]:
    """Scan every image embedded in the PDF and flag style violations."""
    if not pdf_path.exists():
        return []
    try:
        import fitz
    except ImportError:
        return []
    try:
        from PIL import Image
    except ImportError:
        return []

    issues: list[str] = []
    document = fitz.open(pdf_path)
    for page_index, page in enumerate(document, start=1):
        page_width = page.rect.width
        if page_width <= 0:
            continue
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            try:
                base = document.extract_image(xref)
            except Exception:  # noqa: BLE001 - some images can't be extracted
                continue
            try:
                from io import BytesIO

                image = Image.open(BytesIO(base["image"]))
            except Exception:  # noqa: BLE001 - unsupported codec, skip
                continue
            red_ratio = _detect_red(image)
            if red_ratio >= RED_PIXEL_RATIO_THRESHOLD:
                issues.append(
                    f"page {page_index} image xref={xref}: red-line pixels {red_ratio:.2%} "
                    f"≥ {RED_PIXEL_RATIO_THRESHOLD:.0%}; the style guide bans red dashed reference lines."
                )
            if _detect_grid_panel(image):
                issues.append(
                    f"page {page_index} image xref={xref}: looks like a 2×2 (or denser) grid panel; "
                    "single-conclusion figures preferred."
                )
            # Oversize check: compare image bbox width with page width.
            try:
                bboxes = page.get_image_bbox(image_info)
            except Exception:  # noqa: BLE001 - older pymupdf returns differently
                bboxes = None
            if bboxes is not None:
                bbox_list = bboxes if isinstance(bboxes, list) else [bboxes]
                for bbox in bbox_list:
                    try:
                        ratio = bbox.width / page_width
                    except AttributeError:
                        continue
                    if ratio > OVERSIZED_WIDTH_RATIO:
                        issues.append(
                            f"page {page_index} image xref={xref}: width {ratio:.0%} of page "
                            f"exceeds {OVERSIZED_WIDTH_RATIO:.0%} cap."
                        )
    if issues:
        issues.insert(0, f"figure-lint on {rel(pdf_path)} found {len(issues)} potential style violation(s)")
    return issues


def command_figure_lint(args):
    from ._paths import PROJECT_ROOT

    pdf_path = args.pdf if args.pdf.is_absolute() else PROJECT_ROOT / args.pdf
    issues = run_figure_lint(pdf_path)
    print("== Figure Lint ==")
    print(f"pdf: {rel(pdf_path)}")
    if not issues:
        print("figures: ok")
        return
    for issue in issues:
        print(f"WARN: {issue}")
