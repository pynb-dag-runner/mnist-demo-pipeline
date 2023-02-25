from common.utils import chunkify, make_panel_image

# -
import numpy as np


def test_chunkify_list():
    assert list(chunkify([1, 2, 3], 1)) == [[1], [2], [3]]
    assert list(chunkify([1, 2, 3], 2)) == [[1, 2], [3]]
    assert list(chunkify([1, 2, 3], 3)) == [[1, 2, 3]]
    assert list(chunkify([1, 2, 3], 4)) == [[1, 2, 3]]


def test_chunkify_numpy():
    def get_3x4(start_int: int):
        return (np.arange(12) + start_int).reshape(3, 4)

    N = 100
    xs = np.array([get_3x4(k) for k in range(N)])
    assert xs.shape == (N, 3, 4)

    def assert_list_of_arrs_eq(list_of_np_arr1, list_of_np_arr2):
        assert len(list_of_np_arr1) == len(list_of_np_arr2)

        for arr1, arr2 in zip(list_of_np_arr1, list_of_np_arr2):
            assert arr1.shape == arr2.shape
            assert np.allclose(arr1, arr2)

    for xs_chunks in [
        [xs[k].reshape(1, 3, 4) for k in range(N)],
        [np.array([get_3x4(k)]) for k in range(N)],
    ]:
        assert_list_of_arrs_eq(list(chunkify(xs, chunk_size=1)), xs_chunks)

    for xs_chunks in [
        [xs[: (N - 1)], xs[(N - 1) :]],
        [np.array([get_3x4(k) for k in range(N - 1)]), np.array([get_3x4(N - 1)])],
    ]:
        assert_list_of_arrs_eq(list(chunkify(xs, chunk_size=N - 1)), xs_chunks)

    assert_list_of_arrs_eq(list(chunkify(xs, chunk_size=N + 1)), [xs])


def test_make_panel_image():
    def get_2x3(start_int: int):
        return (np.arange(6) + start_int).reshape(2, 3)

    N_images = 5
    xs = np.array([get_2x3(k) for k in range(N_images)])
    assert xs.shape == (N_images, 2, 3)

    def get_panel_arr(images_per_row: int, pad_width: int, background_fill: int):
        return (
            make_panel_image(
                xs,
                pad_width=pad_width,
                background_fill=background_fill,
                images_per_row=images_per_row,
            )
            .astype("int")
            .tolist()
        )

    for b in range(3):
        assert get_panel_arr(images_per_row=2, pad_width=0, background_fill=b) == [
            [0, 1, 2, 1, 2, 3],
            [3, 4, 5, 4, 5, 6],
            [2, 3, 4, 3, 4, 5],
            [5, 6, 7, 6, 7, 8],
            [4, 5, 6, b, b, b],
            [7, 8, 9, b, b, b],
        ]

        assert get_panel_arr(images_per_row=3, pad_width=1, background_fill=b) == [
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, 0, 1, 2, b, b, 1, 2, 3, b, b, 2, 3, 4, b],
            [b, 3, 4, 5, b, b, 4, 5, 6, b, b, 5, 6, 7, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, 3, 4, 5, b, b, 4, 5, 6, b, b, b, b, b, b],
            [b, 6, 7, 8, b, b, 7, 8, 9, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b, b],
        ]

        assert get_panel_arr(images_per_row=2, pad_width=1, background_fill=b) == [
            [b, b, b, b, b, b, b, b, b, b],
            [b, 0, 1, 2, b, b, 1, 2, 3, b],
            [b, 3, 4, 5, b, b, 4, 5, 6, b],
            [b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b],
            [b, 2, 3, 4, b, b, 3, 4, 5, b],
            [b, 5, 6, 7, b, b, 6, 7, 8, b],
            [b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b],
            [b, 4, 5, 6, b, b, b, b, b, b],
            [b, 7, 8, 9, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b],
        ]

        assert get_panel_arr(images_per_row=2, pad_width=2, background_fill=b) == [
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, 0, 1, 2, b, b, b, b, 1, 2, 3, b, b],
            [b, b, 3, 4, 5, b, b, b, b, 4, 5, 6, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, 2, 3, 4, b, b, b, b, 3, 4, 5, b, b],
            [b, b, 5, 6, 7, b, b, b, b, 6, 7, 8, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, 4, 5, 6, b, b, b, b, b, b, b, b, b],
            [b, b, 7, 8, 9, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
            [b, b, b, b, b, b, b, b, b, b, b, b, b, b],
        ]
