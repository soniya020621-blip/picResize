from pathlib import Path


SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
DEFAULT_OUTPUT_DIR = Path.cwd() / "output"
PRESET_SIZES = {
    "1464x600": (1464, 600),
    "600x450": (600, 450),
}


def parse_sizes(raw_text: str) -> list[tuple[int, int]]:
    sizes = []
    chunks = [item.strip() for item in raw_text.split(",") if item.strip()]
    for chunk in chunks:
        if "x" not in chunk.lower():
            raise ValueError(f"尺寸格式错误: {chunk}，应为 宽x高，例如 1464x600")
        width_str, height_str = chunk.lower().split("x", 1)
        width = int(width_str.strip())
        height = int(height_str.strip())
        if width <= 0 or height <= 0:
            raise ValueError(f"尺寸必须大于 0: {chunk}")
        sizes.append((width, height))
    if not sizes:
        raise ValueError("请至少输入一个目标尺寸，例如 1464x600")
    return sizes
