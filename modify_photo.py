import constants
import random
import ssl
import os
from PIL import Image
from urllib.request import urlopen


def paste_random_image_from_directory(image_to_paste_on: "Image.Image",
                                      path_of_directory_to_choose_from: "str",
                                      x_and_y_where_to_start_pasting: "tuple",
                                      pasted_image_size: "tuple" = None,
                                      keep_aspect_ratio: "bool" = False) -> None:
    """
    Randomly chooses a file(only .png, .jpg, .jpeg, .svg, .PSD, .gif extensions are available) in a given
    directory. Resizes the chosen image to :param pasted_image_size keeping or not the aspect ratio according to
    the input (:param keep_aspect_ratio). Then pastes this image on :param image_to_paste_on at
    :param x_and_y_where_to_start_pasting coordinates (x_start, y_start, x_start + width, y_start + height)

    :param image_to_paste_on: !Pillow.Image Pillow Image class object! the image on which the chosen image will be
    pasted
    :param path_of_directory_to_choose_from: the path to the directory from which the pasted image will be
    randomly chosen. The image is chosen among other images that are present in this directory and which have
    .png, .jpg, .jpeg, .svg, .PSD or .gif extension
    :param x_and_y_where_to_start_pasting: coordinates of start points of pasted image on :param
    image_to_paste_on. Basically, it's coordinates of the top left corner of the pasted image
    :param pasted_image_size: resizes the pasted image to this size.
    :param keep_aspect_ratio:  keep or not the aspect ration while resizing the pasted image
    :returns None
    :raises TypeError: if :param image_to_paste_on is not object of Pillow Image class
    :raises ValueError: if the directory from which the pasted image will be randomly chosen is empty (or
    """
    if not isinstance(image_to_paste_on, Image.Image):
        raise TypeError("The image must be the Pillow Image class object")
    files_to_choose_from = [name for name in os.listdir(path_of_directory_to_choose_from) if
                            os.path.isfile(os.path.join(path_of_directory_to_choose_from, name))
                            and os.path.splitext(name)[1] in (".png", ".jpg", ".jpeg", ".svg", ".PSD", ".gif")]
    if not files_to_choose_from:
        raise ValueError("The directory from which the pasted image will be randomly chosen is empty or files in "
                         "it does not have appropriate extensions (.png, .jpg, .jpeg, .svg, .PSD, .gif)")
    random_file_number = random.randint(1, len(files_to_choose_from))
    pasted_image_file_path = os.path.join(path_of_directory_to_choose_from,
                                          (files_to_choose_from[random_file_number - 1]))
    pasted_image = Image.open(pasted_image_file_path).convert("RGBA")
    if pasted_image_size:
        if keep_aspect_ratio:
            pasted_image.thumbnail(pasted_image_size, Image.ANTIALIAS)
        else:
            pasted_image = pasted_image.resize(pasted_image_size, Image.ANTIALIAS)
    width_pasted_image, height_pasted_image = pasted_image.size
    x_to_start, y_to_start = x_and_y_where_to_start_pasting
    paste_area = (x_to_start, y_to_start, x_to_start + width_pasted_image, y_to_start + height_pasted_image)
    image_to_paste_on.paste(pasted_image, paste_area, pasted_image)


def modify_photo(photo, save_path: "str"):
    """"
    Edits the given :param photo adding additional png images and saves it at the given :param save_path

    :param photo: TeleBot File object containing TeleBot UserProfilePhoto
    :param save_path: determines the place to save the result file
    :returns None
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # - Open photo to edit ----------------------------------------------------------------------
    file_url = "https://api.telegram.org/file/bot{}/{}".format(constants.bot_token, photo.file_path)
    image = Image.open(urlopen(file_url, context=ssl.SSLContext())).convert("RGBA")
    # - Add image to the upper part of the photo ------------------------------------------------
    path = os.path.join(script_directory, "Upper")
    paste_random_image_from_directory(image, path, (0, 0), (640, 640), True)
    # - Add image to the central part of the photo ----------------------------------------------
    path = os.path.join(script_directory, "HappyBirthday")
    paste_random_image_from_directory(image, path, (170, 350), (300, 300), True)
    # - Add image to the bottom right part of the photo -----------------------------------------
    path = os.path.join(script_directory, "Cake")
    paste_random_image_from_directory(image, path, (450, 380), (300, 300), True)
    # - Add image to the bottom left part of the photo ------------------------------------------
    path = os.path.join(script_directory, "Present")
    paste_random_image_from_directory(image, path, (-35, 390), (300, 300), True)
    # - Saves modified image --------------------------------------------------------------------
    # image.show()
    image = image.convert("RGB")
    image.save(save_path, "JPEG", quality=90)
