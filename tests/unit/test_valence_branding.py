import os
import unittest

class TestValenceBranding(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.app_path = os.path.join(self.root_dir, 'src', 'ui', 'app.py')
        self.styles_path = os.path.join(self.root_dir, 'src', 'ui', 'styles.py')
        self.header_path = os.path.join(self.root_dir, 'src', 'ui', 'components', 'header.py')
        with open(self.app_path, 'r', encoding='utf-8') as f:
            self.app_content = f.read()
        with open(self.styles_path, 'r', encoding='utf-8') as f:
            self.styles_content = f.read()
        with open(self.header_path, 'r', encoding='utf-8') as f:
            self.header_content = f.read()
        self.all_ui_content = f"{self.app_content}\n{self.styles_content}\n{self.header_content}"

    def test_branding_assets_exist(self):
        # Master vector assets
        flat_svg = os.path.join(self.root_dir, 'assets', 'valence_logo_flat.svg')
        badge_svg = os.path.join(self.root_dir, 'assets', 'valence_logo.svg')
        avatar_png = os.path.join(self.root_dir, 'assets', 'valence_github_avatar.png')
        ui_flat_svg = os.path.join(self.root_dir, 'src', 'ui', 'assets', 'valence_logo_flat.svg')

        self.assertTrue(os.path.exists(flat_svg), f"Missing {flat_svg}")
        self.assertTrue(os.path.exists(badge_svg), f"Missing {badge_svg}")
        self.assertTrue(os.path.exists(avatar_png), f"Missing {avatar_png}")
        self.assertTrue(os.path.exists(ui_flat_svg), f"Missing {ui_flat_svg}")

    def test_app_title_is_valence(self):
        self.assertIn('page_title="Valence"', self.app_content)
        self.assertIn('>VALENCE</span>', self.all_ui_content)

    def test_ui_enhancements_structure(self):
        # 1. Fragment auto-polling decorator
        self.assertIn('@make_fragment_decorator(run_every="5m")', self.app_content)
        self.assertIn('def render_dashboard():', self.app_content)
        
        # 2. Updated timestamp pill displays only timestamp and timezone
        self.assertIn('UPDATED {time_display_str}</span>', self.header_content)
        self.assertNotIn('({relative_display_str})</span>', self.header_content)
        
        # 3. Dynamic timezone support in telemetry call
        self.assertIn('target_tz_str=current_target_tz', self.header_content)
        self.assertIn('tz_abbr=current_tz_abbr', self.header_content)
        
        # 4. Spacing deconfliction
        self.assertIn('margin-bottom: 10px !important;', self.styles_content)
        
        # 5. Live Intelligence feed container demarcation
        self.assertIn('.st-key-live_intelligence_feed_container', self.styles_content)
        self.assertIn('margin-top: 10px !important;', self.styles_content)
        self.assertIn('border: 1px solid var(--card-border) !important;', self.styles_content)

if __name__ == '__main__':
    unittest.main()
