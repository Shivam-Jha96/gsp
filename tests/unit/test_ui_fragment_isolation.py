import os
import unittest
import ast

class TestUIFragmentIsolation(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.app_path = os.path.join(self.root_dir, 'src', 'ui', 'app.py')
        self.header_path = os.path.join(self.root_dir, 'src', 'ui', 'components', 'header.py')
        self.toolbar_path = os.path.join(self.root_dir, 'src', 'ui', 'components', 'toolbar.py')
        self.analytics_path = os.path.join(self.root_dir, 'src', 'ui', 'components', 'analytics.py')
        self.feed_path = os.path.join(self.root_dir, 'src', 'ui', 'components', 'feed.py')

        with open(self.app_path, 'r', encoding='utf-8') as f:
            self.app_content = f.read()
        with open(self.header_path, 'r', encoding='utf-8') as f:
            self.header_content = f.read()
        with open(self.toolbar_path, 'r', encoding='utf-8') as f:
            self.toolbar_content = f.read()
        with open(self.analytics_path, 'r', encoding='utf-8') as f:
            self.analytics_content = f.read()
        with open(self.feed_path, 'r', encoding='utf-8') as f:
            self.feed_content = f.read()

        self.all_ui_content = (
            f"{self.app_content}\n"
            f"{self.header_content}\n"
            f"{self.toolbar_content}\n"
            f"{self.analytics_content}\n"
            f"{self.feed_content}"
        )

    def test_modular_fragment_functions_exist(self):
        # Sibling fragment definitions across modular architecture
        self.assertIn('def render_header_banner(', self.header_content)
        self.assertIn('def render_usp_banner():', self.header_content)
        self.assertIn('def render_filter_toolbar(', self.toolbar_content)
        self.assertIn('def render_analytics_surface(', self.analytics_content)
        self.assertIn('def render_live_intelligence_feed(', self.feed_content)
        self.assertIn('def render_dashboard():', self.app_content)

        # App orchestrator imports and calls modular components
        self.assertIn('render_header_banner(df_signals', self.app_content)
        self.assertIn('render_usp_banner()', self.app_content)
        self.assertIn('render_filter_toolbar(df_signals)', self.app_content)
        self.assertIn('render_analytics_surface(df_signals', self.app_content)
        self.assertIn('render_live_intelligence_feed(df_payloads', self.app_content)

    def test_fragment_decorators_applied(self):
        # Verify targeted components use make_fragment_decorator
        def find_decorator_for_func(content, func_def_name):
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if func_def_name in line:
                    for prev in range(max(0, i - 3), i):
                        if "@make_fragment_decorator" in lines[prev]:
                            return lines[prev]
            return None

        self.assertIsNotNone(find_decorator_for_func(self.header_content, 'def render_header_banner('))
        self.assertIsNotNone(find_decorator_for_func(self.analytics_content, 'def render_analytics_surface('))
        self.assertIsNotNone(find_decorator_for_func(self.feed_content, 'def render_live_intelligence_feed('))
        self.assertIsNotNone(find_decorator_for_func(self.app_content, 'def render_dashboard():'))

    def test_filter_toolbar_scoped_reruns(self):
        # Verify selectbox on_change triggers targeted rerun scopes in toolbar component
        self.assertIn('on_change=lambda: rerun_scoped(["render_analytics_surface", "render_live_intelligence_feed"])', self.toolbar_content)
        self.assertIn('on_change=lambda: rerun_scoped("render_analytics_surface")', self.toolbar_content)
        self.assertIn('on_change=lambda: rerun_scoped(["render_header_banner", "render_analytics_surface", "render_live_intelligence_feed"])', self.toolbar_content)
        self.assertIn('on_change=lambda: rerun_scoped("app")', self.toolbar_content)

    def test_sentiment_pills_in_live_feed_fragment(self):
        # Feed sentiment pills must be inside render_live_intelligence_feed component
        self.assertIn('feed_sentiment_pills', self.feed_content)

if __name__ == '__main__':
    unittest.main()
