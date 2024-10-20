import pymupdf
from PIL import Image
from typing import List, Tuple


class ImageCropper:
    @staticmethod
    def pdf_to_image(pdf_file: str, page_num: int, dpi: int = 300) -> Image.Image:
        with pymupdf.open(pdf_file) as doc:
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    @staticmethod
    def normalize_coordinates(coordinates: List[dict], 
                              output_page_size: Tuple[int, int]) -> Tuple[float, float, float, float]:
        x_values, y_values = zip(*((coord["x"], coord["y"]) for coord in coordinates))
        x1, y1, x2, y2 = min(x_values), min(y_values), max(x_values), max(y_values)
        return (x1 / output_page_size[0], y1 / output_page_size[1],
                x2 / output_page_size[0], y2 / output_page_size[1])

    @staticmethod
    def crop_image(img: Image.Image, 
                   coordinates: Tuple[float, float, float, float],
                   output_file: str) -> None:
        img_width, img_height = img.size
        x1, y1, x2, y2 = (int(coord * dim) for coord, dim in zip(coordinates, (img_width, img_height) * 2))
        img.crop((x1, y1, x2, y2)).save(output_file)

    @classmethod
    def process_pdf_page(cls, 
                         pdf_file: str, 
                         page_num: int, 
                         coordinates: List[dict], 
                         page_size: Tuple[int, int],
                         output_file: str, 
                         dpi: int = 300) -> None:
        img = cls.pdf_to_image(pdf_file, page_num, dpi)
        norm_coords = cls.normalize_coordinates(coordinates, page_size)
        cls.crop_image(img, norm_coords, output_file)
