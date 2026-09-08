const fileInput =
    document.getElementById("fileInput");

const uploadBox =
    document.getElementById("uploadBox");

const previewContainer =
    document.getElementById("previewContainer");

const selectedSection =
    document.getElementById("selectedSection");

const fileCount =
    document.getElementById("fileCount");

const augmentButton =
    document.getElementById("augmentButton");

const loading =
    document.getElementById("loading");

const resultSection =
    document.getElementById("resultSection");

const resultContainer =
    document.getElementById("resultContainer");

const downloadAll =
    document.getElementById("downloadAll");


let selectedFiles = [];


/* =========================================
   选择图片
========================================= */

fileInput.addEventListener(
    "change",
    function () {

        selectedFiles =
            Array.from(this.files);

        showPreview();

    }
);


/* =========================================
   显示上传图片
========================================= */

function showPreview() {

    previewContainer.innerHTML = "";


    if (selectedFiles.length === 0) {

        selectedSection.classList.add(
            "hidden"
        );

        augmentButton.disabled = true;

        return;
    }


    selectedSection.classList.remove(
        "hidden"
    );


    augmentButton.disabled = false;


    fileCount.textContent =
        `${selectedFiles.length} 张`;


    selectedFiles.forEach(
        function (file) {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "preview-item";


            const img =
                document.createElement(
                    "img"
                );


            img.src =
                URL.createObjectURL(file);


            const name =
                document.createElement(
                    "div"
                );


            name.className =
                "preview-name";


            name.textContent =
                file.name;


            item.appendChild(img);

            item.appendChild(name);

            previewContainer.appendChild(
                item
            );

        }
    );
}


/* =========================================
   拖拽上传
========================================= */

uploadBox.addEventListener(
    "dragover",
    function (event) {

        event.preventDefault();

        uploadBox.style.borderColor =
            "#6c63ff";

    }
);


uploadBox.addEventListener(
    "dragleave",
    function () {

        uploadBox.style.borderColor =
            "#d5d9e2";

    }
);


uploadBox.addEventListener(
    "drop",
    function (event) {

        event.preventDefault();

        uploadBox.style.borderColor =
            "#d5d9e2";


        selectedFiles =
            Array.from(
                event.dataTransfer.files
            ).filter(
                file =>
                    file.type.startsWith(
                        "image/"
                    )
            );


        showPreview();

    }
);


/* =========================================
   开始增强
========================================= */

augmentButton.addEventListener(
    "click",
    async function () {

        if (selectedFiles.length === 0) {

            alert(
                "请先选择图片"
            );

            return;
        }


        loading.classList.remove(
            "hidden"
        );


        augmentButton.disabled = true;


        resultContainer.innerHTML = "";


        resultSection.classList.add(
            "hidden"
        );


        const formData =
            new FormData();


        selectedFiles.forEach(
            function (file) {

                formData.append(
                    "images",
                    file
                );

            }
        );


        try {

            const response =
                await fetch(
                    "/augment",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!data.success) {

                alert(
                    data.message ||
                    "处理失败"
                );

                return;
            }


            showResults(data);


        } catch (error) {

            console.error(error);

            alert(
                "服务器处理失败，"
                + "请检查 Flask 是否正常运行"
            );

        } finally {

            loading.classList.add(
                "hidden"
            );

            augmentButton.disabled =
                false;

        }

    }
);


/* =========================================
   显示增强结果
========================================= */

function showResults(data) {

    resultContainer.innerHTML = "";


    data.results.forEach(
        function (result) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "result-item";


            item.innerHTML = `

                <div class="original-name">

                    原图：
                    ${result.original}

                </div>


                <div class="result-grid">


                    <!-- 冷色 -->

                    <div class="result-card">

                        <img
                            src="${result.cool}"
                        >

                        <div class="result-info">

                            <h3>
                                🧊 冷色调
                            </h3>

                            <a
                                href="${result.cool}"
                                download
                                class="download-button"
                            >
                                下载图片
                            </a>

                        </div>

                    </div>


                    <!-- 暖色 -->

                    <div class="result-card">

                        <img
                            src="${result.warm}"
                        >

                        <div class="result-info">

                            <h3>
                                🔥 暖色调
                            </h3>

                            <a
                                href="${result.warm}"
                                download
                                class="download-button"
                            >
                                下载图片
                            </a>

                        </div>

                    </div>


                    <!-- 放大 -->

                    <div class="result-card">

                        <img
                            src="${result.enlarged}"
                        >

                        <div class="result-info">

                            <h3>
                                🔍 放大 2×
                            </h3>

                            <a
                                href="${result.enlarged}"
                                download
                                class="download-button"
                            >
                                下载图片
                            </a>

                        </div>

                    </div>


                    <!-- 对比度 -->

                    <div class="result-card">

                        <img
                            src="${result.contrast}"
                        >

                        <div class="result-info">

                            <h3>
                                🌓 对比度增强
                            </h3>

                            <a
                                href="${result.contrast}"
                                download
                                class="download-button"
                            >
                                下载图片
                            </a>

                        </div>

                    </div>


                    <!-- 模糊 -->

                    <div class="result-card">

                        <img
                            src="${result.blur}"
                        >

                        <div class="result-info">

                            <h3>
                                🌫️ 强模糊
                            </h3>

                            <a
                                href="${result.blur}"
                                download
                                class="download-button"
                            >
                                下载图片
                            </a>

                        </div>

                    </div>


                </div>
            `;


            resultContainer.appendChild(
                item
            );

        }
    );


    // 下载全部
    downloadAll.href =
        data.zip;


    resultSection.classList.remove(
        "hidden"
    );


    // 自动滚动
    resultSection.scrollIntoView({
        behavior: "smooth"
    });

}