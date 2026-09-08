import os
import uuid
import zipfile

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


# ==========================================
# Flask 初始化
# ==========================================

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ==========================================
# 允许的图片格式
# ==========================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff"
}


# ==========================================
# 首页
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# 图片增强
# ==========================================

@app.route("/augment", methods=["POST"])
def augment():

    files = request.files.getlist("images")

    if not files:
        return jsonify({
            "success": False,
            "message": "没有上传图片"
        }), 400


    # ======================================
    # 创建任务ID
    # ======================================

    task_id = uuid.uuid4().hex

    task_output_dir = os.path.join(
        OUTPUT_FOLDER,
        task_id
    )

    os.makedirs(
        task_output_dir,
        exist_ok=True
    )


    results = []


    # ======================================
    # 逐张处理
    # ======================================

    for index, file in enumerate(files):

        if not file.filename:
            continue


        original_filename = file.filename

        print(
            f"\n正在处理：{original_filename}"
        )


        # ----------------------------------
        # 获取扩展名
        # ----------------------------------

        _, ext = os.path.splitext(
            original_filename
        )

        ext = ext.lower()


        if ext not in ALLOWED_EXTENSIONS:

            print(
                f"❌ 不支持的文件："
                f"{original_filename}"
            )

            continue


        # ==================================
        # 直接读取上传文件
        #
        # 不使用 cv2.imread()
        # ==================================

        file_bytes = file.read()

        np_array = np.frombuffer(
            file_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )


        # ==================================
        # 判断图片是否读取成功
        # ==================================

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


        # ==================================
        # 使用安全的英文文件名
        # ==================================

        base_name = (
            f"image_{index + 1:04d}"
        )


        # ==================================
        # 执行5种增强
        # ==================================

        augmented = augment_image(
            image
        )


        print(
            "生成增强图片：",
            list(augmented.keys())
        )


        # ==================================
        # 保存结果
        # ==================================

        output_files = {}


        for aug_type, aug_image in augmented.items():

            output_filename = (
                f"{base_name}_"
                f"{aug_type}"
                f"{ext}"
            )

            output_path = os.path.join(
                task_output_dir,
                output_filename
            )


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


            output_files[aug_type] = (
                f"/output/"
                f"{task_id}/"
                f"{output_filename}"
            )


        # ==================================
        # 添加结果
        # ==================================

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


    # ======================================
    # 检查
    # ======================================

    if len(results) == 0:

        try:
            os.rmdir(task_output_dir)
        except:
            pass

        return jsonify({

            "success": False,

            "message":
                "没有成功读取任何图片，"
                "请检查图片格式。"

        }), 400


    # ======================================
    # 创建 ZIP
    # ======================================

    zip_filename = (
        f"{task_id}.zip"
    )

    zip_path = os.path.join(
        OUTPUT_FOLDER,
        zip_filename
    )


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

            zip_file.write(
                file_path,
                filename
            )


    total_generated = sum(
        sum(
            1
            for key in [
                "cool",
                "warm",
                "enlarged",
                "contrast",
                "blur"
            ]
            if item.get(key)
        )
        for item in results
    )


    print(
        f"\n✅ 本次任务完成"
    )

    print(
        f"处理图片：{len(results)} 张"
    )

    print(
        f"生成图片：{total_generated} 张"
    )


    # ======================================
    # 返回前端
    # ======================================

    return jsonify({

        "success": True,

        "task_id": task_id,

        "results": results,

        "count": len(results),

        "total_generated": total_generated,

        "zip":
            f"/download/{zip_filename}"

    })


# ==========================================
# 显示增强图片
# ==========================================

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


# ==========================================
# 下载 ZIP
# ==========================================

@app.route(
    "/download/<filename>"
)
def download_file(filename):

    return send_from_directory(
        OUTPUT_FOLDER,
        filename,
        as_attachment=True
    )


# ==========================================
# 启动
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )