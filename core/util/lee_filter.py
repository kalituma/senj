from scipy.ndimage import uniform_filter, variance

def apply_lee_filter(bands:dict, size:int):
    """
    Apply Lee filter to reduce speckle noise.

    Parameters:
        bands (dict): Input bands data.
        size (int): Size of the window filter.

    Returns:
        dict: Filtered bands.
    """
    for key, value in bands.items():
        band = value['value']
        value['value'] = lee_filter(band, size)
    return bands

def lee_filter(img, size):
    # added from original preprocessing code
    """
    Apply Lee filter to reduce speckle noise.

    Parameters:
        img (np.array): Input image data.
        size (int): Size of the window filter.

    Returns:
        np.array: Filtered image.
    """
    img_mean = uniform_filter(img, size)
    img_sqr_mean = uniform_filter(img ** 2, size)
    img_variance = img_sqr_mean - img_mean ** 2

    overall_variance = variance(img)

    # Calculate the weights for the filter
    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)

    return img_output