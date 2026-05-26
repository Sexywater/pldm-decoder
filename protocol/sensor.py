# protocol/sensor.py
# Sensor ID extraction from PLDM type 2 blocks
from core.config import get_value_from_ini, INI_TYPE2
from core.utils import get_data_from_lst
from parser.vdm_header import extract_vdm_header


# extracts a sensor ID from a log block at the index specified in the ini file,
# based on the command code of PLDM type 2 messages.
def get_sensor_id(block):
	vdm_header = extract_vdm_header(block)
	if vdm_header is None or vdm_header["pldm_type_code"] != "02":
		return None
	
	command_section_map = {
		"0A": "SENSOR_EVENT",
		"11": "GET_SENSOR_READING_REQUEST",
		"21": "GET_STATE_SENSOR_READINGS_REQUEST",
		"51": "NUMERIC_SENSOR_PDR",
	}
	section = command_section_map.get(vdm_header["pldm_command_code"])
	if section is None:
		return None
	
	sensor_id_idx = get_value_from_ini(INI_TYPE2, section, "sensor_id").split(';')[0]
	sensor_id_length = get_value_from_ini(INI_TYPE2, section, "sensor_id").split(';')[1]
	if get_data_from_lst(block, int(sensor_id_idx) + 1) == "00":
		return get_data_from_lst(block, sensor_id_idx)  # single byte
	else:
		return get_data_from_lst(block, int(sensor_id_idx) + 1) + get_data_from_lst(block, sensor_id_idx)  # double byte
