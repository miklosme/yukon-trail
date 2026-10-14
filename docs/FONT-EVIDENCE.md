# Original font evidence

Observed2026-10-13: the supplied Windows font is TrueType, not a missing raster
font requiring reconstruction. `YUF_____.TTF`,24,236bytes, SHA-256
`6a2c8f3356a9affef9711a14070b5de1cac95c320799360d10c78d8df40f4f18`.
Its SFNT naming records agree across Unicode/Mac/Windows entries: family/full
name `Yukon Font`, style `Regular`, PostScript name `YukonFont`.
The verified executable contains `Yukon Font` at file`0x50202`, NE data13:`0de2`
(Ghidra`1060:0de2`). This is a resource/use lead; font construction, point size,
style, layout and original glyph rasterization remain to be traced/compared.

Read the actual directory/name fields with:

```sh
python3 tools/inspect_yukon_font.py original/extracted/windows/YUF_____.TTF
```

The inventory verifies the exact source hash and table/string bounds, and fails
on unsupported selected naming encodings. It does not decode glyphs, verify
SFNT table checksums or test font loading. Metadata with exact table/string
locations is in [font-source-evidence.json](font-source-evidence.json).
The format interpretation follows Microsoft's primary
[SFNT directory specification](https://learn.microsoft.com/en-us/typography/opentype/spec/otff)
and [naming-table specification](https://learn.microsoft.com/en-us/typography/opentype/spec/name).
No font conversion/dependency was installed. Keep the original font and any
browser copies in ignored local asset directories. Using this source font in
canvas is an implementation candidate; browser/native pixel fidelity is unknown.
