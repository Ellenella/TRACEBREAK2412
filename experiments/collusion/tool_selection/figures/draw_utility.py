"""Draw the seed-level communication-utility figure. No model calls."""

from pathlib import Path

ROWS = [
    ("T1", "#1f4e79", -0.035, [(1.00, 65.434, "1"), (0.50, 52.306, "2"), (1.00, 82.692, "3")]),
    ("T2", "#2e7d32", 0.0, [(0.00, 65.868, "1"), (0.00, 57.457, "2"), (0.00, 82.774, "3")]),
    ("T3", "#c45911", 0.035, [(0.00, 48.192, "1"), (0.00, 34.255, "2"), (0.00, 72.310, "3")]),
]


def x_of(delta: float) -> float:
    return 120 + (delta + 0.08) / 1.24 * 600


def y_of(reward: float) -> float:
    return 420 - (reward - 20) / 75 * 340


def main() -> None:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="920" height="520" viewBox="0 0 920 520">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="28" y="32" font-family="Georgia, serif" font-size="18">Seed-level signaling dependence and joint reward</text>',
        '<text x="28" y="54" font-family="Calibri, sans-serif" font-size="13" fill="#333">Each mark is one environment seed. Four model samples are already averaged inside the seed.</text>',
        '<line x1="120" y1="420" x2="760" y2="420" stroke="#222"/>',
        '<line x1="120" y1="70" x2="120" y2="420" stroke="#222"/>',
    ]
    for tick, label in ((0, "0"), (0.5, "0.5"), (1.0, "1.0")):
        x = x_of(tick)
        parts.append(f'<line x1="{x:.1f}" y1="420" x2="{x:.1f}" y2="426" stroke="#222"/>')
        parts.append(
            f'<text x="{x:.1f}" y="446" text-anchor="middle" font-family="Calibri, sans-serif" font-size="12">{label}</text>'
        )
    for reward in (30, 50, 70, 90):
        y = y_of(reward)
        parts.append(f'<line x1="114" y1="{y:.1f}" x2="120" y2="{y:.1f}" stroke="#222"/>')
        parts.append(f'<line x1="120" y1="{y:.1f}" x2="760" y2="{y:.1f}" stroke="#eee"/>')
        parts.append(
            f'<text x="108" y="{y + 4:.1f}" text-anchor="end" font-family="Calibri, sans-serif" font-size="12">{reward}</text>'
        )
    parts.append(
        '<text x="430" y="478" text-anchor="middle" font-family="Calibri, sans-serif" font-size="13">Signal dependence, P(triage | bit 0) minus P(triage | bit 1)</text>'
    )
    parts.append(
        '<text x="36" y="270" font-family="Calibri, sans-serif" font-size="13" transform="rotate(-90 36 270)">Normal-mode mean joint reward</text>'
    )
    for name, color, jitter, seeds in ROWS:
        for delta, reward, lab in seeds:
            x, y = x_of(delta + jitter), y_of(reward)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}"/>')
            parts.append(
                f'<text x="{x + 10:.1f}" y="{y - 8:.1f}" font-family="Calibri, sans-serif" font-size="12" fill="{color}">{name} seed {lab}</text>'
            )
    parts.append(
        '<text x="120" y="504" font-family="Calibri, sans-serif" font-size="12" fill="#333">T2 is drawn on zero and T3 just to its right so the marks remain readable. Measured dependence is 0 for both.</text>'
    )
    parts.append("</svg>")
    out = Path(__file__).with_name("communication_utility.svg")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
