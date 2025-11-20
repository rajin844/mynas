import os

def fix_material_imports(base_dir="frontend_flutter/lib"):
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".dart"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Skip if already imported
                if "package:flutter/material.dart" in content:
                    continue

                # Only patch if file contains UI code (Widget, Scaffold, etc.)
                if any(keyword in content for keyword in ["Widget", "Scaffold", "MaterialApp", "AppBar", "BuildContext"]):
                    print(f"Fixing imports in {file_path}")
                    content = f"import 'package:flutter/material.dart';\n" + content
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

if __name__ == "__main__":
    fix_material_imports()
    print("✅ All Flutter UI files now have material.dart imported!")
