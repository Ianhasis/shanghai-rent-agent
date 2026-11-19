"""生成期末报告 Word：论证优先，插图服务于叙述。"""
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
DESKTOP_OUT = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_论文体例.docx"


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


def add_fig(doc, path: Path, caption: str, width_in: float = 5.5):
    """只放图与图题；分析写在前后正文，避免“一图一段堆结论”。"""
    if not path.exists():
        add_para(doc, f"（缺少图片文件：{path.name}）", first_line_indent=False)
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(path), width=Inches(width_in))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)
    set_run_font(c.add_run(caption), "宋体", 10.5)


def add_shot_placeholder(doc, fig_no: str, title: str, howto: str):
    box = doc.add_paragraph()
    box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    box.paragraph_format.space_before = Pt(6)
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
    c.paragraph_format.space_after = Pt(8)
    set_run_font(c.add_run(f"{fig_no} {title}"), "宋体", 10.5)


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
    cap.paragraph_format.space_after = Pt(8)
    set_run_font(cap.add_run("表1 测试集主要定量结果"), "宋体", 10.5)


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
    add_para(
        doc,
        "图1给出对应的总体结构：网页入口将任务交给编排器，编排器再调度数据工具、回归模型与建议模块，"
        "并在必要时进入人工确认。该图要说明的不是界面装饰，而是“谁调用谁、失败时如何退出”。",
    )
    add_fig(doc, RES / "fig_architecture_cn.png", "图1 系统总体结构", 5.9)
    add_para(doc, SECTIONS[1][1][1])
    add_para(
        doc,
        "把上述逻辑展开为时间顺序，即得到图2的任务流程。与结构图不同，流程图强调步骤先后："
        "先形成可执行参数，再检索与估价，最后生成建议并做安全检查。缺参追问、无匹配提示与高偏差复核，"
        "都是这条链路上的失败分支，而不是事后附加说明。",
    )
    add_fig(doc, RES / "fig_workflow_cn.png", "图2 Agent 任务执行流程", 6.0)
    add_para(doc, SECTIONS[1][1][2])
    add_para(
        doc,
        "在用户侧，上述设计表现为两类任务与两种找房入口。图3用于展示任务入口是否清晰；"
        "完整运行结果将在实验部分与评价问题一并给出，以免在方案章过早陷入界面细节。",
    )
    add_shot_placeholder(
        doc,
        "图3",
        "用户任务入口界面",
        "截取首页：帮我找房 / 判断这套房贵不贵，以及一句话找房 / 精确筛选。",
    )

    # 三
    add_heading_cn(doc, SECTIONS[2][0])
    add_para(doc, SECTIONS[2][1][0])
    add_para(doc, SECTIONS[2][1][1])
    add_para(
        doc,
        "在进入训练细节前，先确认数据工具侧是否具备按区域筛选的条件。图4显示清洗后样本的行政区分布："
        "多区覆盖使区域约束可执行，但分布不均也预示后续分区误差可能不同。图5则给出划分方案，"
        "保证验证与测试职责分离，避免把选模结果误当作最终泛化成绩。",
    )
    add_fig(doc, RES / "fig_district_cn.png", "图4 清洗后房源的行政区分布", 5.8)
    add_fig(doc, RES / "fig_split_cn.png", "图5 训练集、验证集与测试集划分", 4.3)
    add_para(doc, SECTIONS[2][1][2])

    # 四
    add_heading_cn(doc, SECTIONS[3][0])
    for p in SECTIONS[3][1]:
        add_para(doc, p)

    # 五 —— 论证主线
    add_heading_cn(doc, SECTIONS[4][0])
    add_para(doc, SECTIONS[4][1][0])

    add_para(doc, SECTIONS[4][1][1])
    add_metrics_table(doc)
    add_para(
        doc,
        "为把表1中的对比关系可视化，图6聚焦绝对误差，图7同时给出拟合优度与相对误差，图8将 Lasso 与基线并置。"
        "三者共同支撑同一判断：多特征回归优于单价外推；同时相对误差仍高，因而不能取消复核。",
    )
    add_fig(doc, RES / "fig_mae_cn.png", "图6 测试集平均绝对误差（MAE）对照", 5.6)
    add_fig(doc, RES / "fig_r2_mape_cn.png", "图7 测试集 R² 与 MAPE", 5.8)
    add_fig(doc, RES / "fig_metrics_compare_cn.png", "图8 Lasso 与基线关键指标对照", 5.6)

    add_para(doc, SECTIONS[4][1][2])
    add_para(
        doc,
        "对应地，图9用于观察拟合的主体趋势与尾部离散，图10用于观察残差是否对称、是否存在长尾；"
        "图12与图13把误差分解到居室与行政区切片，图14给出高偏差个案。这样，从“平均变好”推进到“哪里仍然不好”，"
        "再自然引出安全策略，而不是先摆图后补理由。",
    )
    add_fig(doc, RES / "fig_pred_vs_true_cn.png", "图9 预测值与挂牌价对照（密度图）", 4.7)
    add_fig(doc, RES / "fig_residual_cn.png", "图10 测试集残差分布", 5.5)

    add_para(doc, SECTIONS[4][1][3])
    add_fig(doc, RES / "fig_feature_cn.png", "图11 Lasso 特征影响（绝对值前十）", 5.6)

    add_para(
        doc,
        "在确认特征方向大体合理后，仍需检查误差的结构性差异与失败形态，否则平均指标会掩盖薄弱输入。",
    )
    add_fig(doc, RES / "fig_error_by_rooms_cn.png", "图12 不同居室条件下的平均绝对误差", 5.3)
    add_fig(doc, RES / "fig_error_by_district_cn.png", "图13 平均误差较高的行政区（前八）", 5.5)
    add_fig(doc, RES / "fig_failure_cn.png", "图14 高百分比误差失败案例", 5.6)

    add_para(doc, SECTIONS[4][1][4])
    add_para(
        doc,
        "图15给出可复现样例通过情况，图16给出关闭模型后的消融对照。若消融后建议能力明显下降，"
        "即可证明回归组件进入了任务闭环。随后用端到端截图核对：自然语言找房、单套判断与边界失败是否都能按设计工作。",
    )
    add_fig(doc, RES / "fig_sample_tests_cn.png", "图15 Agent 可复现样例测试结果", 5.5)
    if (RES / "fig_ablation_cn.png").exists():
        add_fig(doc, RES / "fig_ablation_cn.png", "图16 消融实验：启用与关闭回归模型", 5.6)

    add_para(
        doc,
        "完整运行证据用于把“指标—误差—消融”拉回到真实交互。图17至图19分别对应一句话找房、单套判断与边界处理；"
        "它们不是额外展示，而是对第三问（模型是否进入流程、失败是否可处置）的实例化核查。",
    )
    add_shot_placeholder(
        doc,
        "图17",
        "一句话找房完整运行结果",
        "输入如“闵行预算6000两居，帮我看看划不划算”，截取结论与至少两套房源卡片。",
    )
    add_shot_placeholder(
        doc,
        "图18",
        "单套判断运行结果",
        "在“判断这套房贵不贵”中完成一次判断并截取结果区。",
    )
    add_shot_placeholder(
        doc,
        "图19",
        "异常或边界情形处理",
        "例如预算过低导致无匹配，或提示核实的界面。",
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
        alt = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_论证版.docx"
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
    print("body_chinese_chars_approx", cn)
    print("images", sum(1 for r in doc.part.rels.values() if "image" in r.reltype))


if __name__ == "__main__":
    main()
