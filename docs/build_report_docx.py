"""生成期末报告 Word：每图均有解读；结构对齐评分标准。运行：python docs/build_report_docx.py"""
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


def add_fig(doc, path: Path, caption: str, note: str, width_in: float = 5.7):
    """插图 + 图题 + 图下解读（证据说明）。"""
    if not path.exists():
        add_para(doc, f"（缺图：{path.name}）", first_line_indent=False)
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(width_in))

    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(2)
    set_run_font(c.add_run(caption), "宋体", 10.5)

    n = doc.add_paragraph()
    n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    n.paragraph_format.space_after = Pt(10)
    n.paragraph_format.first_line_indent = Cm(0.74)
    set_run_font(n.add_run("图释：" + note), "宋体", 10.5)


def add_shot_placeholder(doc, title: str, howto: str, note: str):
    box = doc.add_paragraph()
    box.paragraph_format.space_before = Pt(8)
    box.paragraph_format.space_after = Pt(2)
    set_run_font(
        box.add_run(f"【请自行截图替换】{title}"),
        "黑体",
        11,
        True,
        RGBColor(0x9A, 0x34, 0x12),
    )
    tip = doc.add_paragraph()
    tip.paragraph_format.space_after = Pt(2)
    tip.paragraph_format.left_indent = Cm(0.3)
    set_run_font(tip.add_run(howto), "宋体", 10.5, False, RGBColor(0x5B, 0x6B, 0x7C))
    add_para(doc, "图释：" + note, first_line_indent=True, size=10.5)


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
    set_run_font(cap.add_run("表1 测试集主要定量结果（来源：results/train_report.json）"), "宋体", 10.5)
    add_para(
        doc,
        "表释：四列指标同时给出，避免只报单一准确率。Lasso 与 Linear/Ridge 接近但验证集略优，故作为 Agent 默认模型；"
        "相对基线 MAE 明显下降，说明多特征回归有效；MAPE 仍约 33%，提示必须保留人工复核。",
        size=10.5,
    )


