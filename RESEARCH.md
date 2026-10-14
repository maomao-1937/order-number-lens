# 选题记录 — 2026-10-14

价值主张：对批量图片中的长订单编号做本地 OCR 候选提取与人工复核分流。用户任务是“给一批自己的截图/照片，得到逐图编号候选与不一致原因”；非目标是自动入账、保真证明、付款核验或连接美团账号。

一手需求：[V2EX 运营者 2026-04-20/21](https://v2ex.com/t/1207206) 明确说定期处理大量美团订单截图，云 OCR 成本高，拍照图漏中间 3–4 位；[Stack Overflow 2020-05-23](https://stackoverflow.com/questions/61967297/pytesseract-skipping-numbers-while-detecting-text) 有独立用户遇到 12 位数字被 OCR 跳过；[Stack Overflow 2022-10-31](https://stackoverflow.com/questions/74263139/image-recognition-difficulties-with-ocr-reading-numbers-from-a-picture) 有另一人处理反复拍摄的 8 位数字但识别不稳定。后两条是相邻的长数字照片任务，不能证明美团细分市场规模。V2EX 讨论自 4 月延续到 6 月，有 49 条回复，是关注信号但不是付费/留存数据。没有真实美团数据集或用户试用。

竞品核验（GitHub 与搜索/产品页，访问 2026-10-14）：[FP 报销系统](https://github.com/zhangdexuan/fp-reimbursement-system) 为 MIT、本地部署、含订单截图 OCR、但带完整报销审批流程；[ImageToTable 的美团截图提取](https://imagetotable.ai/ja/extract/meituan-order-screenshot) 为在线提取页面。两者说明“识别订单截图”并非空白市场。它们的公开页面未提供可验证的该场景独立用户评价，也未证明用户会选择本 CLI。窄差异是只处理本地批量长编号，并把双预处理不一致、重复、长度异常显式导向人工复核，而不是生成一堆完整报销流程或上传云端。若已有工具的人工校对足够顺畅，本差异就不成立。

技术/版权边界：本项目调用 [RapidOCR](https://github.com/RapidAI/RapidOCR) 公布的 Python API；未复制 FP、ImageToTable 或 RapidOCR 的代码与提示词。结合 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的任务输入/输出视角和 [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) 的角色化反证视角进行审查，而非安装或复制其中 Agent。模型输出和两个图像处理视图高度相关，绝不能当作两个独立读数或完整准确率。合成图仅证明程序能跑，不是美团场景验证。
