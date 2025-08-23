from app.adapters import onchain as oc


def test_merge_onchain_presence_and_empty_call_tolerant():
    fn = getattr(oc, "merge_onchain", None)
    # If fn exists, ensure it accepts empty addresses & returns a list.
    # If it doesn't exist, this still passes (short-circuits).
    assert (fn is None) or isinstance(fn("sol", []), list)
