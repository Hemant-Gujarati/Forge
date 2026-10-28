from forge.approvals import ApprovalStore


def test_request_and_approve() -> None:
    store = ApprovalStore(":memory:")
    request = store.request("write_file", "Change README.md")
    assert store.list() == [request]
    result = store.decide(request.id, approve=True)
    assert result is not None
    assert result.status == "approved"
    assert store.list() == []
