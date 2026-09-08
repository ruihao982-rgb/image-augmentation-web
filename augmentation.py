import cv2
import albumentations as A


# ==========================================
# 1. 放大 2 倍
# ==========================================
def enlarge_image(image, scale=2.0):
    """
    视觉放大2倍：
    截取原图中心区域的一半，
    再缩放回原图尺寸。
    """

    h, w = image.shape[:2]

    new_h = int(h / scale)
    new_w = int(w / scale)

    # 防止尺寸过小
    new_h = max(new_h, 1)
    new_w = max(new_w, 1)

    # 计算中心区域
    x1 = (w - new_w) // 2
    y1 = (h - new_h) // 2

    x2 = x1 + new_w
    y2 = y1 + new_h

    crop = image[y1:y2, x1:x2]

    # 放大回原图尺寸
    enlarged = cv2.resize(
        crop,
        (w, h),
        interpolation=cv2.INTER_CUBIC
    )

    return enlarged


# ==========================================
# 2. 冷色调
# ==========================================
def adjust_cool(image, strength=30):
    """
    增加蓝色，减少红色，使图片整体偏冷。
    
    OpenCV读取图片为BGR格式：
    B = 蓝色
    G = 绿色
    R = 红色
    """

    result = image.astype("int16")

    # 增加蓝色
    result[:, :, 0] += strength

    # 减少红色
    result[:, :, 2] -= strength

    result = result.clip(0, 255)

    return result.astype("uint8")


# ==========================================
# 3. 暖色调
# ==========================================
def adjust_warm(image, strength=30):
    """
    增加红色，减少蓝色，使图片整体偏暖。
    """

    result = image.astype("int16")

    # 减少蓝色
    result[:, :, 0] -= strength

    # 增加红色
    result[:, :, 2] += strength

    result = result.clip(0, 255)

    return result.astype("uint8")


# ==========================================
# 4. 对比度增强
# ==========================================
contrast_transform = A.Compose([
    A.RandomBrightnessContrast(
        brightness_limit=0.0,
        contrast_limit=0.5,
        p=1.0
    )
])


# ==========================================
# 5. 强模糊
# ==========================================
blur_transform = A.Compose([
    A.GaussianBlur(
        blur_limit=(25, 29),
        p=1.0
    )
])


# ==========================================
# 对一张图片进行全部增强
# ==========================================
def augment_image(image):

    # -------------------------------
    # 1. 冷色调
    # -------------------------------
    cool = adjust_cool(
        image,
        strength=30
    )

    # -------------------------------
    # 2. 暖色调
    # -------------------------------
    warm = adjust_warm(
        image,
        strength=30
    )

    # -------------------------------
    # 3. 放大 2 倍
    # -------------------------------
    enlarged = enlarge_image(
        image,
        scale=2.0
    )

    # -------------------------------
    # 4. 对比度
    # -------------------------------
    contrast = contrast_transform(
        image=image
    )["image"]

    # -------------------------------
    # 5. 模糊
    # -------------------------------
    blur = blur_transform(
        image=image
    )["image"]

    # 返回全部结果
    return {
        "cool": cool,
        "warm": warm,
        "enlarged": enlarged,
        "contrast": contrast,
        "blur": blur
    }