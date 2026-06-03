def test_app_imports() -> None:
    from trading_bot.app import app

    assert app.title == "Tradebot Backend"

