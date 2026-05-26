# protocol/reader.py
# Data reading utilities for PLDM protocol blocks
from functools import lru_cache
from core.config import get_value_from_ini, INI_TYPE2
from core.utils import get_data_from_lst
from core.types import hex_to_type


@lru_cache(maxsize=128)
def _parse_field_spec(ini_file, section, key_name):
	"""Parse 'index;length' from ini into (index, length) tuple, cached"""
	ini_value = get_value_from_ini(ini_file, section, key_name)
	if ini_value is None:
		return None
	parts = ini_value.split(';')
	return (int(parts[0]), int(parts[1]))


def is_request_block(block, expected_len, trailer_len=0):
	"""Check if block is a request message by length and optional trailer pattern.
	
	Args:
		block: The data block to check
		expected_len: Expected total length of the block
		trailer_len: Number of trailing bytes that should be zero (0 = no check)
	"""
	if len(block) != expected_len:
		return False
	if trailer_len > 0:
		return block[-trailer_len:] == ["00"] * trailer_len
	return True


def get_multi_data_from_block(block, ini_file, section, key_name):
	val = ""
	spec = _parse_field_spec(ini_file, section, key_name)
	if spec is None:
		return ""
	idx, length = spec

	for i in range(length):
		data = get_data_from_lst(block, idx)
		if data is None:
			break
		val = val + data
		idx = idx + 1
	return val
	

def get_multi_keys_data_from_block(block, ini_file, section, key_name_list):
	reading_info = {}
	for key_name in key_name_list:
		reading_info[key_name] = get_multi_data_from_block(block, ini_file, section, key_name)
	if len(key_name_list) == 1:
		return reading_info[key_name]
	else:
		return reading_info
	

def get_values_according_to_keys(block, ini_file, section, keys):
	reading_info = {}
	for item in keys:
		val = get_multi_data_from_block(block, ini_file, section, item)
		reading_info[item] = get_value_from_ini(ini_file, item.upper(), val)
	if len(keys) == 1:
		return reading_info[item]
	else:
		return reading_info


def get_present_reading(block, section, sensor_data_size):
	present_reading_length = get_value_from_ini(INI_TYPE2, "PRESENT_READING_LENGTH", sensor_data_size)
	if present_reading_length is None:
		return {"hex": "", "dec": 0}
	present_reading = ""
	base_idx_str = get_value_from_ini(INI_TYPE2, section, "present_reading")
	if base_idx_str is None:
		return {"hex": "", "dec": 0}
	base_idx = int(base_idx_str)
	for length in range(int(present_reading_length)-1, -1, -1):
		data = get_data_from_lst(block, base_idx + length)
		if data is None:
			break
		present_reading += data
	try:
		dec_val = hex_to_type(present_reading, sensor_data_size) if present_reading else 0
	except (ValueError, TypeError):
		dec_val = 0
	return {
		"hex": present_reading,
		"dec": dec_val
	}
