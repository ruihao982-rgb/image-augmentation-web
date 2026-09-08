import os
import uuid
import zipfile
import time
import shutil

import cv2
import numpy as np

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory
)

from augmentation import augment_image


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)


# =========================================================
# 文件夹
# =========================================================

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# 上传限制
# =========================================================

# 单张图片最大 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# 一次最多上传 20 张
MAX_FILES = 20

# 单次上传总大小最大 100 MB
MAX_TOTAL_SIZE = 100 * 1024 * 1024

# Flask 请求总大小限制
app.config["MAX_CONTENT_LENGTH"] = MAX_TOTAL_SIZE


# =========================================================
# 支持的图片格式
# =========================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff"
}


# =========================================================
# 自动清理旧文件
# =========================================================

def cleanup_old_files():
    """
    删除 1 小时以前的输出文件和任务目录。
    """

    expire_time = time.time() - 3600

    # -----------------------------------------------------
    # 清理 outputs
    # -----------------------------------------------------

    if os.path.exists(OUTPUT_FOLDER):

        for name in os.listdir(OUTPUT_FOLDER):

            path = os.path.join(
                OUTPUT_FOLDER,
                name
            )

            try:

                # 获取最后修改时间
                modify_time = os.path.getmtime(path)

                if modify_time < expire_time:

                    # 如果是目录
                    if os.path.isdir(path):

                        shutil.rmtree(path)

                        print(
                            f"🗑 已删除旧任务：{name}"
                        )

                    # 如果是文件
                    elif os.path.isfile(path):

                        os.remove(path)

                        print(
                            f"🗑 已删除旧文件：{name}"
                        )

            except Exception as e:

                print(
                    f"⚠️ 清理文件失败 {path}: {e}"
                )

    # -----------------------------------------------------
    # 清理 uploads
    # -----------------------------------------------------

    if os.path.exists(UPLOAD_FOLDER):

        for name in os.listdir(UPLOAD_FOLDER):

            path = os.path.join(
                UPLOAD_FOLDER,
                name
            )

            try:

                if os.path.getmtime(path) < expire_time:

                    if os.path.isfile(path):

                        os.remove(path)

                        print(
                            f"🗑 已删除上传文件：{name}"
                        )

            except Exception as e:

                print(
                    f"⚠️ 清理上传文件失败 {path}: {e}"
                )


# =========================================================
# 首页
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# 图片增强
# =========================================================

