# handlers/get_state_sensor_readings.py
from core.config import get_value_from_ini, INI_TYPE2, INI_NIC_SENSOR
from core.utils import get_data_from_lst
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block, is_request_block
from protocol.sensor import get_sensor_id
from protocol.payload import new_payload


# Process the payload content related to get state sensor reading of PLDM type 2 PlatformEventMsg
def process_getstatesensorreadings_payload(block):
	vdm_payload = new_payload()
	# If the block length is 25 and the last two data entries are both "00", determine whether it is a request.
	if is_request_block(block, 25, 2):
		sensor_id = get_sensor_id(block)
		if sensor_id is None:
			return vdm_payload
		sensor_func = get_value_from_ini(INI_NIC_SENSOR, "SENSOR_LIST", sensor_id)
		vdm_payload["output"].append(f"Request sensor id {sensor_id} value means request {sensor_func}")
	
		return vdm_payload
		
	keys = ["completion_code", "sensor_operational_state"]
	values_from_the_keys = get_values_according_to_keys(block, INI_TYPE2, "GET_STATE_SENSOR_READINGS_RESPONSE", keys)
	composite_sensor_count = int(get_multi_data_from_block(block, INI_TYPE2, "GET_STATE_SENSOR_READINGS_RESPONSE", "composite_sensor_count"))
	
	present_state_idx = get_value_from_ini(INI_TYPE2, "GET_STATE_SENSOR_READINGS_RESPONSE", "present_state").split(';')[0]
	previous_state_idx = get_value_from_ini(INI_TYPE2, "GET_STATE_SENSOR_READINGS_RESPONSE", "previous_state").split(';')[0]
	event_state_idx = get_value_from_ini(INI_TYPE2, "GET_STATE_SENSOR_READINGS_RESPONSE", "event_state").split(';')[0]
	
	if composite_sensor_count == 2:
		state_sections = ["LINK_STATE", "LEASH_STATUS"]
		for count in range(composite_sensor_count):
			section = state_sections[count]
			
			present_state = get_data_from_lst(block, present_state_idx)
			present_state_meaning = get_value_from_ini(INI_NIC_SENSOR, section, present_state)
			present_state_idx = int(present_state_idx) + 4
		
			previous_state = get_data_from_lst(block, previous_state_idx)
			previous_state_meaning = get_value_from_ini(INI_NIC_SENSOR, section, previous_state)
			previous_state_idx = int(previous_state_idx) + 4
	
			event_state = get_data_from_lst(block, event_state_idx)
			event_state_meaning = get_value_from_ini(INI_TYPE2, "EVENT_STATE", event_state)
			event_state_idx = int(event_state_idx) + 4
		
			vdm_payload["output"].append(f"Composite sensor NO.{count+1} value change from {previous_state} to {present_state} means change from {previous_state_meaning} to {present_state_meaning}")
			vdm_payload["verbose"].append(f"completion_code = {values_from_the_keys['completion_code']}, composite_sensor_count = {composite_sensor_count}, sensor_operational_state = {values_from_the_keys['sensor_operational_state']}，present_state = {present_state}, present_state_meaning = {present_state_meaning}, previous_state = {previous_state}, previous_state_meaning = {previous_state_meaning},  event_state = {event_state}, event_state_meaning = {event_state_meaning}")

		return vdm_payload
