import ast
import os
import unittest

class TestUIChartConfig(unittest.TestCase):
    def setUp(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.app_path = os.path.join(root_dir, 'src', 'ui', 'app.py')
        with open(self.app_path, 'r', encoding='utf-8') as f:
            self.source = f.read()

    def test_plotly_chart_config_removes_zoom(self):
        # Parse AST to ensure syntax is valid
        tree = ast.parse(self.source)
        self.assertIsNotNone(tree)

        # Verify scrollZoom is False
        self.assertIn("'scrollZoom': False", self.source)

        # Verify modeBarButtonsToRemove contains zoom2d, zoomIn2d, zoomOut2d
        self.assertIn("'modeBarButtonsToRemove': ['zoom2d', 'zoomIn2d', 'zoomOut2d']", self.source)

        # Verify yaxis has fixedrange=True to prevent vertical scaling deformation
        self.assertIn("fixedrange=True", self.source)

if __name__ == '__main__':
    unittest.main()
