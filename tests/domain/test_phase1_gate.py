"""Phase 1 gate: data model + state transition regression (P1-7)."""

import ast
from pathlib import Path

import chessmind_ab.domain as domain
from chessmind_ab.domain import (
    Board,
    Color,
    GameState,
    GameStatus,
    Move,
    MoveType,
    Piece,
    PieceType,
    Position,
    StateTransition,
)


def test_domain_exports_phase1_foundation() -> None:
    required = {
        "Color",
        "PieceType",
        "GameStatus",
        "MoveType",
        "Position",
        "Piece",
        "Board",
        "Move",
        "GameState",
        "StateTransition",
    }
    assert required.issubset(set(domain.__all__))


def test_domain_sources_do_not_import_ai_or_ui() -> None:
    domain_root = Path(domain.__file__).resolve().parent
    forbidden = (
        "chessmind_ab.ai",
        "chessmind_ab.search",
        "chessmind_ab.application",
        "chessmind_ab.presentation",
        "chessmind_ab.ui",
    )
    for path in domain_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            else:
                continue
            for name in names:
                assert not any(
                    name == item or name.startswith(item + ".") for item in forbidden
                ), f"{path.name} imports forbidden module {name}"


def test_state_transition_is_copy_on_move_end_to_end() -> None:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    e2 = Position.from_chess_notation("e2")
    e4 = Position.from_chess_notation("e4")
    pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    board.set_piece(e2, pawn)

    parent = GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )
    parent.validate_king_invariant()

    child = StateTransition.apply(
        parent,
        Move(
            from_position=e2,
            to_position=e4,
            moving_piece=pawn,
            move_type=MoveType.PAWN_DOUBLE,
        ),
    )

    assert parent.board.get_piece(e2) == pawn
    assert parent.side_to_move is Color.WHITE
    assert parent.ply_count == 0
    assert child.board.get_piece(e2) is None
    assert child.board.get_piece(e4) == pawn
    assert child.side_to_move is Color.BLACK
    assert child.ply_count == 1
    child.validate_king_invariant()