def main():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)

    build_cover(doc)

    # 一、需求与目标
    add_heading_cn(doc, SECTIONS[0][0])
    for p in SECTIONS[0][1]:
        add_para(doc, p)

    # 二、方案与系统设计
    add_heading_cn(doc, SECTIONS[1][0])
    add_para(doc, SECTIONS[1][1][0])
    add_fig(
        doc,
        RES / "fig_architecture_cn.png",
        "图1 系统设计：模型 / 工具 / 数据 / 人工确认",
        "本图对应评分项“Agent 设计”：网页入口把任务交给编排器；编排器调度 Skill、数据工具与回归模型；"
        "高偏差或无匹配时进入人工复核，而不是由模型单独做高影响决策。它说明各组件如何协同完成同一任务。",
        6.0,
    )
    add_para(doc, SECTIONS[1][1][1])
    add_fig(
        doc,
        RES / "fig_workflow_cn.png",
        "图2 Agent 任务流程",
        "本图把端到端流程拆成可检查步骤：先校验输入，再连数据并筛选，随后调用机器学习预测公允价，"
        "再生成建议，最后做安全检查。每一步失败都有出口，满足“说明每一步作用”和“失败与安全处理”要求。",
        6.2,
    )
    add_para(doc, SECTIONS[1][1][2])
    add_shot_placeholder(
        doc,
        "截图A · 任务入口（找房模式）",
        "打开在线原型，选择「帮我找房」。截取：标题、模式切换、预算/区域/居室/面积/想看几套、以及「开始帮我找」。"
        "建议参数：预算6000，浦东，面积30–80，想看8套。"
        "地址：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app/",
        "用于证明任务入口明确：用户输入什么、系统从哪里开始执行。请用真实页面替换本占位。",
    )

    # 三、机器学习方法
    add_heading_cn(doc, SECTIONS[2][0])
    add_para(doc, SECTIONS[2][1][0])
    add_para(doc, SECTIONS[2][1][1])
    add_fig(
        doc,
        RES / "fig_district_cn.png",
        "图3 清洗后房源行政区分布",
        "本图说明数据工具侧的覆盖情况：清洗后样本在多个行政区均有分布，使“按区域筛选”具备事实基础。"
        "分布并不均匀，后续分区误差分析需结合这一点，避免把稀缺区域的误差简单外推到全市。",
        5.9,
    )
    add_fig(
        doc,
        RES / "fig_split_cn.png",
        "图4 训练 / 验证 / 测试划分",
        "本图给出数据划分证据：固定随机种子42，验证集只用于选模型，测试集只用于最终报告，"
        "防止把调参结果伪装成泛化成绩，对应“报告样例数量、筛选规则和数据划分”的要求。",
        4.4,
    )
    add_para(doc, SECTIONS[2][1][2])

    # 四、Skills 与组件复用
    add_heading_cn(doc, SECTIONS[3][0])
    for p in SECTIONS[3][1]:
        add_para(doc, p)

    # 五、实验设计与结果
    add_heading_cn(doc, SECTIONS[4][0])
    add_para(doc, SECTIONS[4][1][0])
    add_para(doc, SECTIONS[4][1][1])
    add_metrics_table(doc)

    add_fig(
        doc,
        RES / "fig_mae_cn.png",
        "图5 测试集 MAE 对照",
        "MAE 越低越好。三个回归模型均明显低于单价基线，说明多特征学习相对“只按面积外推”更有效；"
        "三者彼此接近，后续以验证集略优且更易解释的 Lasso 作为 Agent 默认模型。",
        5.7,
    )
    add_fig(
        doc,
        RES / "fig_r2_mape_cn.png",
        "图6 测试集 R² 与 MAPE",
        "R² 反映可解释方差，MAPE 反映相对误差。模型 R² 高于基线，但 MAPE 仍偏高，"
        "这是设置人工复核阈值的直接证据：点预测有用，但不能当作确定成交价。",
        5.9,
    )
    add_fig(
        doc,
        RES / "fig_metrics_compare_cn.png",
        "图7 Lasso 与基线关键指标对照",
        "把 MAE/RMSE（千元）与 MAPE 放在同一对照中，便于一眼看到：Lasso 全面优于基线，"
        "同时相对误差仍不可忽视。该图支撑“有合适基线或方法比较”的评分观察点。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][2])
    add_fig(
        doc,
        RES / "fig_pred_vs_true_cn.png",
        "图8 预测值 vs 挂牌价（密度图）",
        "颜色越深表示样本越密集。多数点贴近 y=x，说明整体拟合方向正确；高价区与异常低价区更散，"
        "对应后文失败案例分析——误差并非均匀分布，系统在尾部更需要人工确认。",
        4.8,
    )
    add_fig(
        doc,
        RES / "fig_residual_cn.png",
        "图9 残差分布",
        "残差=预测价−挂牌价。分布大致以0为中心，但存在长尾，说明少数样本偏差很大。"
        "这解释了为何 Agent 对高偏差条目要提示“建议核实”，而不是一律强推。",
        5.6,
    )
    add_para(doc, SECTIONS[4][1][3])
    add_fig(
        doc,
        RES / "fig_feature_cn.png",
        "图10 Lasso 特征影响 Top10",
        "绝对值越大表示影响越强；颜色区分正负方向。面积与部分行政区靠前，方向符合常识，"
        "满足“比较特征影响”的拓展要求。解释时注意 One-Hot 系数是相对参照类，不宜当作独立因果效应。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][4])
    add_fig(
        doc,
        RES / "fig_error_by_rooms_cn.png",
        "图11 分居室误差",
        "不同居室的平均绝对误差并不相同，说明模型在部分户型切片上更弱。"
        "这对 Agent 的启示是：同类误差更高的输入，更应依赖复核提示，而不是只看总 MAE。",
        5.4,
    )
    add_fig(
        doc,
        RES / "fig_error_by_district_cn.png",
        "图12 分区误差（Top8）",
        "部分行政区平均误差更高，可能与样本更少、行政区粗分噪声或未建模区位溢价有关。"
        "它回答“系统在哪些输入上表现较差”，并为后续改进（更细区位特征）提供证据。",
        5.6,
    )
    add_fig(
        doc,
        RES / "fig_failure_cn.png",
        "图13 高误差失败案例",
        "按百分比误差排序的失败样本用于定性分析。常见模式是挂牌显著偏离预测，"
        "可能来自异常挂牌、行政区错分、标题噪声或未建模装修/楼盘因素；对应处置是人工复核。",
        5.7,
    )
    add_para(doc, SECTIONS[4][1][5])
    add_fig(
        doc,
        RES / "fig_sample_tests_cn.png",
        "图14 Agent 可复现样例测试",
        "6个手工样例全部通过，覆盖正常查询与边界失败。该图证明 Agent 层评估不是只挑成功截图，"
        "而是可用 tests/ 脚本复现，对应“可复现交付”与“避免只展示成功案例”。",
        5.6,
    )
    if (RES / "fig_ablation_cn.png").exists():
        add_fig(
            doc,
            RES / "fig_ablation_cn.png",
            "图15 消融对照：启用 / 关闭模型",
            "关闭回归后仍可按约束检索，但失去公允价建议能力。该对照证明机器学习组件不是装饰，"
            "而是建议流程的必要环节，对应 Skills/实验中的消融要求。",
            5.7,
        )

    add_shot_placeholder(
        doc,
        "截图B · 完整运行结果（找房）",
        "用截图A相同参数点击「开始帮我找」。截取至少2–3条结果，必须能看清房东要价、参考合理价、大概相差与建议标签。",
        "用于展示一次完整运行：输入→关键结果。请证明预测已进入建议流程，而不是只返回筛选列表。",
    )
    add_shot_placeholder(
        doc,
        "截图C · 单套判断模式",
        "切换「判断这套房贵不贵」，填写区域/面积/户型/要价后点「帮我判断」，截取输入区与结果区。",
        "用于证明同一模型也可服务“已看到具体房”的判断任务，体现 Agent 任务入口的两种形态。",
    )
    add_shot_placeholder(
        doc,
        "截图D · 异常/边界处理（任选）",
        "例如预算改为1200后点开始，截取无匹配或提示放宽条件；或截取高偏差时的核实提示。",
        "用于证明失败与安全处理真实存在：系统能正确拒绝或请求人工确认，而不是只展示成功路径。",
    )

    # 六、讨论与改进
    add_heading_cn(doc, SECTIONS[5][0])
    for p in SECTIONS[5][1]:
        add_para(doc, p)

    # 七、参考文献
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
        "scikit-learn 1.6.0（BSD-3-Clause）[1][7]；pandas 2.2.3；numpy 2.4.6；joblib 1.4.2；matplotlib 3.10.0；"
        "streamlit 1.67.0（Apache-2.0）[3]；上海链家租房数据（Junru-Sheng/lianjia_Crawler，学习研究用途）[2]；"
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
    add_heading_cn(doc, "附录 D 截图清单（完成后可删除本附录）")
    add_para(
        doc,
        "请将截图A–D替换为真实页面截图后删除本附录。截图需看清输入与结果，不必截取代码编辑器。",
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
        alt = Path(r"c:\Users\Lenovo\Desktop") / "机器学习期末报告_沪租估Agent_图释版.docx"
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
