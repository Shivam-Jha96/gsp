import os
import unittest
import ast

class TestUIFragmentIsolation(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.app_path = os.path.join(self.root_dir, 'src', 'ui', 'app.py')
        with open(self.app_path, 'r', encoding='utf-8') as f:
            self.app_content = f.read()

    def test_modular_fragment_functions_exist(self):
        # Sibling fragment definitions
        self.assertIn('def render_header_banner(', self.app_content)
        self.assertIn('def render_usp_banner():', self.app_content)
        self.assertIn('def render_filter_toolbar(', self.app_content)
        self.assertIn('def render_analytics_surface(', self.app_content)
        self.assertIn('def render_live_intelligence_feed(', self.app_content)
        self.assertIn('def render_dashboard():', self.app_content)

    def test_fragment_decorators_applied(self):
        # Verify targeted components use make_fragment_decorator
        lines = self.app_content.splitlines()
        
        def find_decorator_for_func(func_def_name):
            for i, line in enumerate(lines):
                if func_def_name in line:
                    for prev in range(max(0, i - 3), i):
                        if "@make_fragment_decorator" in lines[prev]:
                            return lines[prev]
            return None

        self.assertIsNotNone(find_decorator_for_func('def render_header_banner('))
        self.assertIsNotNone(find_decorator_for_func('def render_analytics_surface('))
        self.assertIsNotNone(find_decorator_for_func('def render_live_intelligence_feed('))

    def test_filter_toolbar_scoped_reruns(self):
        # Verify selectbox on_change triggers targeted rerun scopes
        self.assertIn('on_change=lambda: rerun_scoped(["render_analytics_surface", "render_live_intelligence_feed"])', self.app_content)
        self.assertIn('on_change=lambda: rerun_scoped("render_analytics_surface")', self.app_content)
        self.assertIn('on_change=lambda: rerun_scoped(["render_header_banner", "render_analytics_surface", "render_live_intelligence_feed"])', self.app_content)
        self.assertIn('on_change=lambda: rerun_scoped("app")', self.app_content)

    def test_sentiment_pills_in_live_feed_fragment(self):
        # Feed sentiment pills must be inside render_live_intelligence_feed
        feed_idx = self.app_content.find('def render_live_intelligence_feed(')
        dash_idx = self.app_content.find('def render_dashboard():')
        feed_section = self.app_content[feed_idx:dash_idx]
        self.assertIn('feed_sentiment_pills', feed_section)

if __name__ == '__main__':
    unittest.main()
