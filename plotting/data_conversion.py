import numpy as np

__author__ = 'peter'


def memoize(fcn):

    lookup = {}

    def memoization_wrapper(*args):
        if args in lookup:
            return lookup[args]
        else:
            out = fcn(*args)
            lookup[args]=out
            return out

    return memoization_wrapper


def vector_length_to_tile_dims(vector_length):
    """
    You have vector_length tiles to put in a 2-D grid.  Find the size
    of the grid that best matches the desired aspect ratio.

    TODO: Actually do this with aspect ratio

    :param vector_length:
    :param desired_aspect_ratio:
    :return: n_rows, n_cols
    """
    n_cols = np.ceil(np.sqrt(vector_length))
    n_rows = np.ceil(vector_length/n_cols)
    grid_shape = int(n_rows), int(n_cols)
    return grid_shape


@memoize
def _data_shape_and_boundary_width_to_grid_slices(shape, grid_shape, boundary_width):

    assert len(shape) in (3, 4) or len(shape)==5 and shape[-1]==3
    is_colour = shape[-1]==3
    size_y, size_x = (shape[-3], shape[-2]) if is_colour else (shape[-2], shape[-1])
    is_vector = (len(shape)==4 and is_colour) or (len(shape)==3 and not is_colour)

    if grid_shape is None:
        grid_shape = vector_length_to_tile_dims(shape[0]) if is_vector else shape[:2]
    n_rows, n_cols = grid_shape

    output_shape = n_rows*(size_y+boundary_width)+1, n_cols*(size_x+boundary_width)+1
    index_pairs = []
    for i in xrange(n_rows):
        for j in xrange(n_cols):
            if is_vector:
                pull_indices = (i*n_cols + j, )
                if pull_indices[0] == shape[0]:
                    break
            else:
                pull_indices = (i, j)
            if not is_colour:
                pull_indices+=(slice(None), slice(None), np.newaxis, )
            start_row, start_col = i*(size_y+1)+1, j*(size_x+1)+1
            push_indices = slice(start_row, start_row+size_y), slice(start_col, start_col+size_x)
            index_pairs.append((pull_indices, push_indices))
    return output_shape, index_pairs


def put_data_in_grid(data, grid_shape = None, fill_colour = np.array((0, 0, 128), dtype = 'uint8'), boundary_width = 1):
    """
    Given a 3-d or 4-D array, put it in a 2-d grid.
    :param data: A 4-D array of any data type
    :return: A 3-D uint8 array of shape (n_rows, n_cols, 3)
    """
    shp = data.shape
    output_shape, slice_pairs = _data_shape_and_boundary_width_to_grid_slices(data.shape, grid_shape, boundary_width)
    output_data = np.empty(output_shape+(3, ), dtype='uint8')
    output_data[..., :] = fill_colour  # Maybe more efficient just to set the spaces.
    scaled_data = scale_data_to_8_bit(data)
    for pull_slice, push_slice in slice_pairs:
        output_data[push_slice] = scaled_data[pull_slice]
    return output_data


def scale_data_to_8_bit(data):
    """
    Scale data to range [0, 255]
    """
    min_data = np.min(data)
    scale = 255./(np.max(data)-min_data)
    return (data-min_data)*scale


class RecordBuffer(object):

    def __init__(self, buffer_len):
        self._buffer_len = buffer_len
        self._buffer = None
        self._ix = 0
        self._base_indices = np.arange(buffer_len)

    def __call__(self, data):
        if self._buffer is None:
            shape = () if np.isscalar(data) else data.shape
            self._buffer = np.zeros((self._buffer_len, )+shape)+np.nan
        self._buffer[self._ix] = data
        self._ix = (self._ix+1) % self._buffer_len
        return self._buffer[(self._base_indices+self._ix) % self._buffer_len]