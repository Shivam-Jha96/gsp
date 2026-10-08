"""
Common Streamlit UI helper utilities, decorators, and control components.
"""

from typing import Optional, List, Any
import streamlit as st


def render_segmented_filter(
    label: str,
    options: List[str],
    default_ix: Optional[int] = 0,
    key: Optional[str] = None,
    on_change: Any = None
) -> Optional[str]:
    """
    Renders resilient segmented/pill filter buttons across Streamlit versions.
    """
    default_val = options[default_ix] if (default_ix is not None and 0 <= default_ix < len(options)) else None
    if key:
        if key not in st.session_state or st.session_state[key] is None or st.session_state[key] not in options:
            st.session_state[key] = default_val
        kwargs = {"key": key, "label_visibility": "collapsed"}
        if on_change is not None:
            kwargs["on_change"] = on_change
        if hasattr(st, "pills"):
            res = st.pills(label, options, **kwargs)
            return res or default_val
        elif hasattr(st, "segmented_control"):
            res = st.segmented_control(label, options, **kwargs)
            return res or default_val
        else:
            return st.radio(label, options, index=default_ix, horizontal=True, **kwargs)
    else:
        kwargs = {"default": default_val, "label_visibility": "collapsed"}
        if hasattr(st, "pills"):
            res = st.pills(label, options, **kwargs)
            return res or default_val
        elif hasattr(st, "segmented_control"):
            res = st.segmented_control(label, options, **kwargs)
            return res or default_val
        else:
            return st.radio(label, options, index=default_ix, horizontal=True, label_visibility="collapsed")


def make_fragment_decorator(run_every: Optional[str] = "5m", key: Optional[str] = None):
    """
    Resilient decorator providing isolated fragment rendering with automated polling.
    Falls back gracefully if fragment API is unsupported.
    """
    def decorator(func):
        frag_key = key or func.__name__
        if hasattr(st, "fragment"):
            kwargs = {}
            if run_every is not None:
                kwargs["run_every"] = run_every
            if frag_key is not None:
                kwargs["key"] = frag_key
            return st.fragment(**kwargs)(func)
        elif hasattr(st, "experimental_fragment"):
            kwargs = {}
            if run_every is not None:
                kwargs["run_every"] = run_every
            return st.experimental_fragment(**kwargs)(func)  # type: ignore[attr-defined]
        return func
    return decorator


def rerun_scoped(target: Any):
    """
    Triggers scoped Streamlit fragment rerun while syncing preference state to query params.
    """
    try:
        from ui.state_persistence import sync_all_preferences_to_query_params
        sync_all_preferences_to_query_params()
    except Exception:
        try:
            from src.ui.state_persistence import sync_all_preferences_to_query_params
            sync_all_preferences_to_query_params()
        except Exception:
            pass

    try:
        st.rerun(scope=target)
    except TypeError:
        try:
            st.rerun(target)
        except Exception:
            st.rerun()
    except Exception:
        st.rerun()
