"""
优惠券AB测试统计功效模拟
========================
场景：定价策略师测试"满30减5"vs"满25减3"哪个GMV更高
已知：历史GMV均值=100元，标准差=30元
问题：每组需要多少样本才能检测到X元的GMV差异？

使用方法：
    python ab_test_power_simulation.py
"""

import numpy as np
import scipy.stats as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================
# 中文字体（Windows: Microsoft YaHei）
# ============================================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)

# ============================================
# Part 1: 统计功效模拟
# ============================================

def simulate_ab_test(n_per_group, true_effect, std, alpha=0.05):
    """模拟一次AB测试，返回是否检出显著差异"""
    group_a = np.random.normal(100, std, n_per_group)
    group_b = np.random.normal(100 + true_effect, std, n_per_group)
    t_stat, p_value = st.ttest_ind(group_b, group_a)
    return p_value < alpha


def calc_statistical_power(n_per_group, true_effect, std, n_simulations=1000):
    """重复模拟 n_simulations 次，计算统计功效"""
    significant_count = sum(
        simulate_ab_test(n_per_group, true_effect, std)
        for _ in range(n_simulations)
    )
    return significant_count / n_simulations


# ============================================
# Part 2: MDE 与样本量计算
# ============================================
from scipy.stats import norm


def calc_mde(std, n_per_group, alpha=0.05, power=0.8):
    """计算最小可检测效应（MDE）"""
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    return (z_alpha + z_power) * std * np.sqrt(2 / n_per_group)


def calc_sample_size(std, mde, alpha=0.05, power=0.8):
    """反算所需样本量"""
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    return int(np.ceil(2 * ((z_alpha + z_beta) * std / mde) ** 2))


# ============================================
# 主程序
# ============================================
if __name__ == '__main__':
    effect = 5
    std_dev = 30
    sample_sizes = [50, 100, 200, 500, 1000, 2000]

    # --- Part 1 ---
    powers = [calc_statistical_power(n, effect, std_dev) for n in sample_sizes]

    print("=" * 50)
    print("Part 1: 固定效应量 5 元, 标准差 30 元")
    print("=" * 50)
    for n, p in zip(sample_sizes, powers):
        status = "[OK]" if p >= 0.8 else "[XX]"
        print(f"  每组 {n:>5} 人 -> 功效 = {p:.1%}  {status}")

    n_fixed = 500
    effects_list = [1, 2, 3, 5, 8, 10]
    powers2 = [calc_statistical_power(n_fixed, e, std_dev) for e in effects_list]

    print("\n固定 500 人, 不同效应量:")
    for e, p in zip(effects_list, powers2):
        status = "[OK]" if p >= 0.8 else "[XX]"
        print(f"  效应量 {e:>2} 元 -> 功效 = {p:.1%}  {status}")

    # --- Part 2 ---
    print("\n" + "=" * 50)
    print("Part 2: MDE 与样本量")
    print("=" * 50)

    print("\n不同人数下的 MDE:")
    for n in [100, 200, 500, 1000, 2000, 5000]:
        mde = calc_mde(std_dev, n)
        print(f"  每组 {n:>5} 人 -> MDE = {mde:.1f} 元")

    print("\n检测不同效果所需的每组人数:")
    for target in [10, 8, 5, 3, 2, 1]:
        needed = calc_sample_size(std_dev, target)
        print(f"  检测 {target} 元差异 -> 每组 {needed:>6} 人")

    # --- 图表 ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(sample_sizes, powers, 'o-', linewidth=2, markersize=8)
    axes[0].axhline(0.8, color='red', linestyle='--', label='80%功效（行业标准）')
    axes[0].set_xlabel('每组样本量')
    axes[0].set_ylabel('统计功效')
    axes[0].set_title('样本量 vs 统计功效（效应量固定=5元）')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(effects_list, powers2, 'o-', linewidth=2, markersize=8, color='orange')
    axes[1].axhline(0.8, color='red', linestyle='--', label='80%功效（行业标准）')
    axes[1].set_xlabel('效应量（元）')
    axes[1].set_ylabel('统计功效')
    axes[1].set_title('效应量 vs 统计功效（每组固定500样本）')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('ab_test_power.png', dpi=150)
    print("\n图表已保存至 ab_test_power.png")
