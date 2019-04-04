from xmlparser import count_hdr_lines
import pytest


def test_count_hdr_lines():
    file_path = 'C:\\Users\mural\PycharmProjects\dbGaPDataDictionaryParser\sample_hasheader.txt'
    test_1 = count_hdr_lines(file_path, colname=['DOCFILE'])
    test_2 = count_hdr_lines(file_path, colname=['DOCFILE', 'MIN'])
    test_3 = count_hdr_lines(file_path)
    assert (test_1, test_2, test_3) == (3, 3, 3)