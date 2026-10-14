# OrderNumberLens

本地批量提取图片中的长订单编号，并把识别不一致、长度不符、重复或未找到的图片明确列入人工复核队列。它适合需要处理自己持有的订单截图/拍照图片、又不想把图片送到云 OCR 的小团队。它**不是**报销系统、账务对账工具或准确率保证。

核心识别是真实的 [RapidOCR](https://github.com/RapidAI/RapidOCR) 本地 ONNX OCR 模型，不是字符串假数据。每张图运行原图与增强图两次 OCR，提取“订单号 / Order No”附近的长数字。两次一致仅标为 `consistent_candidate`，**仍需对照原图人工核对**；同一模型的两次结果并非独立证据，可能一起认错。

## 安装与演示

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)。在仓库根目录：

```sh
uv sync --python 3.11 --extra test
uv run python examples/make_demo.py --out demo.local.png
uv run order-number-lens demo.local.png --expected-length 16 --csv-out review.local.csv --json-out review.local.json
uv run pytest -q
```

默认示例是英文标签的**虚构**订单图，编号为 `1234567890123456`。若你的机器有支持中文的字体，可生成中文标签示例，例如 macOS：

```sh
uv run python examples/make_demo.py --font '/System/Library/Fonts/Hiragino Sans GB.ttc' --out demo-zh.local.png
uv run order-number-lens demo-zh.local.png --expected-length 16
```

批量处理自己的图片目录（只扫描目录第一层，不自动递归、不改名、不删除原图）：

```sh
uv run order-number-lens /path/to/your-images --expected-length 16 --csv-out review.local.csv
```

支持 PNG/JPEG/WebP/BMP。`--expected-length` 是你根据真实业务格式提供的约束；不确定时可省略，但风险更高。CSV 供人工审阅，不应直接导入生产业务系统。JSON 还包含 OCR 看到的局部文本和分数，可能含敏感信息；请保存在本地，不要提交真实订单图片或报告到公开仓库。初次安装会下载 Python 依赖；RapidOCR 运行时可能准备其本地模型文件。之后识别过程不调用付费 OCR API，也不会上传图片。

状态含义：`consistent_candidate` 只是两次本地处理给出相同数字；`review_needed` 表示结果不一致、只有一次识别到、长度不合、图片出错或批次中重复；`not_found` 表示没有在标签附近找到 8–25 位数字。OCR 分数不是“编号正确概率”。实际美团图片版式、模糊/反光/遮挡、订单号格式、平台改版均未在真实样本上验证。中文样例也只是合成图片，不代表业务准确率。

## 设计判断与下一步

现有本地报销套件和云端图片提取服务已覆盖通用 OCR；本项目只尝试解决“批次中哪些长编号值得人工核对”的窄任务，避免将识别结果伪装成已确认记录。研究来源、替代品和负面证据见 [RESEARCH.md](RESEARCH.md)。要验证价值，应在获得授权且脱敏的至少 50 张真实截图与拍照图片上，由人建立编号真值，分别统计完整正确率、漏报、误报和复核耗时，再与现有工作流比较。在此之前，不建议无人值守地采用结果。

代码采用 MIT；RapidOCR 及模型有各自许可证，请核对其上游条款。
