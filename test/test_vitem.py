"""Tests for visual graph items (VItem), such as dummy nodes and their labels.

These tests ensure that rendering artifacts—especially the visual positioning of
dummy node labels—are robust. For instance, tall LaTeX expressions (like integrals 
or fractions) shouldn't overlap with the node body.
"""

import pytest
from pyzx.utils import VertexType
from pytestqt.qtbot import QtBot

from zxlive.graphscene import GraphScene
from zxlive.common import SCALE

def test_dummy_label_position(qtbot: QtBot) -> None:
    """Test that dummy labels sit cleanly above the node without overlapping.
    
    This verifies the regression fix where tall LaTeX formulas (e.g. `$\\int$`) 
    with a simple fixed upward offset would visually bleed into and overlap the 
    dummy circle below it. The label's `y` position should be dynamically 
    anchored based on its calculated bounding height.
    """
    from zxlive.common import new_graph
    g = new_graph()
    
    # 1. Plain text label
    v_text = g.add_vertex(VertexType.DUMMY, qubit=0, row=0)
    g.set_vdata(v_text, 'text', 'hello')
    
    # 2. LaTeX label
    v_latex = g.add_vertex(VertexType.DUMMY, qubit=1, row=0)
    g.set_vdata(v_latex, 'text', r'$\int$')
    
    scene = GraphScene()
    scene.set_graph(g)
    
    vitem_text = scene.vertex_map[v_text]
    vitem_latex = scene.vertex_map[v_latex]
    
    # Refresh to ensure dummy labels are created and positioned
    vitem_text.refresh()
    vitem_latex.refresh()
    
    gap = 2.0
    node_top = -0.06 * SCALE
    
    # Check text item position
    assert vitem_text.dummy_text_item is not None
    text_rect = vitem_text.dummy_text_item.boundingRect()
    expected_text_y = node_top - gap - text_rect.height()
    assert vitem_text.dummy_text_item.pos().y() == pytest.approx(expected_text_y)
    
    # Check svg item position
    assert vitem_latex.dummy_svg_item is not None
    assert vitem_latex._dummy_svg_renderer is not None
    svg_rect = vitem_latex._dummy_svg_renderer.viewBoxF()
    expected_svg_y = node_top - gap - svg_rect.height()
    assert vitem_latex.dummy_svg_item.pos().y() == pytest.approx(expected_svg_y)


def test_boundary_phase_cleared_on_refresh(qtbot: QtBot) -> None:
    """Test that boundary vertices never display stale phase labels.

    Regression test for #462.
    """
    from zxlive.common import new_graph

    g = new_graph()
    v = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)

    scene = GraphScene()
    scene.set_graph(g)
    vitem = scene.vertex_map[v]

    assert vitem.phase_item.toPlainText() == ""

    vitem.phase_item.setPlainText("π/4")
    assert vitem.phase_item.toPlainText() == "π/4"

    vitem.phase_item.refresh()
    assert vitem.phase_item.toPlainText() == ""


def test_boundary_io_labels_preserved_on_refresh(qtbot: QtBot) -> None:
    """Test that I/O labels on boundary vertices survive a refresh.
    """
    from zxlive.common import new_graph

    g = new_graph()
    v_in = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
    v_out = g.add_vertex(VertexType.BOUNDARY, qubit=1, row=2)

    scene = GraphScene()
    scene.set_graph(g)

    scene.vertex_map[v_in].phase_item.setPlainText("in-0")
    scene.vertex_map[v_out].phase_item.setPlainText("out-0")

    scene.vertex_map[v_in].phase_item.refresh()
    scene.vertex_map[v_out].phase_item.refresh()

    assert scene.vertex_map[v_in].phase_item.toPlainText() == "in-0"
    assert scene.vertex_map[v_out].phase_item.toPlainText() == "out-0"


def test_boundary_phase_cleared_after_type_change(qtbot: QtBot) -> None:
    """Test that changing a vertex from Z to BOUNDARY clears its phase label.

    Simulates scenario where incremental graph update changes vertex's type from
    Z to BOUNDARY. The PhaseItem text set for the Z spider must be cleared.
    """
    from fractions import Fraction
    from zxlive.common import new_graph

    g = new_graph()
    v = g.add_vertex(VertexType.Z, qubit=0, row=0, phase=Fraction(1, 4))

    scene = GraphScene()
    scene.set_graph(g)
    vitem = scene.vertex_map[v]
    assert vitem.phase_item.toPlainText() != ""

    new_g = new_graph()
    new_v = new_g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)

    scene.update_graph(new_g)

    new_vitem = scene.vertex_map[new_v]
    assert new_vitem.phase_item.toPlainText() == ""
