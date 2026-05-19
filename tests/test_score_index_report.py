import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "score_index_report.py"
spec = importlib.util.spec_from_file_location("score_index_report", MODULE_PATH)
score_index_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(score_index_report)


def table_row_cells(row: str) -> list[str]:
    assert row.startswith("|")
    assert row.endswith("|")
    cells = []
    current = []
    escaped = False
    for char in row[1:-1]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


class ScoreIndexReportTests(unittest.TestCase):
    def test_render_markdown_escapes_pipe_characters_in_table_cells(self):
        index = {
            "source_path": "sources/example.pdf",
            "pdf_sheet_offset_for_primary_score_pages": 54,
            "notes": "Example score index.",
            "chants": [
                {
                    "number": 1,
                    "id": "chant|with|pipes",
                    "title": "Title | Subtitle",
                    "primary_score_pages": [1, 3],
                }
            ],
        }

        markdown = score_index_report.render_markdown(index)

        data_row = markdown.splitlines()[-1]
        self.assertEqual(
            table_row_cells(data_row),
            [
                "1",
                "`chant\\|with\\|pipes`",
                "Title \\| Subtitle",
                "1, 3",
                "55, 57",
            ],
        )


if __name__ == "__main__":
    unittest.main()
