# Telanico 3D Web

Play the public preview: **https://sgdenikin-sys.github.io/Telanico-3D-Web/**

This repository contains the exported single-threaded Godot Compatibility Web runtime and its publication infrastructure. Blender scenes, source generators, vendor downloads and the development project stay in the private Telanico-3D-Lab repository.

The importer checks the exact allowlisted `codex/telanico-overworld-v2-1` feature branch every ten minutes and when publication infrastructure changes. For a controlled release, `tools/preview-source.json` pins the successful private Actions `run_id` and `commit`; the importer fetches that exact run and rejects failed or mismatched candidates. The existing workflow also accepts an optional `source_run_id` dispatch input. Without a pin/input, it follows the newest candidate. It requires the newest Godot Web playable run to succeed, verifies its artifact identity and permits only browser runtime filenames. Failed, expired or mismatched candidates preserve the previous release; an unchanged commit is a no-op. No private main merge or manually copied Actions run number is required.

`site/build.json` and the in-game HUD identify the published source commit. A changed release is deployed through GitHub Pages, then its actual HTTPS desktop and phone-landscape WebGL startup is verified by the publishing workflow. Runtime assets are credited in `site/LICENSES.html`.

Use landscape orientation: tap a department, review the route and choose Walk. Drag pans; pinch or wheel zooms. Inspect enables constrained orbit; Reset restores the north-up overview. The animated humanoid is a temporary courier, not final Cooper art. Departments currently have placeholder entrances; invoice quests and interiors are not implemented in this preview.
