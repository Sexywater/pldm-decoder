# handlers/get_pdr.py
import re
from core.config import INI_TYPE2, get_value_from_ini
from core.utils import get_multi_data_from_lst
from core.types import to_decimal, parse_range_filed_support, parse_support_thresholds
from protocol.reader import get_values_according_to_keys, get_multi_keys_data_from_block, is_request_block
from protocol.sensor import get_sensor_id
from protocol.payload import new_payload


def _parse_terminus_locator_pdr(block, vdm_payload):
	"""Parse terminus locator PDR response"""
	keys = ["pldm_terminus_handle", "tid", "container_id", "terminus_locator_value_size"]
	datas = get_multi_keys_data_from_block(block, INI_TYPE2, "TERMINUS_LOCATOR_PDR", keys)
	
	keys = ["validity", "terminus_locator_type"]
	values = get_values_according_to_keys(block, INI_TYPE2, "TERMINUS_LOCATOR_PDR", keys)
	
	vdm_payload["output"].append(f"validity : {values['validity']} , terminus_locator_type : {values['terminus_locator_type']}")
	vdm_payload["verbose"].append(f"pldm_terminus_handle : {datas['pldm_terminus_handle']} , tid : {datas['tid']} , container_id : {datas['container_id']} , terminus_locator_value_size : {datas['terminus_locator_value_size']}")
	
	if values['terminus_locator_type'] == "uid":
		terminus_instance = get_multi_keys_data_from_block(block, INI_TYPE2, "UID", ['terminus_instance'])
		device_uid = ' '.join(block[52:])
		
		vdm_payload["output"].append(f"device_uid : {device_uid}")
		vdm_payload["verbose"].append(f"terminus_instance : {terminus_instance}")


def _parse_numeric_sensor_pdr(block, vdm_payload):
	"""Parse numeric sensor PDR response"""
	keys = ["sensor_init", "sensor_auxiliary_name_pdr", "base_unit", "rate_unit", "rel", "is_linear", "sensor_data_size"]
	values = get_values_according_to_keys(block, INI_TYPE2, "NUMERIC_SENSOR_PDR", keys)
	
	keys = ["pldm_terminus_handle", "entity_type", "entity_instance_number", "container_id", "unit_modifier", "resolution", "offset", "accuracy", "plus_tolerance", "minus_tolerance", "hysteresis", "support_thresholds", "threshold_and_hysteresis_volatility", "state_transition_interval", "update_interval"]
	datas = get_multi_keys_data_from_block(block, INI_TYPE2, "NUMERIC_SENSOR_PDR", keys)
	sensor_id = get_sensor_id(block)
	support_thresholds = parse_support_thresholds(bin(int(datas['support_thresholds'], 16))[2:])
	
	vdm_payload["output"].append(f"sensor_id : {sensor_id} , sensor_init : {values['sensor_init']} , sensor_auxiliary_name_pdr : {values['sensor_auxiliary_name_pdr']} , base_unit : {values['base_unit']} , rate_unit : {values['rate_unit']} , is_linear : {values['is_linear']} , sensor_data_size : {values['sensor_data_size']} , resolution : {datas['resolution']} , support_thresholds : {support_thresholds}")
	vdm_payload["verbose"].append(
		f"pldm_terminus_handle : {datas['pldm_terminus_handle']} , entity_type : {datas['entity_type']} , entity_instance_number : {datas['entity_instance_number']} , container_id : {datas['container_id']} , unit_modifier : {datas['unit_modifier']} , offset : {datas['offset']} , accuracy : {datas['accuracy']} , plus_tolerance : {datas['plus_tolerance']} , minus_tolerance : {datas['minus_tolerance']} , "
		f"hysteresis : {datas['hysteresis']} , threshold_and_hysteresis_volatility : {datas['threshold_and_hysteresis_volatility']} , state_transition_interval : {datas['state_transition_interval']} , update_interval: {datas['update_interval']} ,"
	)
	
	sensor_data_size_bits = int(re.search(r'\d+', values['sensor_data_size']).group())
	sensor_data_size_bytes = sensor_data_size_bits // 8
	
	# Calculate range field area start offset: after update_interval
	update_interval_cfg = get_value_from_ini(INI_TYPE2, "NUMERIC_SENSOR_PDR", "update_interval")
	ui_offset, ui_length = (int(x) for x in update_interval_cfg.split(';'))
	range_base = ui_offset + ui_length
	
	# max_readable / min_readable each occupy sensor_data_size_bytes
	max_readable = to_decimal(get_multi_data_from_lst(block, range_base, sensor_data_size_bytes))
	min_readable = to_decimal(get_multi_data_from_lst(block, range_base + sensor_data_size_bytes, sensor_data_size_bytes))
	
	# range_field_format (1 byte) and range_field_support (1 byte)
	range_field_format = get_multi_data_from_lst(block, range_base + sensor_data_size_bytes * 2, 1)
	field_format = int(range_field_format) if range_field_format else 0
	range_field_support = get_multi_data_from_lst(block, range_base + sensor_data_size_bytes * 2 + 1, 1)
	range_field_support = parse_range_filed_support(bin(int(range_field_support, 16))[2:])
	
	# 9 range field values, each occupies field_format bytes
	field_names = [
		"nominal_value", "normal_max", "normal_min",
		"warning_high", "warning_low", "critical_high",
		"critical_low", "fatal_high", "fatal_low"
	]
	field_start = range_base + sensor_data_size_bytes * 2 + 2
	field_values = {}
	for i, name in enumerate(field_names):
		field_values[name] = to_decimal(
			get_multi_data_from_lst(block, field_start + field_format * i, field_format)
		)
	
	vdm_payload["verbose"].append(
		f"max_readable : {max_readable} , min_readable : {min_readable} , "
		f"range_field_format : {range_field_format} , range_field_support : {range_field_support} , "
		f"nominal_value : {field_values['nominal_value']} , normal_max : {field_values['normal_max']} , "
		f"normal_min : {field_values['normal_min']} , warning_high : {field_values['warning_high']} , "
		f"warning_low : {field_values['warning_low']} , critical_high : {field_values['critical_high']} , "
		f"critical_low : {field_values['critical_low']} , fatal_high : {field_values['fatal_high']} , "
		f"fatal_low : {field_values['fatal_low']} "
	)


