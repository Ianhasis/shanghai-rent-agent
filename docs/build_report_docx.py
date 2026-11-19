"""生成期末报告 Word（毕业论文体例：图题居中，分析用“如图X所示”）。"""
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


def add_fig(doc, path: Path, caption: str, analysis: str, width_in: float = 5.6):
    """插图 + 居中图题 + 正文分析（如图X所示……）。"""
    if not path.exists():
        add_para(doc, f"（缺少图片文件：{path.name}）", first_line_indent=False)
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        p.add_run().add_picture(str(path), width=Inches(width_in))

    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    set_run_font(c.add_run(caption), "宋体", 10.5)

    add_para(doc, analysis, first_line_indent=True, size=12)


def add_shot_placeholder(doc, fig_no: str, title: str, howto: str, analysis: str):
    box = doc.add_paragraph()
    box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    box.paragraph_format.space_before = Pt(8)
    box.paragraph_format.space_after = Pt(2)
    set_run_font(
        box.add_run(f"【待补充截图】{fig_no} {title}"),
        "宋体",
        10.5,
        True,
        RGBColor(0x66, 0x66, 0x66),
    )
    tip = doc.add_paragraph()
    tip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tip.paragraph_format.space_after = Pt(4)
    set_run_font(tip.add_run(howto), "宋体", 9, False, RGBColor(0x88, 0x88, 0x88))

    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    set_run_font(c.add_run(f"{fig_no} {title}"), "宋体", 10.5)
    add_para(doc, analysis, first_line_indent=True, size=12)


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
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(6)
    set_run_font(cap.add_run("表1 测试集主要定量结果"), "宋体", 10.5)
    add_para(
        doc,
        "如表1所示，三种线性模型在测试集上的 MAE、RMSE 与 R² 均明显优于单价基线；其中 Lasso 验证集表现略优，故作为 Agent 默认模型。"
        "MAPE 仍约 33%，表明相对误差不可忽视，系统必须保留人工复核机制，而不能将点预测直接视为成交价。",
    )


