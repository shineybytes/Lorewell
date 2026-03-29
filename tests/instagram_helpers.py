def patch_instagram_settings(
    mocker,
    *,
    graph_api_version="v25.0",
    instagram_account_id="17841473771500345",
    page_access_token="page-token",
    app_base_url="https://example.test",
):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.graph_api_version = graph_api_version
    mock_settings.instagram_account_id = instagram_account_id
    mock_settings.page_access_token = page_access_token
    mock_settings.app_base_url = app_base_url
    return mock_settings


def make_response(
    mocker,
    *,
    ok: bool,
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
):
    response = mocker.Mock()
    response.ok = ok
    response.status_code = status_code
    response.text = text
    if json_data is None:
        json_data = {}
    response.json.return_value = json_data
    return response