def _parse_state_sensor_pdr(block, vdm_payload):
	"""Parse state sensor PDR response"""
	keys = ["sensor_init", "sensor_auxiliary_name_pdr"]
	values = get_values_according_to_keys(block, INI_TYPE2, "STATE_SENSOR_PDR", keys)
	
	keys = ["pldm_terminus_handle", "entity_type", "entity_instance_number", "container_id", "composite_sensor_count", "state_set_id", "possible_states_size"]
	datas = get_multi_keys_data_from_block(block, INI_TYPE2, "STATE_SENSOR_PDR", keys)
	sensor_id = get_sensor_id(block)
	
	vdm_payload["output"].append(f"sensor_id : {sensor_id} , sensor_init : {values['sensor_init']} , sensor_auxiliary_name_pdr : {values['sensor_auxiliary_name_pdr']} , composite_sensor_count : {datas['composite_sensor_count']} ,  state_set_id : {datas['state_set_id']} , possible_states_size : {datas['possible_states_size']}")
	vdm_payload["verbose"].append(f"pldm_terminus_handle : {datas['pldm_terminus_handle']} , entity_type : {datas['entity_type']} , entity_instance_number : {datas['entity_instance_number']} , container_id : {datas['container_id']}")


def process_get_pdr_payload(block):
	vdm_payload = new_payload()
	
	if is_request_block(block, 37, 3):
		keys = ["record_handle", "data_transfer_handle", "request_count", "record_change_number"]
		datas = get_multi_keys_data_from_block(block, INI_TYPE2, "GET_PDR_REQUEST", keys)
		
		transfer_operation_flag = get_values_according_to_keys(block, INI_TYPE2, "GET_PDR_REQUEST", ["transfer_operation_flag"])
	
		vdm_payload["output"].append(f"record_handle : {datas['record_handle']} , data_transfer_handle : {datas['data_transfer_handle']} , transfer_operation_flag : {transfer_operation_flag} , request_count : {datas['request_count']} , record_change_number : {datas['record_change_number']}")
		return vdm_payload
		
	else:
		keys = ["get_pdr_completion_code", "transfer_flag"]
		values = get_values_according_to_keys(block, INI_TYPE2, "GET_PDR_RESPONSE", keys)		
		keys = ["next_record_handle", "next_data_transfer_handle", "response_count"] 
		datas = get_multi_keys_data_from_block(block, INI_TYPE2, "GET_PDR_RESPONSE", keys)
		
		vdm_payload["verbose"].append(f"get_pdr_completion_code : {values['get_pdr_completion_code']} , transfer_flag : {values['transfer_flag']} , next_record_handle : {datas['next_record_handle']} , next_data_transfer_handle : {datas['next_data_transfer_handle']} , response_count : {datas['response_count']}")

		pdr_type = get_values_according_to_keys(block, INI_TYPE2, "PDR_HEADER_FORMAT", ["pdr_type"])	
		keys = ["record_handle", "pdr_header_version", "record_change_number", "data_length"]
		datas = get_multi_keys_data_from_block(block, INI_TYPE2, "PDR_HEADER_FORMAT", keys)
		
		vdm_payload["output"].append(f"pdr_type : {pdr_type}")
		vdm_payload["verbose"].append(f"record_handle : {datas['record_handle']} , pdr_header_version : {datas['pdr_header_version']} , record_change_number : {datas['record_change_number']} , data_length : {datas['data_length']}")
		
		if pdr_type == "terminus locator pdr":
			_parse_terminus_locator_pdr(block, vdm_payload)
		elif pdr_type == "numeric sensor pdr":
			_parse_numeric_sensor_pdr(block, vdm_payload)
		elif pdr_type == "state sensor pdr":
			_parse_state_sensor_pdr(block, vdm_payload)
		
		return vdm_payload
