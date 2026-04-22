import traceback
from pathlib import Path
from PIL import Image


def reframe_image(img: Image.Image, target_w: int, target_h: int, crop_direction: str = 'auto') -> Image.Image:
    """智能重构图幅 - 无留白版本。

    策略：
    1. 如果原图与目标比例差异 <= 5%，直接缩放
    2. 如果比例差异 > 5%，等比缩放到完全覆盖目标尺寸，然后裁剪
       - horizontal: 以高度为基准缩放，从左右裁剪
       - vertical: 以宽度为基准缩放，从上下裁剪
       - auto: 选择裁剪量最小的方案
    3. 绝不留白
    """
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    # 计算比例差异
    ratio_diff = abs(src_ratio - target_ratio) / target_ratio

    # 如果比例差异 <= 5%，直接缩放即可
    if ratio_diff <= 0.05:
        return img.resize((target_w, target_h), Image.LANCZOS).convert("RGB")

    # 比例差异较大，需要裁剪
    # 方案A：以宽度为基准缩放，高度超出时从上下裁剪
    k_a = target_w / src_w
    h_a = int(round(src_h * k_a))

    # 方案B：以高度为基准缩放，宽度超出时从左右裁剪
    k_b = target_h / src_h
    w_b = int(round(src_w * k_b))

    # 选择方案：目标是覆盖目标尺寸（不留白）
    # 方案A可行条件: h_a >= target_h
    # 方案B可行条件: w_b >= target_w
    valid_a = h_a >= target_h
    valid_b = w_b >= target_w

    # 根据 crop_direction 和可行性选择方案
    if crop_direction == 'horizontal':
        # 优先从左右裁剪：优先方案B
        use_a = not valid_b
    elif crop_direction == 'vertical':
        # 优先从上下裁剪：优先方案A
        use_a = valid_a
    else:
        # auto: 选择裁剪量最小的可行方案
        if valid_a and valid_b:
            crop_a = h_a - target_h
            crop_b = w_b - target_w
            use_a = crop_a <= crop_b
        elif valid_a:
            use_a = True
        elif valid_b:
            use_a = False
        else:
            # 都不可行，选择缩放更大的方案（确保覆盖）
            use_a = k_a >= k_b

    # 执行缩放和裁剪
    if use_a:
        scale_w = target_w
        scale_h = h_a
        resized = img.resize((scale_w, scale_h), Image.LANCZOS)
        # 从上下裁剪
        top = (scale_h - target_h) // 2
        cropped = resized.crop((0, top, target_w, top + target_h))
    else:
        scale_w = w_b
        scale_h = target_h
        resized = img.resize((scale_w, scale_h), Image.LANCZOS)
        # 从左右裁剪
        left = (scale_w - target_w) // 2
        cropped = resized.crop((left, 0, left + target_w, target_h))

    return cropped.convert("RGB")


# 兼容旧接口
resize_keep_full_image = reframe_image
resize_keep_ratio = reframe_image


def batch_export(files: list[Path], sizes: list[tuple[int, int]], output_dir: Path, crop_direction: str = 'auto') -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ok_count = 0
    fail_count = 0

    for src in files:
        try:
            with Image.open(src) as img:
                for w, h in sizes:
                    out_img = reframe_image(img, w, h, crop_direction)
                    out_name = f"{src.stem}_{w}x{h}.jpg"
                    out_img.save(output_dir / out_name, format="JPEG", quality=95)
                    ok_count += 1
        except Exception:
            fail_count += 1
            traceback.print_exc()

    return ok_count, fail_count
