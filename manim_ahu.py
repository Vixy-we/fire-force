"""
manim_ahu.py

Manim Community scene: animated AHU psychrometric journey.
Reads stage data from MANIM_STAGE_DATA environment variable (JSON path).
Does NOT require LaTeX — all text uses Pango-based Text objects.

Usage:
    python -m manim manim_ahu.py AHUJourneyScene -ql --media_dir media
"""

import json
import os
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Arrow, Text, VGroup, Group, VMobject,
    Create, FadeIn, FadeOut, GrowFromCenter, Write, LaggedStart,
    UP, DOWN, RIGHT, LEFT, ORIGIN,
    config as manim_config,
    NumberLine,
)


# ─── Coordinate helpers ─────────────────────────────────────────────────────
X_MIN, X_MAX = 0, 50
Y_MIN, Y_MAX = 0.0, 0.030
X_LEN, Y_LEN = 12, 7
X_SHIFT = -0.5  # horizontal chart center offset


def psat(t):
    """Saturation vapour pressure (Pa) — Magnus formula."""
    return 610.78 * np.exp(17.27 * t / (t + 237.3))


def humidity_ratio(t, rh_dec):
    """W = 0.622 * (RH * Psat) / (101325 - RH * Psat)"""
    ps = psat(t)
    pw = rh_dec * ps
    denom = 101325.0 - pw
    if denom <= 0:
        return Y_MAX
    return min(0.622 * pw / denom, 0.035)


# ─── Stage metadata ─────────────────────────────────────────────────────────
STAGE_META = {
    "outdoor":      {"label": "Outdoor Air",    "color": "#FF6B35"},
    "mixing":       {"label": "Mixed Air",      "color": "#FFD700"},
    "cooling_coil": {"label": "Cooling Coil",   "color": "#7B2FFF"},
    "fan":          {"label": "Supply Fan",      "color": "#00C9FF"},
    "supply":       {"label": "Supply Air",      "color": "#00E676"},
}
STAGE_ORDER = ["outdoor", "mixing", "cooling_coil", "fan", "supply"]


