"""Tests for TikZ proof export (zxlive.tikz)."""

import re

from pyzx.utils import VertexType
from pytestqt.qtbot import QtBot

from zxlive.common import GraphT, new_graph
from zxlive.proof import ProofModel, Rewrite
from zxlive.tikz import proof_to_tikz


def _make_graph(qubit_min: float, qubit_max: float) -> GraphT:
    """Build a minimal graph spanning the given qubit range."""
    g = new_graph()
    g.add_vertex(VertexType.Z, qubit=qubit_min, row=0)
    g.add_vertex(VertexType.Z, qubit=qubit_max, row=1)
    return g


# Regex for the equal-sign nodes emitted by proof_to_tikz.
# Captures the y-coordinate as group 1.
_EQ_NODE_RE = re.compile(
    r"\\node \[style=none\] \(\d+\) at \([^,]+, (-?[\d.]+)\)"
)

# Regex for Z-spider vertex nodes. Captures (x, y) as groups 1 and 2.
_Z_NODE_RE = re.compile(
    r"\\node \[style=Z dot\] \(\d+\) at \((-?[\d.]+), (-?[\d.]+)\)"
)


def test_eq_sign_uses_max_height(qtbot: QtBot) -> None:
    """Equal sign between steps is centred using the taller of the two graphs."""
    tall = _make_graph(0, 4)   # height 4
    short = _make_graph(0, 1)  # height 1

    proof = ProofModel(tall)
    proof.add_rewrite(Rewrite("r", "r", short))

    tikz = proof_to_tikz(proof)
    eq_nodes = _EQ_NODE_RE.findall(tikz)
    assert len(eq_nodes) == 1

    y = float(eq_nodes[0])
    # yoffset starts at -10, so y = -(-10) - eq_height/2 = 10 - eq_height/2.
    # With the fix, eq_height = max(4, 1) = 4, giving y = 8.0.
    # Without the fix, eq_height = 1, giving y = 9.5.
    assert y == 8.0


def test_eq_sign_symmetric_heights(qtbot: QtBot) -> None:
    """When adjacent graphs have equal heights, eq_height equals that height."""
    g1 = _make_graph(0, 3)
    g2 = _make_graph(0, 3)

    proof = ProofModel(g1)
    proof.add_rewrite(Rewrite("r", "r", g2))

    tikz = proof_to_tikz(proof)
    eq_nodes = _EQ_NODE_RE.findall(tikz)
    assert len(eq_nodes) == 1

    y = float(eq_nodes[0])
    # eq_height = max(3, 3) = 3, so y = 10 - 1.5 = 8.5.
    assert y == 8.5


def test_eq_sign_short_then_tall(qtbot: QtBot) -> None:
    """Equal sign is still correct when the second graph is taller."""
    short = _make_graph(0, 1)  # height 1
    tall = _make_graph(0, 5)   # height 5

    proof = ProofModel(short)
    proof.add_rewrite(Rewrite("r", "r", tall))

    tikz = proof_to_tikz(proof)
    eq_nodes = _EQ_NODE_RE.findall(tikz)
    assert len(eq_nodes) == 1

    y = float(eq_nodes[0])
    # eq_height = max(1, 5) = 5, so y = 10 - 2.5 = 7.5.
    assert y == 7.5


def test_offset_graph_is_normalised(qtbot: QtBot) -> None:
    """Graphs drawn away from the origin are translated to start at qubit 0."""
    g = _make_graph(5, 8)  # height 3, but offset to qubit 5-8

    proof = ProofModel(g)
    tikz = proof_to_tikz(proof)

    ys = [float(y) for _, y in _Z_NODE_RE.findall(tikz)]
    # After normalisation the qubit span should be 0..3, mapped to
    # y-coordinates -yoffset .. -(yoffset+3) = 10 .. 7.
    assert min(ys) == 7.0
    assert max(ys) == 10.0


def test_offset_graphs_align_eq_sign(qtbot: QtBot) -> None:
    """Equal sign aligns correctly even when graphs are offset from the origin."""
    # Both graphs have height 2 but sit at different qubit offsets.
    g1 = _make_graph(10, 12)  # height 2, offset at qubit 10
    g2 = _make_graph(3, 5)    # height 2, offset at qubit 3

    proof = ProofModel(g1)
    proof.add_rewrite(Rewrite("r", "r", g2))

    tikz = proof_to_tikz(proof)
    eq_nodes = _EQ_NODE_RE.findall(tikz)
    assert len(eq_nodes) == 1

    y = float(eq_nodes[0])
    # Both heights are 2 after normalisation, so eq_height = 2, y = 10 - 1.0 = 9.0.
    assert y == 9.0
