import numpy as np
from PIL import Image
import scipy.ndimage


def pre_process(img, options, check_channels=True):
    """Pre-processes images based on options generated from SMILER ParameterMap.

	Args:
	    img: A numpy array containing the input image.
        options: A dict generated by SMILER's ParameterMap.
        check_channels: if True, convert output to 3 channels.

	Returns:
        result: ndarray
	"""
    color_space = options.get('color_space', 'RGB')

    if not isinstance(img, np.ndarray):
        img = np.array(img, dtype=np.uint8)
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    if color_space not in ['default', 'RGB', 'gray', 'YCbCr', 'LAB', 'HSV']:
        raise ValueError(
            '{0} color space is not suppported'.format(color_space))

    if color_space == 'gray':
        color_space = 'L'

    if color_space != 'default':
        img = Image.fromarray(img).convert(color_space)
        img = np.array(img)

    if color_space == 'L':
        img = np.expand_dims(img, 2)  # adding third channel
        img = np.repeat(img, 3, axis=2)  # repeating values

    return img


def _gauss2d(shape=(3, 3), sigma=0.5):
    """
    2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])
    """
    m, n = [(ss - 1.) / 2. for ss in shape]
    y, x = np.ogrid[-m:m + 1, -n:n + 1]
    h = np.exp(-(x * x + y * y) / (2. * sigma * sigma))
    h[h < np.finfo(h.dtype).eps * h.max()] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh
    return h

def post_process(img, options):
    """Pre-processes images based on options generated from SMILER ParameterMap.

	Args:
        img: a numpy array containing the model output.
        options: A dict generated by SMILER's ParameterMap.

    Returns:
        result: numpy array
    """
    do_smoothing = options.get('do_smoothing', 'default')
    scale_output = options.get('scale_output', 'min-max')

    smooth_size = options.get('smooth_size', 9.0)
    smooth_std = options.get('smooth_std', 3.0)
    smooth_prop = options.get('smooth_prop', 0.05)

    scale_min = options.get('scale_min', 0.0)
    scale_max = options.get('scale_max', 1.0)

    if not isinstance(img, np.ndarray):
        img = np.array(img)

    if do_smoothing in ['custom', 'proportional']:
        if do_smoothing == 'custom':
            Filter = _gauss2d(
                shape=(smooth_size, smooth_size), sigma=smooth_std)
        elif do_smoothing == 'proportional':
            h, w = img.shape
            largest_size = h if h > w else w
            smooth_std = smooth_prop * largest_size
            smooth_size = int(3 * smooth_std)

            Filter = _gauss2d(
                shape=(smooth_size, smooth_size), sigma=smooth_std)

        img = scipy.ndimage.correlate(img, Filter, mode='reflect')

    if scale_output in ['min-max', 'normalized']:
        if scale_output == 'min-max':
            img = np.interp(img, (img.min(), img.max()),
                            (scale_min, scale_max))

        elif scale_output == 'normalized':
            img = (img - img.mean()) / img.std()

    return img
