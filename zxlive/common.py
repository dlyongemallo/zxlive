import typing
from typing import Tuple
from typing_extensions import TypeAlias
import pyzx

VT: TypeAlias = int
ET: TypeAlias = Tuple[int,int]
GraphT: TypeAlias = pyzx.graph.graph_s.GraphS

from pyzx.graph.graph_s import GraphS as Graph