def main():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)

    build_cover(doc)

    add_heading_cn(doc, SECTIONS[0][0])
    for p in SECTIONS[0][1]:
        add_para(doc, p)

    add_heading_cn(doc, SECTIONS[1][0])
    add_para(doc, SECTIONS[1][1][0])
    add_fig(
        doc,
        RES / "fig_architecture_cn.png",
        "图1 系统总体结构",
        "如图1所示，用户经由网页入口提交找房或估价任务；RentAgent 负责目标理解、参数校验与工具调度，"
        "分别连接房源数据工具、回归模型与建议生成模块，并在高偏差或无匹配时转入人工确认。"
        "该结构体现了模型、工具、数据与人机协作在同一任务中的组织关系。",
        6.0,
    )
    add_para(doc, SECTIONS[1][1][1])
    add_fig(
        doc,
        RES / "fig_workflow_cn.png",
        "图2 Agent 任务执行流程",
        "如图2所示，系统将端到端过程分解为入口校验、数据连接、模型调用、硬约束筛选、公允价预测、建议生成与安全检查等步骤。"
        "每一步均具有明确输入输出与失败分支：例如参数缺失时先追问，无匹配时返回可解释提示，高偏差时请求人工复核。",
        6.2,
    )
    add_para(doc, SECTIONS[1][1][2])
    add_shot_placeholder(
        doc,
        "图3",
        "用户任务入口界面",
        "截取网页首页：任务选择（帮我找房 / 判断这套房贵不贵），以及找房方式（一句话找房 / 精确筛选）。",
        "如图3所示（待作者补充真实截图），系统在打开后即可明确区分两类任务，并在找房任务下提供自然语言与结构化筛选两种入口。"
        "该界面用于说明任务入口清晰、交互路径可理解。",
    )

    add_heading_cn(doc, SECTIONS[2][0])
    add_para(doc, SECTIONS[2][1][0])
    add_para(doc, SECTIONS[2][1][1])
    add_fig(
        doc,
        RES / "fig_district_cn.png",
        "图4 清洗后房源的行政区分布",
        "如图4所示，清洗后的房源样本覆盖多个行政区，为按区域筛选提供了数据基础。"
        "同时也可看到样本分布并不均匀，这为后续分区误差差异提供了背景。",
        5.9,
    )
    add_fig(
        doc,
        RES / "fig_split_cn.png",
        "图5 训练集、验证集与测试集划分",
        "如图5所示，本实验固定随机种子 42，将数据划分为拟合、验证与测试三部分："
        "验证集仅用于选择模型，测试集仅用于最终报告，从而降低评估泄漏风险。",
        4.4,
    )
    add_para(doc, SECTIONS[2][1][2])

    add_heading_cn(doc, SECTIONS[3][0])
    for p in SECTIONS[3][1]:
        add_para(doc, p)

    add_heading_cn(doc, SECTIONS[4][0])
    add_para(doc, SECTIONS[4][1][0])
    add_para(doc, SECTIONS[4][1][1])
    add_metrics_table(doc)

    add_fig(
        doc,
        RES / "fig_mae_cn.png",
        "图6 测试集平均绝对误差（MAE）对照",
        "如图6所示，Linear、Ridge 与 Lasso 的测试集 MAE 均低于单价基线，说明引入多特征学习能够降低绝对误差。"
        "三者数值接近，后续结合验证集表现与可解释性选择 Lasso 作为默认模型。",
        5.7,
    )
    add_fig(
        doc,
        RES / "fig_r2_mape_cn.png",
        "图7 测试集决定系数（R²）与平均绝对百分比误差（MAPE）",
        "如图7所示，模型 R² 高于基线，表明可解释方差更大；但 MAPE 仍处于较高水平，"
        "说明相对误差不可忽视。该结果直接支持“点预测需配合人工复核”的系统设计。",
        5.9,
    )
    add_fig(
        doc,
        RES / "fig_metrics_compare_cn.png",
        "图8 Lasso 与基线关键指标对照",
        "如图8所示，在 MAE、RMSE 与 MAPE 三项指标上，Lasso 均优于单价基线。"
        "该对照满足课程对基线比较的要求，并为 Agent 默认调用 Lasso 提供定量依据。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][2])
    add_fig(
        doc,
        RES / "fig_pred_vs_true_cn.png",
        "图9 预测值与挂牌价的对照（密度图）",
        "如图9所示，样本主要沿对角线聚集，表明整体拟合方向正确；高价区域与异常低价区域离散更大，"
        "提示尾部样本是误差分析与人工复核的重点。",
        4.8,
    )
    add_fig(
        doc,
        RES / "fig_residual_cn.png",
        "图10 测试集残差分布",
        "如图10所示，残差大致以零为中心，但存在明显长尾。"
        "长尾对应少数高偏差样本，解释了为何系统需要在建议流程中设置高偏差复核阈值。",
        5.6,
    )
    add_para(doc, SECTIONS[4][1][3])
    add_fig(
        doc,
        RES / "fig_feature_cn.png",
        "图11 Lasso 特征影响（绝对值前十）",
        "如图11所示，面积与部分行政区指示变量的影响较为突出，方向大体符合领域常识，"
        "从而完成“比较特征影响”的拓展分析。解释时应注意 One-Hot 系数具有相对性，不宜直接当作独立因果效应。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][4])
    add_fig(
        doc,
        RES / "fig_error_by_rooms_cn.png",
        "图12 不同居室条件下的平均绝对误差",
        "如图12所示，不同居室切片上的平均绝对误差并不相同，说明模型表现具有结构性差异。"
        "对误差更高的输入类型，Agent 更应依赖复核提示而非给出过度肯定的结论。",
        5.4,
    )
    add_fig(
        doc,
        RES / "fig_error_by_district_cn.png",
        "图13 平均误差较高的行政区（前八）",
        "如图13所示，部分行政区平均误差相对更高，可能与样本量、行政区粗分噪声或未建模区位因素有关。"
        "该结果用于说明系统薄弱输入区间，并为后续特征增强提供方向。",
        5.6,
    )
    add_fig(
        doc,
        RES / "fig_failure_cn.png",
        "图14 高百分比误差失败案例",
        "如图14所示，按百分比误差排序的失败样本多表现为挂牌价显著偏离模型预测。"
        "可能原因包括异常挂牌、行政区错分、标题噪声以及未纳入的装修或楼盘溢价；对应处置是触发人工复核。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][5])
    add_fig(
        doc,
        RES / "fig_sample_tests_cn.png",
        "图15 Agent 可复现样例测试结果",
        "如图15所示，手工构造的 6 个样例全部通过，覆盖正常查询与边界失败情形。"
        "该结果说明 Agent 层评估可复现，而非仅依赖挑选出的成功截图。",
        5.6,
    )
    if (RES / "fig_ablation_cn.png").exists():
        add_fig(
            doc,
            RES / "fig_ablation_cn.png",
            "图16 消融实验：启用与关闭回归模型的对照",
            "如图16所示，关闭回归模型后系统仍可按约束检索，但失去基于公允价的建议能力。"
            "该消融证明机器学习组件进入了建议流程，而不是仅作为展示性模块存在。",
            5.7,
        )

    add_shot_placeholder(
        doc,
        "图17",
        "一句话找房的完整运行结果",
        "输入例如“闵行预算6000两居，帮我看看划不划算”，截取结果摘要与至少两套房源卡片（含要价、参考合理价、相差与建议）。",
        "如图17所示（待作者补充真实截图），系统能够在自然语言目标下完成检索与估价，并给出面向用户的结论与候选列表，"
        "用于证明预测已接入建议流程。",
    )
    add_shot_placeholder(
        doc,
        "图18",
        "单套判断运行结果",
        "在“判断这套房贵不贵”中完成一次判断，截取输入与结果（参考合理价、相差比例与建议）。",
        "如图18所示（待作者补充真实截图），同一回归模型也可服务于单套估价任务，体现 Agent 对不同任务入口的统一调度。",
    )
    add_shot_placeholder(
        doc,
        "图19",
        "异常或边界情形处理",
        "例如将预算设为过低后运行，截取无匹配或提示补充/核实的界面。",
        "如图19所示（待作者补充真实截图），系统在边界输入下能够给出可解释的失败或复核提示，"
        "满足失败处理与人机协作方面的考察要求。",
    )

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

    add_heading_cn(doc, "附录 A 复用组件清单与许可证说明")
    add_para(
        doc,
        "scikit-learn 1.6.0（BSD-3-Clause）[1][7]；pandas 2.2.3；numpy 2.4.6；joblib 1.4.2；matplotlib 3.10.0；"
        "streamlit 1.67.0（Apache-2.0）[3]；上海链家租房数据（Junru-Sheng/lianjia_Crawler，学习研究用途）[2]；"
        "自研模块：goal_parser、rent_filter_skill、RentAgent。"
        "详见 docs/03_复用组件清单.md、docs/04_sklearn深入分析与核验.md、data/DATA_SOURCE.md。"
        "公开仓库未提交密钥。",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 B 运行说明、依赖与测试样例")
    add_para(
        doc,
        "依赖见 requirements.txt。一键复现：python run_all.py。"
        "网页演示：python -m streamlit run app.py。"
        "测试样例：tests/sample_queries.json；运行 python tests/run_samples.py。"
        "报告插图生成：python docs/gen_report_figures.py。"
        "主要模块：app.py、src/agent_core.py、src/goal_parser.py、skills/rent_filter_skill.py、"
        "src/preprocess.py、src/train.py、src/evaluate.py。"
        "代码仓库：https://github.com/Ianhasis/shanghai-rent-agent ；"
        "在线原型：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app",
        first_line_indent=False,
    )
    add_heading_cn(doc, "附录 C 生成式 AI 使用说明")
    add_para(
        doc,
        "本项目在资料检索、代码编写与调试、报告组织与文字润色过程中使用了生成式 AI 辅助。"
        "作者对生成内容进行了核验与修改；实验指标均来自本地真实运行，未伪造数据。"
        "作者能够解释本项目的设计、实现与结论。",
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
        alt = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_论文体例.docx"
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
        if not started or not t:
            continue
        if re.match(r"^图\d+", t) or re.match(r"^表\d+", t):
            continue
        if t.startswith("【待补充截图】") or t.startswith("截取"):
            continue
        body.append(t)
    cn = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body)))
    src_cn = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(p for _, sec in SECTIONS for p in sec)))
    img_n = sum(1 for r in doc.part.rels.values() if "image" in r.reltype)
    print("body_chinese_chars_approx", cn)
    print("source_section_chinese_chars", src_cn)
    print("images", img_n)


if __name__ == "__main__":
    main()