@app.route(
    "/augment",
    methods=["POST"]
)
def augment():

    print("\n========================================")
    print("开始处理图片增强任务")
    print("========================================")

    # -----------------------------------------------------
    # 清理旧文件
    # -----------------------------------------------------

    cleanup_old_files()

    # -----------------------------------------------------
    # 获取上传文件
    # -----------------------------------------------------

    files = request.files.getlist("images")

    # 没有文件
    if not files:

        return jsonify({
            "success": False,
            "message": "没有上传图片"
        }), 400

    # -----------------------------------------------------
    # 检查文件数量
    # -----------------------------------------------------

    if len(files) > MAX_FILES:

        return jsonify({
            "success": False,
            "message": f"一次最多上传 {MAX_FILES} 张图片"
        }), 400

    # -----------------------------------------------------
    # 检查文件大小
    # -----------------------------------------------------

    total_size = 0

    file_data = []

    for file in files:

        if not file.filename:

            continue

        # 读取文件内容
        file_bytes = file.read()

        # 重新定位文件指针
        file.seek(0)

        file_size = len(file_bytes)

        # 累计大小
        total_size += file_size

        # -------------------------------------------------
        # 单文件大小检查
        # -------------------------------------------------

        if file_size > MAX_FILE_SIZE:

            return jsonify({
                "success": False,
                "message": (
                    f"图片「{file.filename}」"
                    f"超过 10 MB 限制"
                )
            }), 400

        # 保存到内存列表
        file_data.append({
            "file": file,
            "bytes": file_bytes,
            "size": file_size
        })

    # -----------------------------------------------------
    # 总大小检查
    # -----------------------------------------------------

    if total_size > MAX_TOTAL_SIZE:

        return jsonify({
            "success": False,
            "message": "本次上传总大小不能超过 100 MB"
        }), 400

    # -----------------------------------------------------
    # 如果没有有效文件
    # -----------------------------------------------------

    if len(file_data) == 0:

        return jsonify({
            "success": False,
            "message": "没有找到有效的图片文件"
        }), 400

    # -----------------------------------------------------
    # 创建任务 ID
    # -----------------------------------------------------

    task_id = uuid.uuid4().hex

    task_output_dir = os.path.join(
        OUTPUT_FOLDER,
        task_id
    )

    os.makedirs(
        task_output_dir,
        exist_ok=True
    )

    # -----------------------------------------------------
    # 保存结果
    # -----------------------------------------------------

    results = []

    # =====================================================
    # 开始逐张处理
    # =====================================================

    for index, item in enumerate(file_data):

        file = item["file"]
        file_bytes = item["bytes"]

        original_filename = file.filename

        print("")
        print("----------------------------------------")
        print(f"正在处理：{original_filename}")
        print("----------------------------------------")

        # -------------------------------------------------
        # 获取扩展名
        # -------------------------------------------------

        _, ext = os.path.splitext(
            original_filename
        )

        ext = ext.lower()

        # -------------------------------------------------
        # 检查格式
        # -------------------------------------------------

        if ext not in ALLOWED_EXTENSIONS:

            print(
                f"❌ 不支持的文件格式："
                f"{original_filename}"
            )

            continue

        # -------------------------------------------------
        # 使用内存数据读取图片
        #
        # 不使用 cv2.imread()
        #
        # 可以解决 Windows / Linux 下
        # 中文文件名导致的读取问题
        # -------------------------------------------------

        np_array = np.frombuffer(
            file_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )

        # -------------------------------------------------
        # 判断图片是否读取成功
        # -------------------------------------------------

        if image is None:

            print(
                f"❌ 图片读取失败："
                f"{original_filename}"
            )

            continue

        print(
            f"✅ 图片读取成功："
            f"{original_filename}"
        )

        print(
            f"   图片尺寸："
            f"{image.shape[1]} x {image.shape[0]}"
        )

        # -------------------------------------------------
        # 使用安全的英文文件名
        #
        # 避免中文文件名、空格、特殊字符等问题
        # -------------------------------------------------

        base_name = (
            f"image_{index + 1:04d}"
        )

        # -------------------------------------------------
        # 生成 5 种增强图片
        # -------------------------------------------------

        try:

            augmented = augment_image(
                image
            )

        except Exception as e:

            print(
                f"❌ 图片增强失败："
                f"{original_filename}"
            )

            print(
                f"   错误信息：{e}"
            )

            continue

        print(
            "生成增强图片：",
            list(augmented.keys())
        )

        # -------------------------------------------------
        # 保存各类增强图片
        # -------------------------------------------------

        output_files = {}

        for aug_type, aug_image in augmented.items():

            # 输出文件名
            #
            # 例如：
            # image_0001_cool.jpg
            # image_0001_warm.jpg
            # image_0001_enlarged.jpg
            # image_0001_contrast.jpg
            # image_0001_blur.jpg

            output_filename = (
                f"{base_name}_"
                f"{aug_type}"
                f"{ext}"
            )

            output_path = os.path.join(
                task_output_dir,
                output_filename
            )

            # -------------------------------------------------
            # 保存图片
            # -------------------------------------------------

            success = cv2.imwrite(
                output_path,
                aug_image
            )

            if not success:

                print(
                    f"❌ 保存失败："
                    f"{output_filename}"
                )

                continue

            print(
                f"  ✅ 已生成："
                f"{output_filename}"
            )

            # -------------------------------------------------
            # 保存访问 URL
            # -------------------------------------------------

            output_files[aug_type] = (
                f"/output/"
                f"{task_id}/"
                f"{output_filename}"
            )

        # -------------------------------------------------
        # 添加结果
        # -------------------------------------------------

        results.append({
            "original": original_filename,

            "cool": output_files.get(
                "cool"
            ),

            "warm": output_files.get(
                "warm"
            ),

            "enlarged": output_files.get(
                "enlarged"
            ),

            "contrast": output_files.get(
                "contrast"
            ),

            "blur": output_files.get(
                "blur"
            )
        })

    # =====================================================
    # 判断是否至少成功处理一张
    # =====================================================

    if len(results) == 0:

        # 删除空任务目录
        try:

            os.rmdir(
                task_output_dir
            )

        except Exception:
            pass

        return jsonify({
            "success": False,
            "message": (
                "没有成功读取任何图片，"
                "请检查图片格式或图片是否损坏。"
            )
        }), 400

    # =====================================================
    # 统计实际生成数量
    # =====================================================

    total_generated = 0

    for item in results:

        for key in [
            "cool",
            "warm",
            "enlarged",
            "contrast",
            "blur"
        ]:

            if item.get(key):

                total_generated += 1

    # =====================================================
    # 如果没有生成任何增强图片
    # =====================================================

    if total_generated == 0:

        try:

            shutil.rmtree(
                task_output_dir
            )

        except Exception:
            pass

        return jsonify({
            "success": False,
            "message": "图片增强失败，没有生成结果。"
        }), 500

    # =====================================================
    # 创建 ZIP
    # =====================================================

    zip_filename = (
        f"{task_id}.zip"
    )

    zip_path = os.path.join(
        OUTPUT_FOLDER,
        zip_filename
    )

    try:

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for filename in os.listdir(
                task_output_dir
            ):

                file_path = os.path.join(
                    task_output_dir,
                    filename
                )

                # 确保只压缩文件
                if not os.path.isfile(
                    file_path
                ):
                    continue

                zip_file.write(
                    file_path,
                    filename
                )

        print(
            f"✅ ZIP 创建成功："
            f"{zip_filename}"
        )

    except Exception as e:

        print(
            f"❌ ZIP 创建失败：{e}"
        )

        return jsonify({
            "success": False,
            "message": "ZIP 文件创建失败"
        }), 500

    # =====================================================
    # 输出任务信息
    # =====================================================

    print("")
    print("========================================")
    print("✅ 本次任务完成")
    print(
        f"处理图片："
        f"{len(results)} 张"
    )
    print(
        f"生成图片："
        f"{total_generated} 张"
    )
    print(
        f"任务 ID："
        f"{task_id}"
    )
    print("========================================")

    # =====================================================
    # 返回 JSON
    # =====================================================

    return jsonify({

        "success": True,

        "task_id": task_id,

        "results": results,

        "count": len(results),

        "total_generated": total_generated,

        "zip": (
            f"/download/"
            f"{zip_filename}"
        )
    })


# =========================================================
# 查看生成的图片
# =========================================================

@app.route(
    "/output/<task_id>/<filename>"
)
def output_file(
    task_id,
    filename
):

    directory = os.path.join(
        OUTPUT_FOLDER,
        task_id
    )

    return send_from_directory(
        directory,
        filename
    )


# =========================================================
# 下载 ZIP
# =========================================================

@app.route(
    "/download/<filename>"
)
def download_file(
    filename
):

    return send_from_directory(
        OUTPUT_FOLDER,
        filename,
        as_attachment=True
    )


# =========================================================
# 上传文件过大
# =========================================================

@app.errorhandler(413)
def request_entity_too_large(error):

    return jsonify({

        "success": False,

        "message": (
            "上传文件过大，"
            "单次上传总大小不能超过 100 MB"
        )

    }), 413


# =========================================================
# 通用异常处理
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    print(
        f"❌ 服务器内部错误：{error}"
    )

    return jsonify({

        "success": False,

        "message": (
            "服务器处理图片时发生错误，"
            "请稍后重试。"
        )

    }), 500


# =========================================================
# 本地运行
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )