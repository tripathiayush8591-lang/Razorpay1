"""
Automated Pytest wrapper for Task 24 End-to-End Rehearsal.
"""

from app.demo.rehearsal import RehearsalRunner


def test_end_to_end_rehearsal_all_stages():
    """Executes the full 11-stage automated rehearsal runner."""
    runner = RehearsalRunner()
    success = runner.run_all()
    assert success is True, f"Rehearsal stages failed: {[k for k, v in runner.results.items() if not v]}"
