# Telanico 3D Web

Play the public preview: **https://sgdenikin-sys.github.io/Telanico-3D-Web/**

This repository contains the exported single-threaded Godot Compatibility Web runtime and its publication infrastructure. Blender scenes, source generators, vendor downloads and the development project stay in the private Telanico-3D-Lab repository.

V2.2 was built and validated on the existing Windows workstation because GitHub refused to start private Actions jobs with an account payment/spending restriction. It uses official Godot 4.6.3 and its matching single-thread Web template. `tools/release-v22.json` records the source commit, runtime SHA-256 hashes, native and desktop/full-phone-browser validation, and known testing limits. The Pages workflow verifies that manifest before deploying. No successful private V2.2 Action is claimed: `site/build.json` identifies the build as local.

The private-artifact importer is manual-only. Its unchanged `tools/preview-source.json` pin retains the previous tested V2.1 for an explicit rollback; invoking it intentionally restores V2.1. There is no scheduled importer to overwrite V2.2. Source models, private game source and test logs are not published here.

`site/build.json` and the in-game HUD identify the published source commit. A changed runtime snapshot is deployed through the existing GitHub Pages Action. Actual HTTPS desktop and touch-browser interactions are checked separately from the release workstation after deployment. Runtime assets are credited in `site/LICENSES.html`.

Use landscape orientation on phones. Choose Cooper, review the draft invoice and assistant, then tap departments and choose Walk. At a destination, choose Enter; Leave Office returns to the map. Drag pans; pinch or wheel zooms; Reset restores the overview. The original office story, invoice, assistant, audio, game clock and outcomes are integrated in V2.2. The overworld humanoid remains a temporary courier, not final Cooper art. Physical iPhone Safari testing remains outstanding; phone validation uses Chromium with touch input.
