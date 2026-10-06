"""Small runtime localization layer for the Streamlit interface."""

import json
from pathlib import Path

_TRANSLATION_DIR = Path(__file__).parent / "translations"
ENGLISH_TEXT = json.loads((_TRANSLATION_DIR / "en.json").read_text(encoding="utf-8"))
TELUGU_TEXT = json.loads((_TRANSLATION_DIR / "te.json").read_text(encoding="utf-8"))
TELUGU = "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41"
ENGLISH = "English"


def translate(text, language=TELUGU):
    """Translate known interface phrases with the selected language catalog."""
    if not isinstance(text, str) or language != TELUGU:
        return text
    for english in sorted(TELUGU_TEXT, key=len, reverse=True):
        text = text.replace(english, TELUGU_TEXT[english])
    return text


def initialize_language(streamlit_module):
    """Restore language from the URL after a browser refresh."""
    if "header_language" not in streamlit_module.session_state:
        try:
            saved = streamlit_module.query_params.get("lang", "en")
        except Exception:
            saved = "en"
        streamlit_module.session_state.header_language = TELUGU if saved == "te" else ENGLISH


def persist_language(streamlit_module):
    """Keep the language choice in the URL so reloads preserve it."""
    try:
        streamlit_module.query_params["lang"] = (
            "te" if streamlit_module.session_state.get("header_language") == TELUGU else "en"
        )
    except Exception:
        pass


def install_localization(streamlit_module):
    """Translate text passed through shared Streamlit display and input APIs."""
    from streamlit.delta_generator import DeltaGenerator

    if getattr(DeltaGenerator, "_cropcare_localization_installed", False):
        return

    methods = (
        "markdown", "write", "caption", "info", "warning", "error", "success",
        "title", "header", "subheader", "text", "button", "form_submit_button",
        "download_button", "selectbox", "radio", "checkbox", "text_input",
        "number_input", "file_uploader", "camera_input", "metric", "date_input",
        "multiselect", "expander", "dataframe", "table", "bar_chart", "line_chart", "area_chart",
    )
    for method_name in methods:
        original = getattr(DeltaGenerator, method_name, None)
        if original is None:
            continue

        def make_wrapper(method, wrapped_name):
            def localized(self, *args, **kwargs):
                try:
                    is_telugu = streamlit_module.session_state.get("header_language") == TELUGU
                except Exception:
                    is_telugu = False
                if not is_telugu:
                    return method(self, *args, **kwargs)

                args = list(args)
                if args and isinstance(args[0], str):
                    args[0] = translate(args[0])
                for key in ("label", "placeholder", "help"):
                    if isinstance(kwargs.get(key), str):
                        kwargs[key] = translate(kwargs[key])

                if wrapped_name in {"selectbox", "radio", "multiselect"}:
                    formatter_index = next(
                        (i for i in range(2, len(args)) if callable(args[i])), None
                    )
                    formatter = kwargs.get("format_func")
                    if formatter is None and formatter_index is not None:
                        formatter = args[formatter_index]
                    def localized_option(option):
                        label = formatter(option) if formatter else option
                        return translate(label) if isinstance(label, str) else label
                    if formatter_index is not None:
                        args[formatter_index] = localized_option
                    else:
                        kwargs["format_func"] = localized_option

                if wrapped_name in {"dataframe", "table"} and args and hasattr(args[0], "columns"):
                    try:
                        args[0] = args[0].rename(columns=lambda col: translate(str(col)))
                    except Exception:
                        pass

                return method(self, *tuple(args), **kwargs)
            return localized

        setattr(DeltaGenerator, method_name, make_wrapper(original, method_name))

    DeltaGenerator._cropcare_localization_installed = True
