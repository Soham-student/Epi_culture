"""
Pipeline 04 - Exploratory Data Analysis & Visualisations
==========================================================
Generates:
  1. Continent-level honey production bar chart
  2. Bloom calendar heatmap (plant × month)
  3. Subspecies wing morphometric comparison plot
  4. Bee-plant network connectance scatter
  5. Correlation heatmap of numerical features
  6. Honey quality radar charts per region
  7. Economic impact index per country bar chart
  8. Climate zone vs bee activity matrix
  9. Data completeness report

Outputs:
  - outputs/fig_honey_production_by_continent.png
  - outputs/fig_bloom_calendar_heatmap.png
  - outputs/fig_wing_morphometrics_comparison.png
  - outputs/fig_network_connectance_scatter.png
  - outputs/fig_correlation_heatmap.png
  - outputs/fig_economic_impact_by_country.png
  - outputs/eda_report.txt
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR  = BASE_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CSV = OUT_DIR / "master_honeybee_dataset.csv"


def load_data() -> pd.DataFrame:
    if not MASTER_CSV.exists():
        raise FileNotFoundError(
            f"Master dataset not found: {MASTER_CSV}\n"
            "Please run pipeline_03_integrate.py first."
        )
    df = pd.read_csv(MASTER_CSV)
    print(f"Loaded master dataset: {len(df)} rows × {len(df.columns)} columns")
    return df


# ── Fig 1: Honey Production by Continent ──────────────────────────────────────
def fig_honey_production(df: pd.DataFrame):
    prod = (
        df.groupby(["continent", "country", "iso_country"])["honey_production_tonnes"]
        .first().reset_index()
    )
    prod_cont = prod.groupby("continent")["honey_production_tonnes"].sum().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Honey Production – Apis mellifera Regions", fontsize=14, fontweight="bold")

    # By continent
    colors = sns.color_palette("viridis", len(prod_cont))
    axes[0].bar(prod_cont.index, prod_cont.values / 1000, color=colors)
    axes[0].set_title("By Continent (thousand tonnes)")
    axes[0].set_xlabel("Continent")
    axes[0].set_ylabel("Honey Production (thousand tonnes)")
    axes[0].tick_params(axis="x", rotation=30)

    # By country (top 15)
    prod_country = prod.sort_values("honey_production_tonnes", ascending=False).head(15)
    axes[1].barh(prod_country["country"], prod_country["honey_production_tonnes"] / 1000,
                 color=sns.color_palette("plasma", len(prod_country)))
    axes[1].set_title("Top 15 Countries (thousand tonnes)")
    axes[1].set_xlabel("Honey Production (thousand tonnes)")
    axes[1].invert_yaxis()

    plt.tight_layout()
    path = OUT_DIR / "fig_honey_production_by_continent.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── Fig 2: Bloom Calendar Heatmap ─────────────────────────────────────────────
def fig_bloom_calendar(df: pd.DataFrame):
    plants = df[["plant_common_name", "bloom_months_start", "bloom_months_end"]].dropna().drop_duplicates()
    plants = plants.sort_values("bloom_months_start")

    # Build bloom matrix
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    plant_names = plants["plant_common_name"].unique()[:30]  # cap at 30
    matrix = np.zeros((len(plant_names), 12))

    for i, pname in enumerate(plant_names):
        row = plants[plants["plant_common_name"] == pname].iloc[0]
        start = int(row["bloom_months_start"]) - 1
        end   = int(row["bloom_months_end"])
        matrix[i, start:end] = 1

    fig, ax = plt.subplots(figsize=(14, max(6, len(plant_names) * 0.35)))
    im = ax.imshow(matrix, cmap="YlOrBr", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(12))
    ax.set_xticklabels(month_labels, fontsize=9)
    ax.set_yticks(range(len(plant_names)))
    ax.set_yticklabels(plant_names, fontsize=8)
    ax.set_title("Bloom Calendar – Honey Bee Forage Plants (Apis mellifera)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Month")
    plt.colorbar(im, ax=ax, label="Flowering (1=Yes)", fraction=0.02)
    plt.tight_layout()
    path = OUT_DIR / "fig_bloom_calendar_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── Fig 3: Subspecies Wing Morphometrics ──────────────────────────────────────
def fig_wing_morphometrics(df: pd.DataFrame):
    morph = (
        df[["known_subspecies", "subspecies_lineage", "forewing_length_mm_mean",
            "forewing_width_mm_mean", "cubital_index_mean", "tongue_length_mm_mean",
            "body_weight_mg_mean"]]
        .dropna(subset=["forewing_length_mm_mean"])
        .drop_duplicates(subset=["known_subspecies"])
    )
    # Use first mentioned subspecies name
    morph["short_name"] = morph["known_subspecies"].apply(lambda x: x.split("(")[0].split("/")[0].strip()[:35])
    morph = morph.sort_values("forewing_length_mm_mean")

    lineage_colors = {"M": "#2196F3", "C": "#4CAF50", "A": "#FF5722", "O": "#9C27B0", "Y": "#FF9800", "Unknown": "#9E9E9E"}
    colors = morph["subspecies_lineage"].map(lineage_colors).fillna("#9E9E9E")

    fig, axes = plt.subplots(1, 3, figsize=(18, max(5, len(morph) * 0.4)))
    fig.suptitle("Apis mellifera Subspecies Wing Morphometrics\n(Tofilski 2008 / Machlowska et al. 2025)",
                 fontsize=13, fontweight="bold")

    for ax, col, label in zip(
        axes,
        ["forewing_length_mm_mean", "cubital_index_mean", "tongue_length_mm_mean"],
        ["Forewing Length (mm)", "Cubital Index", "Tongue Length (mm)"]
    ):
        ax.barh(morph["short_name"], morph[col], color=colors)
        ax.set_xlabel(label)
        ax.set_title(label)
        ax.invert_yaxis()

    # Legend
    legend_patches = [plt.matplotlib.patches.Patch(color=v, label=f"Lineage {k}")
                      for k, v in lineage_colors.items() if k != "Unknown"]
    fig.legend(handles=legend_patches, loc="lower center", ncol=5, fontsize=8, frameon=True)

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    path = OUT_DIR / "fig_wing_morphometrics_comparison.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── Fig 4: Network Connectance Scatter ────────────────────────────────────────
def fig_network_connectance(df: pd.DataFrame):
    scatter = df[["plant_common_name", "plant_type", "network_connectance",
                  "nectar_sugar_conc_pct", "pollen_protein_pct",
                  "honey_hei_score", "economic_impact_index"]].dropna(
        subset=["network_connectance", "nectar_sugar_conc_pct"]
    ).drop_duplicates(subset=["plant_common_name"])

    fig, ax = plt.subplots(figsize=(12, 7))
    plant_types = scatter["plant_type"].unique()
    palette = sns.color_palette("tab10", len(plant_types))
    type_color = dict(zip(plant_types, palette))

    for _, row in scatter.iterrows():
        ax.scatter(row["nectar_sugar_conc_pct"], row["network_connectance"],
                   s=max(20, row["honey_hei_score"] * 1.5) if pd.notna(row["honey_hei_score"]) else 40,
                   color=type_color.get(row["plant_type"], "gray"),
                   alpha=0.75, edgecolors="white", linewidth=0.5)
        ax.annotate(row["plant_common_name"], (row["nectar_sugar_conc_pct"], row["network_connectance"]),
                    fontsize=7, alpha=0.8, xytext=(3, 3), textcoords="offset points")

    legend_patches = [plt.matplotlib.patches.Patch(color=v, label=k) for k, v in type_color.items()]
    ax.legend(handles=legend_patches, title="Plant Type", fontsize=8, loc="lower right")
    ax.set_xlabel("Nectar Sugar Concentration (%)", fontsize=11)
    ax.set_ylabel("Bee-Plant Network Connectance (0–1)", fontsize=11)
    ax.set_title("Plant Foraging Attractiveness for Apis mellifera\n(bubble size = Honey Economic Health Index)",
                 fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)

    path = OUT_DIR / "fig_network_connectance_scatter.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── Fig 5: Correlation Heatmap ────────────────────────────────────────────────
def fig_correlation_heatmap(df: pd.DataFrame):
    num_cols = [
        "nectar_sugar_conc_pct", "pollen_protein_pct", "honey_hei_score",
        "honey_glucose_pct", "honey_fructose_pct", "honey_water_pct",
        "honey_color_mmpfund", "network_connectance", "forewing_length_mm_mean",
        "cubital_index_mean", "tongue_length_mm_mean",
        "annual_temp_c", "annual_precip_mm", "bee_active_months",
        "crop_value_usd_per_ton", "economic_impact_index",
        "honey_production_tonnes", "honey_yield_kg_per_hive",
    ]
    corr_df = df[[c for c in num_cols if c in df.columns]].dropna(how="all")
    corr = corr_df.corr()

    fig, ax = plt.subplots(figsize=(14, 12))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
                center=0, vmin=-1, vmax=1, ax=ax, annot_kws={"size": 7},
                linewidths=0.5)
    ax.set_title("Feature Correlation Matrix – Honeybee Dataset", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = OUT_DIR / "fig_correlation_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── Fig 6: Economic Impact by Country ─────────────────────────────────────────
def fig_economic_impact(df: pd.DataFrame):
    eco = (
        df.groupby("country")["economic_impact_index"]
        .sum().sort_values(ascending=False).reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    palette = sns.color_palette("coolwarm_r", len(eco))
    ax.bar(eco["country"], eco["economic_impact_index"], color=palette)
    ax.set_xlabel("Country")
    ax.set_ylabel("Cumulative Economic Impact Index")
    ax.set_title("Pollinator Economic Impact Index by Country\n(Apis mellifera × Forage Plants)",
                 fontsize=12, fontweight="bold")
    ax.tick_params(axis="x", rotation=55)
    plt.tight_layout()
    path = OUT_DIR / "fig_economic_impact_by_country.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved -> {path.name}")


# ── EDA Report ────────────────────────────────────────────────────────────────
def generate_eda_report(df: pd.DataFrame):
    lines = []
    lines.append("=" * 65)
    lines.append(" HONEYBEE DATASET – EDA REPORT")
    lines.append(" Species: Apis mellifera (Western Honey Bee)")
    lines.append("=" * 65)
    lines.append(f"\nShape : {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append(f"Continents covered  : {sorted(df['continent'].unique())}")
    lines.append(f"Countries covered   : {df['country'].nunique()}")
    lines.append(f"Unique plants       : {df['plant_scientific_name'].nunique()}")
    lines.append(f"Plant families      : {df['family'].dropna().nunique()}")
    lines.append(f"Subspecies recorded : {df['known_subspecies'].nunique()}")
    lines.append(f"Lineages (M/C/A/O/Y): {sorted(df['subspecies_lineage'].dropna().unique())}")
    lines.append(f"Avg data completeness: {df['data_completeness_score'].mean():.1%}")

    lines.append("\n── Honey Production Top 5 ─────────────────────────────")
    top_prod = (df.groupby("country")["honey_production_tonnes"].first()
                  .sort_values(ascending=False).head(5))
    for c, v in top_prod.items():
        lines.append(f"  {c:<20}: {v:>8,} tonnes")

    lines.append("\n── Plants by Type ─────────────────────────────────────")
    for ptype, cnt in df["plant_type"].value_counts().items():
        lines.append(f"  {ptype:<30}: {cnt}")

    lines.append("\n── Honey Types ────────────────────────────────────────")
    for htype, cnt in df["honey_type"].value_counts().items():
        lines.append(f"  {htype:<35}: {cnt}")

    lines.append("\n── Tofilski 2025 Dataset Coverage ─────────────────────")
    tofilski_countries = df[df["in_tofilski_2025_dataset"]==True]["country"].unique()
    lines.append(f"  Countries: {', '.join(sorted(tofilski_countries))}")
    lines.append(f"  Wing images in dataset: 17,457")
    lines.append(f"  Colonies sampled: 1,557")
    lines.append(f"  DOI: 10.1038/s41597-025-06234-8")
    lines.append(f"  Zenodo: 10.5281/zenodo.17075125")

    lines.append("\n── Wing Morphometrics Range ───────────────────────────")
    lines.append(f"  Forewing length: {df['forewing_length_mm_mean'].min():.2f}–{df['forewing_length_mm_mean'].max():.2f} mm")
    lines.append(f"  Cubital index  : {df['cubital_index_mean'].min():.2f}–{df['cubital_index_mean'].max():.2f}")
    lines.append(f"  Tongue length  : {df['tongue_length_mm_mean'].min():.2f}–{df['tongue_length_mm_mean'].max():.2f} mm")

    lines.append("\n── Toxic Honey Risk Plants ────────────────────────────")
    toxic = df[df["toxic_honey_risk"]==True][["plant_common_name","plant_scientific_name","country"]].drop_duplicates()
    for _, r in toxic.iterrows():
        lines.append(f"  {r['plant_common_name']:<25} ({r['plant_scientific_name']}) – {r['country']}")

    lines.append("\n── Key Reference Papers ───────────────────────────────")
    lines.append("  [1] Machlowska J, Kandemir I, Tofilski A et al. (2025)")
    lines.append("      Variation of honey bee wings in southwestern Asia.")
    lines.append("      Scientific Data. DOI:10.1038/s41597-025-06234-8")
    lines.append("  [2] Oleksa A, Cauia E, Tofilski A et al. (2023)")
    lines.append("      Honey bee wing images: a tool for identification and conservation.")
    lines.append("      GigaScience. DOI:10.1093/gigascience/giad019")
    lines.append("  [3] Tofilski A. (2008)")
    lines.append("      Using geometric morphometrics and standard morphometry to discriminate")
    lines.append("      three honeybee subspecies. Apidologie 39:558–563.")
    lines.append("      DOI:10.1051/apido:2008028")

    lines.append("\n" + "=" * 65)

    report = "\n".join(lines)
    path = OUT_DIR / "eda_report.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  EDA report saved -> {path.name}")
    print(report)
    return report


def main():
    print("=" * 60)
    print("  Honeybee Dataset - Pipeline 04: EDA & Visualisations")
    print("=" * 60)

    df = load_data()

    print("\nGenerating figures...")
    fig_honey_production(df)
    fig_bloom_calendar(df)
    fig_wing_morphometrics(df)
    fig_network_connectance(df)
    fig_correlation_heatmap(df)
    fig_economic_impact(df)

    print("\nGenerating EDA report...")
    generate_eda_report(df)

    print("\nPipeline 04 complete.")


if __name__ == "__main__":
    main()
