from app.parents import _with_scores

def test_with_scores_empty_list_returns_empty():
    assert _with_scores([]) == []