class AHUJourneyScene(Scene):
    """
    Animated psychrometric chart showing the air state transformation
    through each stage of an Air Handling Unit.
    No LaTeX required — uses only Text and manual axis labels.
    """

    def construct(self):
        # ── Background ──────────────────────────────────────────────────
        self.camera.background_color = "#0F1117"

        # ── Load stage data ─────────────────────────────────────────────
        json_path = os.environ.get("MANIM_STAGE_DATA", "media/manim_input.json")
        with open(json_path, "r") as f:
            data = json.load(f)

        stage_data = data["stages"]
        energy_data = data.get("energy", {})

        # ════════════════════════════════════════════════════════════════
        # PHASE 1 — Chart Construction (~3s)
        # ════════════════════════════════════════════════════════════════

        # Axes — NO include_numbers to avoid LaTeX dependency
        axes = Axes(
            x_range=[X_MIN, X_MAX, 10],
            y_range=[Y_MIN, Y_MAX, 0.005],
            x_length=X_LEN,
            y_length=Y_LEN,
            axis_config={
                "color": "#2A3140",
                "include_numbers": False,
                "include_ticks": True,
                "tick_size": 0.05,
            },
            tips=False,
        ).shift(LEFT * 0.5)

        # Manual X-axis tick labels (Text, no LaTeX)
        x_labels = VGroup()
        for val in range(0, 51, 10):
            label = Text(str(val), font_size=16, color="#8B95A5")
            label.move_to(axes.c2p(val, 0) + DOWN * 0.35)
            x_labels.add(label)

        # Manual Y-axis tick labels
        y_labels = VGroup()
        for val_i in range(0, 31, 5):
            val = val_i / 1000.0  # 0.000, 0.005, ..., 0.030
            label = Text(f"{val:.3f}", font_size=14, color="#8B95A5")
            label.move_to(axes.c2p(0, val) + LEFT * 0.7)
            y_labels.add(label)

        # Axis title labels
        x_title = Text(
            "Dry Bulb Temperature (deg C)",
            font_size=16, color="#8B95A5",
        ).next_to(axes.x_axis, DOWN, buff=0.7)

        y_title = Text(
            "Humidity Ratio W (kg/kg)",
            font_size=16, color="#8B95A5",
        ).rotate(np.pi / 2).next_to(axes.y_axis, LEFT, buff=1.0)

        self.play(Create(axes), run_time=1.0)
        self.play(
            FadeIn(x_labels), FadeIn(y_labels),
            FadeIn(x_title), FadeIn(y_title),
            run_time=0.5,
        )

        # ── RH Curves ──────────────────────────────────────────────────
        rh_values = [0.20, 0.40, 0.60, 0.80, 1.0]
        rh_curves = []
        rh_text_labels = []

        temps = np.arange(0, 50.5, 0.5)

        for rh in rh_values:
            points = []
            for t in temps:
                w = humidity_ratio(t, rh)
                if w <= Y_MAX:
                    pt = axes.c2p(t, w)
                    points.append(pt)

            if len(points) < 2:
                continue

            curve = VMobject()
            curve.set_points_smoothly([np.array(p) for p in points])

            if rh == 1.0:
                curve.set_stroke(color="#00C9FF", width=2.5)
            else:
                curve.set_stroke(color="#2A3140", width=1.2)

            rh_curves.append(curve)

            # RH label at tail of curve
            label_t = 46.0
            label_w = humidity_ratio(label_t, rh)
            if label_w <= 0.029:
                pct_text = f"{int(rh * 100)}%"
                rh_label = Text(
                    pct_text, font_size=14, color="#8B95A5",
                ).move_to(axes.c2p(label_t, label_w) + UP * 0.2 + RIGHT * 0.3)
                rh_text_labels.append(rh_label)

        # Animate curves sequentially
        self.play(
            LaggedStart(
                *[Create(c) for c in rh_curves],
                lag_ratio=0.15,
            ),
            run_time=2.0,
        )

        if rh_text_labels:
            self.play(*[FadeIn(lb) for lb in rh_text_labels], run_time=0.5)

        # Subtle fill under saturation curve
        if rh_curves:
            sat_curve = rh_curves[-1]
            fill_copy = sat_curve.copy()
            fill_copy.set_fill(color="#00C9FF", opacity=0.03)
            fill_copy.set_stroke(width=0)
            self.add(fill_copy)

        self.wait(0.3)

        # ════════════════════════════════════════════════════════════════
        # PHASE 2 — Stage Points (~5s)
        # ════════════════════════════════════════════════════════════════

        dots = []
        all_labels = VGroup()

        for idx, sid in enumerate(STAGE_ORDER):
            if sid not in stage_data:
                continue

            sd = stage_data[sid]
            meta = STAGE_META[sid]
            number = idx + 1

            # Position using axes coordinate system
            pos = axes.c2p(sd["DBT"], sd["W"])

            dot = Dot(
                point=pos,
                radius=0.12,
                color=meta["color"],
            )
            dot.set_z_index(10)

            # Stage label
            label = Text(
                f"{number}. {meta['label']}  {sd['DBT']:.1f} C",
                font_size=14, color="#E8EAF0",
            ).next_to(dot, UP + RIGHT, buff=0.15)
            label.set_z_index(11)

            # Property card
            detail = Text(
                f"h={sd['h']:.1f} kJ/kg  RH={sd['RH']:.0f}%",
                font_size=12, color="#8B95A5",
            ).next_to(label, DOWN, buff=0.08, aligned_edge=LEFT)
            detail.set_z_index(11)

            dots.append(dot)
            all_labels.add(label, detail)

            self.play(GrowFromCenter(dot), run_time=0.4)
            self.play(FadeIn(label), run_time=0.25)
            self.play(FadeIn(detail), run_time=0.2)
            self.wait(0.4)

        # ════════════════════════════════════════════════════════════════
        # PHASE 3 — Trail Lines (~3s)
        # ════════════════════════════════════════════════════════════════

        for i in range(len(dots) - 1):
            sid_dst = STAGE_ORDER[i + 1]
            arrow_color = STAGE_META[sid_dst]["color"]

            trail_arrow = Arrow(
                start=dots[i].get_center(),
                end=dots[i + 1].get_center(),
                color=arrow_color,
                stroke_width=2.5,
                buff=0.15,
                max_tip_length_to_length_ratio=0.12,
            )

            self.play(Create(trail_arrow), run_time=0.5)
            self.wait(0.3)

        # ════════════════════════════════════════════════════════════════
        # PHASE 4 — Energy Summary (~3s)
        # ════════════════════════════════════════════════════════════════

        total_load = energy_data.get("total_cooling_load", 0)
        moisture = energy_data.get("moisture_removed_g", 0)
        sensible = energy_data.get("coil_sensible", 0)
        shf = sensible / total_load if total_load > 0 else 0

        energy_lines = [
            ("TOTAL COOLING LOAD", f"{total_load:.2f} kJ/kg"),
            ("MOISTURE REMOVED", f"{moisture:.2f} g/kg"),
            ("SENSIBLE HEAT FACTOR", f"{shf:.3f}"),
        ]

        y_start = 2.5

        for idx, (label_text, value_text) in enumerate(energy_lines):
            label = Text(
                label_text, font_size=13, color="#8B95A5",
            ).move_to([5.2, y_start - idx * 1.0, 0])

            value = Text(
                value_text, font_size=20, color="#00C9FF",
                weight="BOLD",
            ).next_to(label, DOWN, buff=0.12)

            self.play(FadeIn(VGroup(label, value)), run_time=0.35)
            self.wait(0.15)

        # ════════════════════════════════════════════════════════════════
        # PHASE 5 — Outro (hold + fade)
        # ════════════════════════════════════════════════════════════════

        self.wait(1.5)

        all_mobs = Group(*self.mobjects)
        self.play(FadeOut(all_mobs), run_time=1.0)
        self.wait(0.3)
