import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def oszlopdiagram(party_support, party_colors, dataset_labels, max, title, output_dir):
    parties = list(party_support.keys())
    num_datasets = len(dataset_labels)
    bar_width = 0.2
    group_spacing = 0.4 
    intra_spacing = 0.05 

    x_positions = []
    x_labels = []
    current_x = 0

    for party in parties:
        group_start_x = current_x
        for i in range(num_datasets):
            x_positions.append(current_x)
            current_x += bar_width + intra_spacing
        group_end_x = current_x - intra_spacing
        group_center = (group_start_x + group_end_x - bar_width) / 2
        x_labels.append(group_center)
        current_x += group_spacing

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#F4F4F4')
    ax.grid(axis='y', color='white', linestyle='-', linewidth=2, alpha=1, zorder=0)

    bar_index = 0
    for party in parties:
        color = party_colors[party]
        for i in range(num_datasets):
            value = party_support[party][i]
            x = x_positions[bar_index]
            bar = ax.bar(x, value, width=bar_width, color=color, zorder=3)
            ax.text(x, value + 1, f'{value:.1f}%', ha='center', va='bottom',
                    fontsize=9, fontweight='bold', color=color)
            bar_index += 1

    ax.set_xticks(x_labels)
    ax.set_xticklabels(parties, fontsize=10, fontweight='bold')
    ax.set_ylabel('Támogatottság (%)')
    ax.set_ylim(0, max)
    ax.set_yticks(range(0, max+1, 5))
    ax.set_title(title, fontsize=14)

    legend_text = '\n'.join([f'{i + 1}. oszlop: {label}' for i, label in enumerate(dataset_labels)])
    plt.figtext(0.5, -0.1, legend_text, wrap=True, horizontalalignment='center', fontsize=10)

    plt.tight_layout()

    today_str = datetime.today().strftime('%Y-%m-%d')
    os.makedirs(output_dir, exist_ok=True)
    filename_base = f'{today_str}_partpref'
    plt.savefig(os.path.join(output_dir, f'{filename_base}.png'), format='png', dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, f'{filename_base}.svg'), format='svg', bbox_inches='tight')
    plt.close()

oszlopdiagram(
    party_support= {
        'Fidesz-KDNP': [36.29, 24,28],
        'TISZA': [29.22, 50],
        'MKKP': [7.81, 15.7],
        'DK': [9.85, 4.28],
        'Mi Hazánk': [3.89, 4.28],
        'Momentum': [9.79, 1.42]
    },
    party_colors = {
        'Fidesz-KDNP': '#FF6A00',
        'TISZA': '#112866',
        'MKKP': '#808080',
        'DK': '#0067AA',
        'Mi Hazánk': '#688D1B',
        'Momentum': '#9900CC'
    },
    dataset_labels = ['2024 június - EP eredmények', '2025 augusztus - 21 Kutatóintézet'],
    max=60,
    title='2025. augusztus - 21 Kutatóintézet mérése Józsefvárosban',
    output_dir="diagramok"
)