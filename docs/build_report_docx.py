"""生成 6–7k 字详细期末报告 Word（含实验图）。"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt

from report_body_text import SECTIONS

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "docs" / "机器学习期末报告_沪租估Agent.docx"
DESKTOP_OUT = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_6to7k.docx"


def set_run_font(run, name="宋体", size=12, bold=False):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = name
    rFonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), name)


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

    # 二 + 架构/流程
    add_heading_cn(doc, SECTIONS[1][0])
    add_para(doc, SECTIONS[1][1][0])
    add_image(doc, RES / "fig_architecture_cn.png", 6.0, "图1 系统设计：模型/工具/数据/人工确认")
    add_para(doc, SECTIONS[1][1][1])
    add_image(doc, RES / "fig_workflow_cn.png", 6.2, "图2 Agent 任务流程")
    for p in SECTIONS[1][1][2:]:
        add_para(doc, p)

    # 三 + 数据图
    add_heading_cn(doc, SECTIONS[2][0])
    for p in SECTIONS[2][1][:2]:
        add_para(doc, p)
    add_image(doc, RES / "fig_district_cn.png", 5.9, "图3 清洗后房源行政区分布")
    add_image(doc, RES / "fig_split_cn.png", 4.4, "图4 训练/验证/测试划分")
    for p in SECTIONS[2][1][2:]:
        add_para(doc, p)

    # 四
    add_heading_cn(doc, SECTIONS[3][0])
    for p in SECTIONS[3][1]:
        add_para(doc, p)

    # 五 + 大量实验图
    add_heading_cn(doc, SECTIONS[4][0])
    add_para(doc, SECTIONS[4][1][0])
    add_para(doc, SECTIONS[4][1][1])
    add_image(doc, RES / "fig_mae_cn.png", 5.7, "图5 测试集 MAE 对照")
    add_image(doc, RES / "fig_r2_mape_cn.png", 6.0, "图6 测试集 R² 与 MAPE")
    add_image(doc, RES / "fig_pred_vs_true_cn.png", 4.7, "图7 预测值 vs 挂牌价")
    add_image(doc, RES / "fig_residual_cn.png", 5.6, "图8 残差分布")
    add_para(doc, SECTIONS[4][1][2])
    add_image(doc, RES / "fig_feature_cn.png", 5.7, "图9 特征影响 Top10")
    add_image(doc, RES / "fig_error_by_rooms_cn.png", 5.5, "图10 分居室误差")
    add_image(doc, RES / "fig_error_by_district_cn.png", 5.7, "图11 分区误差")
    add_image(doc, RES / "fig_failure_cn.png", 5.8, "图12 高误差失败案例")
    add_para(doc, SECTIONS[4][1][3])
    add_para(doc, SECTIONS[4][1][4])
    add_image(doc, RES / "fig_sample_tests_cn.png", 5.7, "图13 样例测试通过情况")
    if (RES / "fig_ablation_cn.png").exists():
        add_image(doc, RES / "fig_ablation_cn.png", 5.7, "图14 消融对照")
    add_para(doc, SECTIONS[4][1][5])
    if (RES / "demo_ui.png").exists():
        add_image(doc, RES / "demo_ui.png", 5.5, "图15 在线原型界面截图")

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
        "scikit-learn 1.6.0（BSD-3-Clause，回归与指标，深入分析对象）；pandas 2.2.3（BSD-3-Clause）；numpy 2.4.6（BSD）；joblib 1.4.2（BSD）；matplotlib 3.10.0（PSF）；streamlit 1.67.0（Apache-2.0）；上海链家租房数据（Junru-Sheng/lianjia_Crawler，学习研究用途）；自研 rent_filter_skill、RentAgent。详见 docs/03、docs/04、data/DATA_SOURCE.md。未提交密钥。",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 B 运行说明、依赖与测试样例")
    add_para(
        doc,
        "依赖：requirements.txt。一键：python run_all.py。网页：python -m streamlit run app.py。测试：tests/sample_queries.json 与 python tests/run_samples.py。主要代码：app.py、src/agent_core.py、skills/rent_filter_skill.py、src/preprocess.py、src/train.py、src/evaluate.py。仓库：https://github.com/Ianhasis/shanghai-rent-agent ；在线：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 C 生成式 AI 使用说明")
    add_para(
        doc,
        "本项目在资料检索、代码编写调试、报告组织与润色中使用了生成式 AI 辅助。作者对内容进行了核验与修改；所有指标来自真实运行，未伪造实验数据。作者能够解释设计、实现与结论。",
        first_line_indent=False,
    )

    doc.save(OUT)
    doc.save(DESKTOP_OUT)

    texts = [p.text for p in doc.paragraphs]
    body = []
    started = False
    for t in texts:
        if t.startswith("一、需求与目标"):
            started = True
        if t.startswith("七、参考文献"):
            break
        if started:
            body.append(t)
    cn = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body)))
    # also count from source text for accuracy excluding captions somewhat - captions have 图 which is fine
    src_cn = len(
        re.findall(
            r"[\u4e00-\u9fff]",
            "\n".join(p for _, sec in SECTIONS for p in sec),
        )
    )
    img_n = sum(1 for r in doc.part.rels.values() if "image" in r.reltype)
    print("saved", OUT)
    print("saved", DESKTOP_OUT)
    print("body_chinese_chars_in_docx", cn)
    print("source_section_chinese_chars", src_cn)
    print("images", img_n)


if __name__ == "__main__":
    main()
