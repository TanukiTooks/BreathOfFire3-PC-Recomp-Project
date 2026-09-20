# Breath of Fire III PC Recomp Project

This repository is a public working snapshot of an experimental PC recompilation project for the PlayStation version of *Breath of Fire III*.

The repo contains project configuration, host-side native helper code, research notes, and tooling used while investigating runtime behaviour and native replacements. It intentionally does not contain the game, PlayStation BIOS files, disc images, generated translated game code, memory-card data, screenshots, VRAM/RAM dumps, or other extracted game assets.

## Current Status

This is active research and development, not a finished release. The local working copy contains generated files and private test captures that are excluded from Git because they are either bulky, derived from runtime data, or not appropriate for a public repository.

Tracked here:

- PSXRecomp project configuration for the Breath of Fire III work area.
- Native host/helper code written for the project.
- Research scripts used for probing, measuring, and validating behaviour.
- Human-readable research notes and roadmaps.

Not tracked here:

- Breath of Fire III disc data or ripped assets.
- PlayStation BIOS dumps.
- Generated recompiler output from original game code.
- Build products, logs, RAM/VRAM captures, screenshots, and local runtime state.

## Legal

You must own your own legal copy of *Breath of Fire III* to experiment with this project locally. This repository is not affiliated with, endorsed by, or sponsored by Capcom, Sony, or any related rights holder.

*Breath of Fire* is a trademark of Capcom Co., Ltd. PlayStation is a trademark of Sony Interactive Entertainment Inc.

## AI Assistance

This project has been developed with AI-assisted research and coding. Changes are still expected to be verified against actual runtime behaviour, traces, or focused tests before being treated as reliable.