project = "Orders Project"
author = "kkaarroollm"
copyright = "2024, kkaarroollm"

extensions = ["myst_parser", "sphinxcontrib.mermaid"]
myst_enable_extensions = ["colon_fence", "deflist"]
myst_fence_as_directive = ["mermaid"]

html_theme = "furo"
html_title = "Orders Project"
html_static_path = []
html_extra_path = ["CNAME"]

exclude_patterns = ["_build"]
