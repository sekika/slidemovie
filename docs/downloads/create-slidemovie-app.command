#!/bin/bash
# Creates ~/Applications/SlideMovie.app, which starts the installed slidemovie GUI.
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
slidemovie_bin="${SLIDEMOVIE_BIN:-$(command -v slidemovie || true)}"
app_dir="$HOME/Applications/SlideMovie.app"
contents_dir="$app_dir/Contents"
icon_path="$script_dir/slidemovie.icns"

if [[ -z "$slidemovie_bin" ]]; then
  echo "slidemovie was not found. Install it first, or set SLIDEMOVIE_BIN to its full path." >&2
  exit 1
fi
if [[ ! -f "$icon_path" ]]; then
  echo "Icon was not found: $icon_path" >&2
  exit 1
fi

mkdir -p "$contents_dir/MacOS" "$contents_dir/Resources"
cp "$icon_path" "$contents_dir/Resources/slidemovie.icns"

cat > "$contents_dir/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleDisplayName</key><string>SlideMovie</string>
  <key>CFBundleExecutable</key><string>SlideMovie</string>
  <key>CFBundleIconFile</key><string>slidemovie.icns</string>
  <key>CFBundleIdentifier</key><string>io.github.sekika.slidemovie.local</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF

cat > "$contents_dir/MacOS/SlideMovie" <<EOF
#!/bin/bash
exec "$slidemovie_bin" -g
EOF
chmod +x "$contents_dir/MacOS/SlideMovie"

open "$app_dir"
echo "Created and opened: $app_dir"
