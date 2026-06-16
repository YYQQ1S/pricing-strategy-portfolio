# -*- coding: utf-8 -*-
"""
多本品市占率堆积柱形图 — 浅色系竞品版（最终优化版）
========================================================
特性不变：
  - 【其他】车型不参与本品排名
  - 每个柱子显示所有车型的百分比标签，仅 TOP3 车型显示名称
  - 仅本品标签加粗
  - 竞品颜色为浅色系，按关键字映射色系（问界→灰，理想→绿，极氪→暖）
  - 全国合计固定最左，无特殊样式
  - 全局字体集中控制
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ============================================================
# 配置区
# ============================================================

ANALYSES = [
    dict(
        product='高山',
        data_file='数据.xlsx',
        sheet_name=0,
        output_file='p_final.png',
        title='',
    ),
]

PRODUCT_COLOR = '#E63946'                     # 本品鲜明红色

# 竞品浅色系调色板（20色，按灰/绿/蓝/暖分组）
COMPETITOR_PALETTE = [
    '#9BA6A2', '#A79D9C', '#B6B9BE', '#BFBFB7', '#C8C4C1',  # 灰色系 0-4
    '#BECFAF', '#CFDABA', '#DDE1AF', '#E3E1BA', '#E6E3D0',  # 绿色系 5-9
    '#AFCCDE', '#BDCEE2', '#CBE4FF', '#C8D9FF', '#CCE6F7',  # 蓝色系 10-14
    '#FCD4CA', '#E4CDBD', '#F5E4B9', '#F8E7D3', '#D4C2B6',  # 暖色系 15-19
]

# 品牌关键词 -> 色系索引范围
COLOR_MAPPING = {
    '问界': (0, 4),    # 灰色系
    '理想': (5, 9),    # 绿色系
    '极氪': (15, 19),  # 暖色系
}

# 字体大小（集中可调）
LABEL_MIN_FONTSIZE = 5          # 极小份额最小字号
LABEL_NORMAL_FONTSIZE = 8       # 正常份额字号
LABEL_MIN_HEIGHT_RATIO = 0      # 标签外置阈值（0表示始终居中）
AXIS_TITLE_FONTSIZE = 13
AXIS_XTICK_FONTSIZE = 9
AXIS_RANK_LABEL_FONTSIZE = 8
LEGEND_FONTSIZE = 8

# 图面尺寸
FIGURE_DPI = 180
FIG_WIDTH = 12
FIG_HEIGHT = 8
BAR_WIDTH_RATIO = 0.6

# 图例自适应
LEGEND_INLINE_LIMIT = 6
LEGEND_BOTTOM_NCOL = 15

# 字体
FONT_CANDIDATES = ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']

plt.rcParams['axes.unicode_minus'] = False


def setup_chinese_font():
    available = {f.name for f in fm.fontManager.ttflist}
    for fc in FONT_CANDIDATES:
        if fc in available:
            plt.rcParams['font.sans-serif'] = [fc, 'DejaVu Sans']
            print(f'[字体] 使用: {fc}')
            return
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    print('[字体] 未找到中文字体')


def build_colors(models, product):
    """为车型分配颜色（本品固定红色，竞品按关键词映射或顺序轮转）"""
    cmap = {}
    used = set()
    cat_counters = {}
    generic_idx = 0
    family_starts = [0, 5, 10, 15]   # 四个色系起始索引

    for m in models:
        if m == product:
            cmap[m] = PRODUCT_COLOR
            continue

        # 匹配品牌关键词
        matched = None
        for kw, (start, end) in COLOR_MAPPING.items():
            if kw in m:
                matched = (start, end)
                break

        if matched:
            start, end = matched
            pool = COMPETITOR_PALETTE[start:end+1]
            idx = cat_counters.get((start, end), 0)
            for _ in range(len(pool)):
                c = pool[idx % len(pool)]
                if c not in used:
                    break
                idx += 1
            cat_counters[(start, end)] = idx + 1
            cmap[m] = c
            used.add(c)
        else:
            # 无匹配：跨色系轮转
            chosen = None
            for _ in range(len(family_starts) * 5):
                fam_idx = generic_idx % len(family_starts)
                start = family_starts[fam_idx]
                for offset in range(5):
                    c_idx = start + offset
                    if c_idx < len(COMPETITOR_PALETTE):
                        c = COMPETITOR_PALETTE[c_idx]
                        if c not in used:
                            chosen = c
                            break
                if chosen:
                    break
                generic_idx += 1
            if chosen is None:
                chosen = COMPETITOR_PALETTE[0]
            cmap[m] = chosen
            used.add(chosen)
            generic_idx += 1

    return cmap


def compute_rank(shares_dict, product, exclude='其他'):
    """计算本品排名，排除指定车型"""
    filtered = {k: v for k, v in shares_dict.items() if k != exclude}
    return sum(1 for v in filtered.values() if v > filtered.get(product, 0)) + 1


def place_label(ax, x, y, height, text, fontsize, fontweight, color):
    """始终在柱段居中放置标签（阈值0强制居中）"""
    ax.text(x, y + height / 2, text, ha='center', va='center',
            fontsize=fontsize, fontweight=fontweight, color=color)


def split_model_name(model):
    """
    智能分行：
      - 纯中文：每2个字符一行（如"理想汽车" → "理想\n汽车"）
      - 中英文混合：中文一行，非中文一行（如"理想L8" → "理想\nL8"）
      - 纯英文/数字：原样一行
    """
    # 情况1：纯中文字符串 → 按每2个字符分行
    if all('\u4e00' <= c <= '\u9fff' for c in model):
        return '\n'.join([model[i:i+2] for i in range(0, len(model), 2)])

    # 情况2：包含中文（且非纯中文）→ 中文与其它字符分行
    chinese_part = ''
    non_chinese_part = ''
    for ch in model:
        if '\u4e00' <= ch <= '\u9fff':
            chinese_part += ch
        else:
            non_chinese_part += ch
    if chinese_part and non_chinese_part:
        return f'{chinese_part}\n{non_chinese_part}'

    # 情况3：纯非中文（英文/数字/符号）→ 原样一行
    return model


def draw_single_chart(df, product, output_file, title):
    # ---- 分离全国合计 ----
    national_patterns = '全国合计|全国总计|总计|合计|全国'
    mask = df['省份'].str.contains(national_patterns, na=False)
    if mask.any():
        national_row = df[mask].iloc[[0]]
        province_rows = df[~mask].copy()
    else:
        print('[提示] 未识别到全国合计行，将第一行作为全国合计')
        national_row = df.iloc[[0]]
        province_rows = df.iloc[1:].copy()

    # 车型列表
    models = [c for c in df.columns if c != '省份' and df[c].notna().any()]
    if product not in models:
        raise ValueError(f'本品 "{product}" 不在列 {models} 中。')

    # 省份按本品市占率排序
    province_rows[product] = pd.to_numeric(province_rows[product], errors='coerce').fillna(0)
    province_rows = province_rows.sort_values(product, ascending=True)

    # 构建堆叠数据：全国合计 + 排序后省份
    regions, stacks = [], []
    if not national_row.empty:
        nat = national_row.iloc[0]
        pairs = [(m, nat[m]) for m in models if pd.notna(nat[m])]
        regions.append('全国合计')
        stacks.append(sorted(pairs, key=lambda x: x[1]))

    for _, row in province_rows.iterrows():
        prov = row['省份']
        pairs = [(m, row[m]) for m in models if pd.notna(row[m])]
        regions.append(prov)
        stacks.append(sorted(pairs, key=lambda x: x[1]))

    # 计算排名（排除“其他”）
    ranks = {reg: compute_rank(dict(stack), product) for reg, stack in zip(regions, stacks)}

    # 颜色映射
    colors = build_colors(models, product)

    # ---- 绘图 ----
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.patch.set_facecolor('#FCFCFC')
    ax.set_facecolor('#FCFCFC')

    x = np.arange(len(regions))
    bar_width = BAR_WIDTH_RATIO
    legend_added = set()

    for i, (reg, stack) in enumerate(zip(regions, stacks)):
        bottom = 0
        top3 = {model for model, _ in sorted(stack, key=lambda x: x[1], reverse=True)[:3]}

        for model, share in stack:
            label = model if model not in legend_added else None
            is_product = (model == product)

            ax.bar(i, share, bar_width, bottom=bottom,
                   color=colors[model], edgecolor='white', linewidth=0.8,
                   label=label, zorder=3)
            legend_added.add(model)

            # 标签文本
            pct = f'{share:.0%}'
            if model in top3:
                text = f'{split_model_name(model)}\n{pct}'
            else:
                text = pct

            # 字号
            if is_product:
                fs = LABEL_NORMAL_FONTSIZE + 0.3
            else:
                fs = max(LABEL_MIN_FONTSIZE,
                         int(LABEL_NORMAL_FONTSIZE * (1 + share * 15)))
                fs = min(fs, LABEL_NORMAL_FONTSIZE)

            fw = 'bold' if is_product else 'normal'
            color_txt = 'white' if is_product else 'black'
            place_label(ax, i, bottom, share, text, fs, fw, color_txt)

            bottom += share

    # ---- X轴 ----
    combined = [f'{reg}\n{ranks[reg]}' for reg in regions]
    ax.set_xticks(x)
    ax.set_xticklabels(combined, fontsize=AXIS_XTICK_FONTSIZE, linespacing=1.8)
    ax.text(0.01, -0.065, f'{len(models)}个车型中\n{product}排名',
            transform=ax.transAxes, ha='center', va='center',
            fontsize=AXIS_RANK_LABEL_FONTSIZE, fontweight='normal', color='black')

    # ---- Y轴隐藏 ----
    total_max = max(sum(s for _, s in stack) for stack in stacks)
    ax.set_ylim(0, max(total_max * 1.18, 0.18))
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', left=False, labelleft=False)

    ax.set_title(title, fontsize=AXIS_TITLE_FONTSIZE, fontweight='bold', pad=15, color='black')

    # ---- 图例 ----
    handles, labels = ax.get_legend_handles_labels()
    unique = dict.fromkeys(zip(handles, labels))
    handles, labels = zip(*unique.keys()) if unique else ([], [])
    n_models = len(models)
    if n_models <= LEGEND_INLINE_LIMIT:
        legend = ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1.01, 1),
                           frameon=True, fontsize=LEGEND_FONTSIZE,
                           edgecolor='#DDD', fancybox=True)
        legend_placement = 'right'
    else:
        legend = ax.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.9),
                           frameon=True, fontsize=LEGEND_FONTSIZE,
                           edgecolor='#DDD', fancybox=True, ncol=LEGEND_BOTTOM_NCOL)
        legend_placement = 'top'

    for text in legend.get_texts():
        if text.get_text() == product:
            text.set_fontweight('bold')
            text.set_color(PRODUCT_COLOR)
        else:
            text.set_color('black')

    # ---- 其他样式 ----
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CFD8DC')
    # 左脊柱已隐藏，无需设置颜色
    ax.tick_params(axis='x', length=0, colors='black')

    # ---- 保存 ----
    if legend_placement == 'top':
        rect = [0, 0.10, 1, 0.88]
    elif legend_placement == 'bottom':
        rect = [0, 0.18, 1, 1]
    else:
        rect = [0, 0.10, 0.95, 1]
    plt.tight_layout(rect=rect)
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    plt.savefig(output_file, dpi=FIGURE_DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f'  [OK] 图表已保存 -> {output_file}')
    plt.close(fig)


def main():
    setup_chinese_font()
    print('=' * 55)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for cfg in ANALYSES:
        product = cfg['product']
        data_file = cfg['data_file']
        sheet = cfg.get('sheet_name', 0)
        output = cfg['output_file']
        title = cfg.get('title', f'各省份车型市占率分布 — 本品：{product}')

        data_file = os.path.join(base_dir, data_file) if not os.path.isabs(data_file) else data_file
        output = os.path.join(base_dir, output) if not os.path.isabs(output) else output

        print(f'\n--- 正在处理本品: {product} ---')
        print(f'  数据文件: {data_file}')

        df = pd.read_excel(data_file, sheet_name=sheet)
        if '省份' not in df.columns:
            print(f'  [WARN] 缺少"省份"列，跳过。列名: {list(df.columns)}')
            continue
        if product not in df.columns:
            print(f'  [WARN] 本品 "{product}" 不在数据列中，跳过。可用: {list(df.columns)}')
            continue

        print(f'  数据: {len(df)} 行 × {len(df.columns)} 列')
        draw_single_chart(df, product, output, title)

    print(f'\n{"=" * 55}')
    print(f'全部完成，共生成 {len(ANALYSES)} 张图表。')


if __name__ == '__main__':
    main()