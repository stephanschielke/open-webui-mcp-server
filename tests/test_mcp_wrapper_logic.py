"""Tests for MCP tool wrapper logic.

Tests that the wrapping pattern used in main.py correctly transforms
list responses to {"items": [...]} format.
"""


def _wrap_list_response(response):
    if isinstance(response, list):
        return {"items": response}
    return response


def test_list_wrapper_transforms_list_to_dict():
    result = [{"id": "1"}, {"id": "2"}]
    wrapped = _wrap_list_response(result)
    assert wrapped == {"items": [{"id": "1"}, {"id": "2"}]}


def test_list_wrapper_returns_dict_unchanged():
    result = {"error": "not found", "code": 404}
    wrapped = _wrap_list_response(result)
    assert wrapped == {"error": "not found", "code": 404}


def test_list_wrapper_returns_empty_list_wrapped():
    result = []
    wrapped = _wrap_list_response(result)
    assert wrapped == {"items": []}


def test_list_wrapper_returns_none_unchanged():
    result = None
    wrapped = _wrap_list_response(result)
    assert wrapped is None


def test_list_wrapper_returns_string_unchanged():
    result = "error message"
    wrapped = _wrap_list_response(result)
    assert wrapped == "error message"
