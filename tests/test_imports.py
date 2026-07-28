import pytest


def test_import_tradeai():
    import src_python
    assert hasattr(src_python, "__name__")


def test_import_components():
    from src_python import AI, broker, run_client, graphic
    assert AI is not None
    assert broker is not None
    assert run_client is not None
    assert graphic is not None
