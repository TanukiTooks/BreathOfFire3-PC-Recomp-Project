# Xbox button prompt artwork

Source supplied by the user: https://www.figma.com/community/file/1271153059120916114/xbox-controller-icons-free

The user supplied Frame 13.png through Frame 18.png as transparent PNG exports. These six originals are retained unchanged. Individual icons are in icons/; manifest.json records every source rectangle, source/output hash, face-button style, and physical SDL input mapping. preview.html displays all 39 icons at several sizes. Author/license metadata was not included with the PNGs; the source URL is retained for attribution research.

Re-import from the workspace root with BoF3 Research/scripts/import_xbox_prompt_icons.py. It verifies that the extracted icons reconstruct each original sheet exactly, including RGBA values and transparency. The default manifest face-button style is color; solid and outline variants are also available.

The playable PSXRecomp build now uses these assets for verified common-font button glyphs. Runtime lookup resolves the current routed controller and its effective mapping, including per-device overrides, before selecting a physical Xbox icon. Keyboard keycaps are drawn separately; PlayStation and unidentified controller families retain original art. The six original PNG sheets and all extracted PNGs remain unchanged. Runtime RGB555 conversion and native-size screenshots are documented in BoF3 Research/coverage/button-prompts/README.md.
