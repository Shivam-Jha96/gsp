"""
Valence UI Component Architecture.
Decomposed, single-responsibility frontend modules.
"""

from ui.components.common import (
    render_segmented_filter,
    make_fragment_decorator,
    rerun_scoped,
    render_clean_html,
)
from ui.components.header import (
    render_header_banner,
    render_usp_banner,
    render_regulatory_disclaimer,
)
from ui.components.toolbar import (
    render_filter_toolbar,
)
from ui.components.analytics import (
    render_analytics_surface,
)
from ui.components.feed import (
    clean_news_item,
    render_live_intelligence_feed,
)
from ui.components.ledger import (
    render_forward_test_ledger_section,
)

__all__ = [
    "render_clean_html",
    "render_segmented_filter",
    "make_fragment_decorator",
    "rerun_scoped",
    "render_header_banner",
    "render_usp_banner",
    "render_regulatory_disclaimer",
    "render_filter_toolbar",
    "render_analytics_surface",
    "clean_news_item",
    "render_live_intelligence_feed",
    "render_forward_test_ledger_section",
]
