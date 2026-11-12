"""Render every report page plus contact sheets, using optional PyMuPDF/Pillow."""

import argparse
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def contact_sheet(paths, target, columns=3, thumb=(400, 570)):
    tiles = []
    for path in paths:
        im = Image.open(path).convert("RGB")
        im.thumbnail(thumb)
        tile = Image.new("RGB", (thumb[0] + 20, thumb[1] + 35), "#e3e8ef")
        tile.paste(im, ((tile.width - im.width) // 2, 20))
        ImageDraw.Draw(tile).text((10, thumb[1] + 20), path.stem, fill="black")
        tiles.append(tile)
    if not tiles:
        return
    rows = (len(tiles) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * tiles[0].width, rows * tiles[0].height), "white")
    for i, tile in enumerate(tiles):
        canvas.paste(tile, ((i % columns) * tile.width, (i // columns) * tile.height))
    canvas.save(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    source = args.run_dir.resolve()
    out = source.parent / "validation" / source.name / "reports"
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted((source / "reports").glob("*.pdf")):
        images = []
        with fitz.open(path) as pdf:
            for i, page in enumerate(pdf):
                png = out / f"{path.stem}_{i + 1:02d}.png"
                page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(png)
                images.append(png)
        contact_sheet(images, out / f"{path.stem}_contact.png")
    print(out)


if __name__ == "__main__":
    main()
