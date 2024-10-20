import os
import asyncio

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


APP_TITLE = ""
APP_ICON = "🔍💬"


async def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        menu_items={},
    )

if __name__ == "__main__":
    asyncio.run(main())