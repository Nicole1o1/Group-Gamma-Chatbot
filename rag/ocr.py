from pathlib import Path
from typing import List, Tuple


def _auto_rotate(image) -> object:
    try:
        import pytesseract
    except ImportError:
        return image

    try:
        osd = pytesseract.image_to_osd(image)
        rotate_line = next(
            (line for line in osd.splitlines() if line.lower().startswith("rotate")),
            None,
        )
        if rotate_line:
            rotate_degrees = int(rotate_line.split(":")[1].strip())
            if rotate_degrees in {90, 180, 270}:
                return image.rotate(rotate_degrees, expand=True)
    except Exception:
        return image
    return image


def ocr_pdf(path: Path) -> List[Tuple[int, str]]:
    """
    OCR a PDF using Tesseract. Returns (page_index, text) tuples.
    Requires system packages: tesseract-ocr and poppler-utils.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies missing. Install 'pdf2image' and 'pytesseract'."
        ) from exc

    images = convert_from_path(str(path), dpi=300)
    pages: List[Tuple[int, str]] = []
    for page_index, image in enumerate(images, start=1):
        image = image.convert("L")
        image = _auto_rotate(image)
        text = pytesseract.image_to_string(
            image, lang="eng", config="--psm 6"
        ) or ""
        text = text.strip()
        if text:
            pages.append((page_index, text))
    return pages
