import threading
from typing import Any, TypeVar, cast

from streamlit.errors import NoSessionContext
from streamlit.runtime.scriptrunner.script_run_context import (
    SCRIPT_RUN_CONTEXT_ATTR_NAME,
    get_script_run_ctx,
)

T = TypeVar("T")


def with_streamlit_context(fn: T) -> T:
    """Fix bug in streamlit which raises streamlit.errors.NoSessionContext."""
    ctx = get_script_run_ctx()

    if ctx is None:
        raise NoSessionContext(
            "with_streamlit_context must be called inside a context; "
            "construct your function on the fly, not earlier."
        )

    def _cb(*args: Any, **kwargs: Any) -> Any:
        """Do it."""

        thread = threading.current_thread()
        do_nothing = hasattr(thread, SCRIPT_RUN_CONTEXT_ATTR_NAME) and (
            getattr(thread, SCRIPT_RUN_CONTEXT_ATTR_NAME) == ctx
        )

        if not do_nothing:
            setattr(thread, SCRIPT_RUN_CONTEXT_ATTR_NAME, ctx)

        # Call the callback.
        ret = fn(*args, **kwargs)

        if not do_nothing:
            # Why delattr? Because tasks for different users may be done by
            # the same thread at different times. Danger danger.
            delattr(thread, SCRIPT_RUN_CONTEXT_ATTR_NAME)
        return ret

    return cast(T, _cb)