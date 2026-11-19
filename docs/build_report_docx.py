"""生成期末报告 Word（依据本科毕业论文常用规范：客观陈述、先文后图）。"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from report_body_text import REFERENCES, SECTIONS

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "docs" / "机器学习期末报告_沪租估Agent.docx"
DESKTOP_OUT = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_图号连续版.docx"
DESKTOP_OUT_ALT = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_请打开此文件.docx"


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


def add_para(doc, text, first_line_indent=True, size=12, cite_superscript=True):
    """正文段落；方括号文献序号按 GB/T 7714 习惯设为上角标。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    if first_line_indent:
        pf.first_line_indent = Cm(0.74)
    if not cite_superscript:
        set_run_font(p.add_run(text), "宋体", size)
        return p
    parts = re.split(r"(\[[0-9,\-\s]+\])", text)
    for part in parts:
        if not part:
            continue
        run = p.add_run(part)
        if re.fullmatch(r"\[[0-9,\-\s]+\]", part):
            set_run_font(run, "宋体", 9)
            run.font.superscript = True
        else:
            set_run_font(run, "宋体", size)
    return p


def add_fig(doc, path: Path, caption: str, width_in: float = 5.5):
    if not path.exists():
        add_para(doc, f"（缺少图片文件：{path.name}）", first_line_indent=False)
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(path), width=Inches(width_in))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    set_run_font(c.add_run(caption), "宋体", 10.5)


def add_shot_placeholder(doc, fig_no: str, title: str):
    box = doc.add_paragraph()
    box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    box.paragraph_format.space_before = Pt(8)
    box.paragraph_format.space_after = Pt(2)
    set_run_font(
        box.add_run(f"【待补充截图】"),
        "宋体",
        10.5,
        True,
        RGBColor(0x66, 0x66, 0x66),
    )
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
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
    cap.paragraph_format.space_after = Pt(10)
    set_run_font(cap.add_run("表1 测试集主要定量结果"), "宋体", 10.5)


