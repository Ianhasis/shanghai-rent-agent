"""生成期末报告 Word（含实验图与截图占位）。运行：python docs/build_report_docx.py"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from report_body_text import SECTIONS

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "docs" / "机器学习期末报告_沪租估Agent.docx"
DESKTOP_OUT = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_6to7k.docx"


def set_run_font(run, name="宋体", size=12, bold=False, color=None):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = name
    rFonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), name)
    if color is not None:
        run.font.color.rgb = color


def add_heading_cn(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run_font(run, "黑体", 16 if level == 1 else 13, True)


def add_para(doc, text, first_line_indent=True, size=12):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    if first_line_indent:
        pf.first_line_indent = Cm(0.74)
    set_run_font(p.add_run(text), "宋体", size)
    return p


def add_image(doc, path: Path, width_in=5.7, caption: str | None = None):
    if not path.exists():
        add_para(doc, f"（缺图：{path.name}）", first_line_indent=False)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width_in))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(c.add_run(caption), "宋体", 10.5)


def add_shot_placeholder(doc, title: str, howto: str):
    """截图占位：请作者自行截取后替换。"""
    box = doc.add_paragraph()
    box.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = box.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(4)
    run = box.add_run(f"【请自行截图替换】{title}")
    set_run_font(run, "黑体", 11, True, RGBColor(0x9A, 0x34, 0x12))

    tip = doc.add_paragraph()
    tip.paragraph_format.space_after = Pt(10)
    tip.paragraph_format.left_indent = Cm(0.3)
    set_run_font(tip.add_run(howto), "宋体", 10.5, False, RGBColor(0x5B, 0x6B, 0x7C))


def build_cover(doc: Document):
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(t.add_run("“机器学习”课程期末报告"), "黑体", 22, True)
    doc.add_paragraph()
    rows = [
        ("题    目", "上海整租租金公允估价与筛选 Agent（沪租估）"),
        ("学    院", "电子电气工程学院"),
        ("专    业", ""),
        ("学    号", ""),
        ("姓    名", ""),
        ("课程教师", ""),
        ("完成日期", date.today().strftime("%Y年%m月%d日")),
        ("组员分工", "个人完成（如有组员请自行补充）"),
    ]
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    for i, (k, v) in enumerate(rows):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = v
        for cell in (table.cell(i, 0), table.cell(i, 1)):
            for p in cell.paragraphs:
                for run in p.runs:
                    set_run_font(run, "宋体", 12)
    tip = doc.add_paragraph()
    tip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(tip.add_run("（姓名、学号、专业、课程教师请自行填写）"), "宋体", 10.5)
    doc.add_page_break()


def add_metrics_table(doc: Document):
    add_para(doc, "表1 给出测试集上主要定量结果（数值来自 results/train_report.json）。", False)
    table = doc.add_table(rows=5, cols=5)
    table.style = "Table Grid"
    headers = ["模型", "MAE", "RMSE", "R²", "MAPE%"]
    data = [
        ["Linear", "2244.9", "3205.8", "0.695", "33.71"],
        ["Ridge", "2244.6", "3205.9", "0.695", "33.70"],
        ["Lasso（选用）", "2243.3", "3206.6", "0.695", "33.66"],
        ["基线（单价×面积）", "2968.6", "4256.9", "0.463", "42.69"],
    ]
    for j, h in enumerate(headers):
        table.cell(0, j).text = h
    for i, row in enumerate(data, 1):
        for j, v in enumerate(row):
            table.cell(i, j).text = v
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    set_run_font(run, "宋体", 10.5)
    doc.add_paragraph()


def main():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)

    build_cover(doc)

    # 一
    add_heading_cn(doc, SECTIONS[0][0])
    for p in SECTIONS[0][1]:
        add_para(doc, p)

    # 二
    add_heading_cn(doc, SECTIONS[1][0])
    add_para(doc, SECTIONS[1][1][0])
    add_image(doc, RES / "fig_architecture_cn.png", 6.0, "图1 系统设计：模型 / 工具 / 数据 / 人工确认")
    add_para(doc, SECTIONS[1][1][1])
    add_image(doc, RES / "fig_workflow_cn.png", 6.2, "图2 Agent 任务流程")

    add_shot_placeholder(
        doc,
        "截图A · 任务入口（找房模式）",
        "打开在线原型，选择「帮我找房」。截取整页上半部分：标题「沪租估」、模式切换、预算/区域/居室/面积/想看几套、以及「开始帮我找」按钮。"
        "建议参数：预算 6000，区域 浦东，居室 不限，面积 30–80，想看几套 8。"
        "在线地址：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app/",
    )

    # 三
    add_heading_cn(doc, SECTIONS[2][0])
    for p in SECTIONS[2][1][:2]:
        add_para(doc, p)
    add_image(doc, RES / "fig_district_cn.png", 5.9, "图3 清洗后房源行政区分布")
    add_image(doc, RES / "fig_split_cn.png", 4.4, "图4 训练 / 验证 / 测试划分")
    add_para(doc, SECTIONS[2][1][2])

    # 四
    add_heading_cn(doc, SECTIONS[3][0])
    for p in SECTIONS[3][1]:
        add_para(doc, p)

    # 五
    add_heading_cn(doc, SECTIONS[4][0])
    add_para(doc, SECTIONS[4][1][0])
    add_para(doc, SECTIONS[4][1][1])
    add_metrics_table(doc)
    add_image(doc, RES / "fig_mae_cn.png", 5.7, "图5 测试集 MAE 对照")
    add_image(doc, RES / "fig_r2_mape_cn.png", 5.9, "图6 测试集 R² 与 MAPE")
    add_image(doc, RES / "fig_metrics_compare_cn.png", 5.7, "图7 Lasso 与基线关键指标对照")
    add_image(doc, RES / "fig_pred_vs_true_cn.png", 4.8, "图8 预测值 vs 挂牌价（密度图）")
    add_image(doc, RES / "fig_residual_cn.png", 5.6, "图9 残差分布")
    add_image(doc, RES / "fig_feature_cn.png", 5.7, "图10 Lasso 特征影响 Top10")
    add_image(doc, RES / "fig_error_by_rooms_cn.png", 5.4, "图11 分居室误差")
    add_image(doc, RES / "fig_error_by_district_cn.png", 5.6, "图12 分区误差")
    add_image(doc, RES / "fig_failure_cn.png", 5.7, "图13 高误差失败案例")
    add_para(doc, SECTIONS[4][1][2])
    add_image(doc, RES / "fig_sample_tests_cn.png", 5.6, "图14 Agent 样例测试通过情况")
    if (RES / "fig_ablation_cn.png").exists():
        add_image(doc, RES / "fig_ablation_cn.png", 5.7, "图15 消融对照")

    add_shot_placeholder(
        doc,
        "截图B · 完整运行结果（找房）",
        "在截图A相同参数下点击「开始帮我找」。截取结果区：至少 2–3 条房源卡片，必须能看清「房东要价」「参考合理价」「大概相差」和建议标签（价格正常/可能偏贵/相对划算等）。"
        "若出现“差得比较多，建议再确认”的提示，一并截入。",
    )
    add_shot_placeholder(
        doc,
        "截图C · 单套判断模式",
        "切换到「判断这套房贵不贵」。填写：区域浦东、面积约60、2室1厅、朝向南、勾选地铁、房东要价自定（如6000）。点击「帮我判断」，截取输入区与结果区（参考合理价、相差比例、建议标签）。",
    )
    add_shot_placeholder(
        doc,
        "截图D · 异常/边界处理（任选其一）",
        "任选一种：(1) 预算改成极低如1200后点开始，截取“暂时没有合适房源”或提示放宽条件；"
        "或 (2) 面积范围调成上界小于下界（若界面允许）/未知区域场景的失败提示。"
        "目的：证明系统有失败处理与人工确认提示，而不是只展示成功案例。",
    )

    # 六
    add_heading_cn(doc, SECTIONS[5][0])
    for p in SECTIONS[5][1]:
        add_para(doc, p)

    add_heading_cn(doc, "七、参考文献")
    for r in [
        "[1] Pedregosa F, et al. Scikit-learn: Machine Learning in Python. JMLR, 2011. https://scikit-learn.org/",
        "[2] Junru-Sheng. lianjia_Crawler（上海链家租房数据整理）. GitHub. https://github.com/Junru-Sheng/lianjia_Crawler",
        "[3] Streamlit Inc. Streamlit Documentation. https://docs.streamlit.io/",
        "[4] 李航. 统计学习方法. 清华大学出版社.",
        "[5] Hastie T, Tibshirani R, Friedman J. The Elements of Statistical Learning. Springer.",
        "[6] 《机器学习》课程讲义：回归、正则化、模型评估与实验设计相关内容.",
        "[7] scikit-learn User Guide: Linear Models. https://scikit-learn.org/stable/modules/linear_model.html",
    ]:
        add_para(doc, r, first_line_indent=False)

    add_heading_cn(doc, "附录 A 复用组件清单与许可证/来源")
    add_para(
        doc,
        "scikit-learn 1.6.0（BSD-3-Clause）；pandas 2.2.3；numpy 2.4.6；joblib 1.4.2；matplotlib 3.10.0；"
        "streamlit 1.67.0（Apache-2.0）；上海链家租房数据（Junru-Sheng/lianjia_Crawler，学习研究用途）；"
        "自研 rent_filter_skill、RentAgent。详见 docs/03_复用组件清单.md、docs/04_sklearn深入分析与核验.md、"
        "data/DATA_SOURCE.md。仓库未提交密钥。",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 B 运行说明、依赖与测试样例")
    add_para(
        doc,
        "依赖：requirements.txt。一键复现：python run_all.py。"
        "网页：python -m streamlit run app.py。"
        "测试：tests/sample_queries.json；python tests/run_samples.py。"
        "报告图：python docs/gen_report_figures.py。"
        "主要模块：app.py、src/agent_core.py、skills/rent_filter_skill.py、src/preprocess.py、src/train.py、src/evaluate.py。"
        "仓库：https://github.com/Ianhasis/shanghai-rent-agent ；"
        "在线：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 C 生成式 AI 使用说明")
    add_para(
        doc,
        "本项目在资料检索、代码编写调试、报告组织与润色中使用了生成式 AI 辅助。"
        "作者对内容进行了核验与修改；全部指标来自真实运行，未伪造实验数据。"
        "作者能够解释设计、实现与结论。",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 D 截图清单（请作者完成后删除本附录说明）")
    add_para(
        doc,
        "请将上文红色标注的截图A–D替换为真实页面截图后，删除本附录。"
        "截图时建议使用浏览器全页或窗口截图，保证标题、输入与结果可读；不必截取代码编辑器。",
        first_line_indent=False,
    )

    try:
        doc.save(OUT)
        print("saved", OUT)
    except Exception as e:
        print("save repo docx failed:", e)
    try:
        doc.save(DESKTOP_OUT)
        print("saved", DESKTOP_OUT)
    except Exception as e:
        alt = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_评分对齐版.docx"
        doc.save(alt)
        print("desktop locked, saved", alt, "err", e)

    texts = [p.text for p in doc.paragraphs]
    body = []
    started = False
    for t in texts:
        if t.startswith("一、需求与目标"):
            started = True
        if t.startswith("七、参考文献"):
            break
        if started and not t.startswith("【请自行截图") and not t.startswith("图") and not t.startswith("表"):
            body.append(t)
    cn = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body)))
    src_cn = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(p for _, sec in SECTIONS for p in sec)))
    img_n = sum(1 for r in doc.part.rels.values() if "image" in r.reltype)
    print("body_chinese_chars_approx", cn)
    print("source_section_chinese_chars", src_cn)
    print("images", img_n)


if __name__ == "__main__":
    main()