def main():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)

    build_cover(doc)
    s1, s2, s3, s4, s5, s6 = SECTIONS

    # 一
    add_heading_cn(doc, s1[0])
    for p in s1[1]:
        add_para(doc, p)

    # 二：段1 → 段2+图1 → 段3前半+图2 → 段3后半+图3 → 段4
    add_heading_cn(doc, s2[0])
    add_para(doc, s2[1][0])
    add_para(doc, s2[1][1])
    add_fig(doc, RES / "fig_architecture_cn.png", "图1 系统总体结构", 5.9)
    # 段3含图2与图3引用：拆成两段以便插图
    p3 = s2[1][2]
    split_marker = "用户任务入口界面如图3所示"
    if split_marker in p3:
        before, after = p3.split(split_marker, 1)
        add_para(doc, before.strip())
        add_fig(doc, RES / "fig_workflow_cn.png", "图2 Agent 任务执行流程", 6.0)
        add_para(doc, split_marker + after)
        add_shot_placeholder(doc, "图3", "用户任务入口界面")
    else:
        add_para(doc, p3)
        add_fig(doc, RES / "fig_workflow_cn.png", "图2 Agent 任务执行流程", 6.0)
        add_shot_placeholder(doc, "图3", "用户任务入口界面")
    add_para(doc, s2[1][3])

    # 三：问题→数据→特征→模型→划分(图4/5)→接入任务
    add_heading_cn(doc, s3[0])
    for i in range(5):
        add_para(doc, s3[1][i])
    add_fig(doc, RES / "fig_district_cn.png", "图4 清洗后房源的行政区分布", 5.8)
    add_fig(doc, RES / "fig_split_cn.png", "图5 训练集、验证集与测试集划分", 4.3)
    add_para(doc, s3[1][5])
    add_para(doc, s3[1][6])

    # 四
    add_heading_cn(doc, s4[0])
    for p in s4[1]:
        add_para(doc, p)

    # 五：先引述、再插图；图号按出现顺序 6→19 连续
    p5 = s5[1]
    add_heading_cn(doc, s5[0])
    add_para(doc, p5[0])
    add_para(doc, p5[1])
    add_metrics_table(doc)

    add_para(doc, p5[2])
    add_fig(doc, RES / "fig_mae_cn.png", "图6 测试集平均绝对误差（MAE）对照", 5.6)
    add_para(doc, p5[3])
    add_fig(doc, RES / "fig_r2_mape_cn.png", "图7 测试集决定系数（R²）与平均绝对百分比误差（MAPE）", 5.8)
    add_para(doc, p5[4])
    add_fig(doc, RES / "fig_metrics_compare_cn.png", "图8 Lasso 与基线关键指标对照", 5.6)

    add_para(doc, p5[5])
    add_fig(doc, RES / "fig_pred_vs_true_cn.png", "图9 预测值与挂牌价对照（密度图）", 4.7)
    add_para(doc, p5[6])
    add_fig(doc, RES / "fig_residual_cn.png", "图10 测试集残差分布", 5.5)
    add_para(doc, p5[7])
    add_fig(doc, RES / "fig_error_by_rooms_cn.png", "图11 不同居室条件下的平均绝对误差", 5.3)
    add_para(doc, p5[8])
    add_fig(doc, RES / "fig_error_by_district_cn.png", "图12 平均误差较高的行政区（前八）", 5.5)
    add_para(doc, p5[9])
    add_fig(doc, RES / "fig_failure_cn.png", "图13 高百分比误差失败案例", 5.6)

    add_para(doc, p5[10])
    add_fig(doc, RES / "fig_feature_cn.png", "图14 Lasso 特征影响（绝对值前十）", 5.6)

    add_para(doc, p5[11])
    add_fig(doc, RES / "fig_sample_tests_cn.png", "图15 Agent 可复现样例测试结果", 5.5)
    add_para(doc, p5[12])
    if (RES / "fig_ablation_cn.png").exists():
        add_fig(doc, RES / "fig_ablation_cn.png", "图16 消融实验：启用与关闭回归模型", 5.6)
    add_para(doc, p5[13])
    add_shot_placeholder(doc, "图17", "一句话找房完整运行结果")
    add_shot_placeholder(doc, "图18", "单套判断运行结果")
    add_shot_placeholder(doc, "图19", "异常或边界情形处理结果")

    # 六
    add_heading_cn(doc, s6[0])
    for p in s6[1]:
        add_para(doc, p)

    add_heading_cn(doc, "七、参考文献")
    for r in REFERENCES:
        add_para(doc, r, first_line_indent=False, cite_superscript=False)

    add_heading_cn(doc, "附录 A 复用组件清单与许可证说明")
    add_para(
        doc,
        "scikit-learn 1.6.0（BSD-3-Clause）[4-5]；pandas 2.2.3；numpy 2.4.6；joblib 1.4.2；matplotlib 3.10.0；"
        "streamlit 1.67.0（Apache-2.0）[6]；上海链家租房数据（Junru-Sheng/lianjia_Crawler，学习研究用途）[7]；"
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

    for dest in (OUT, DESKTOP_OUT, DESKTOP_OUT_ALT):
        try:
            doc.save(dest)
            print("saved", dest)
        except Exception as e:
            print("save failed:", dest, e)

    # 校验：图题必须按 1..N 连续出现
    fig_caps = []
    for t in doc.paragraphs:
        m = re.match(r"^图(\d+)\s", t.text.strip())
        if m:
            fig_caps.append(int(m.group(1)))
    expected = list(range(1, len(fig_caps) + 1))
    print("figure_caption_order", fig_caps)
    if fig_caps != expected:
        raise SystemExit(f"FIGURE ORDER BROKEN: got {fig_caps}, expected {expected}")
    print("figure_order_ok", True)

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
        if t.startswith("【待补充截图】"):
            continue
        body.append(t)
    print("body_chinese_chars_approx", len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body))))
    print("images", sum(1 for r in doc.part.rels.values() if "image" in r.reltype))


if __name__ == "__main__":
    main()
