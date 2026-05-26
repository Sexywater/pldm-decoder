# handlers/get_sensor_reading.py
from core.config import get_value_from_ini, INI_TYPE2, INI_NIC_SENSOR
from protocol.reader import get_values_according_to_keys, get_present_reading
from protocol.sensor import get_sensor_id
from protocol.payload import new_payload


# Process the payload content related to get sensor reading of PLDM type 2 PlatformEventMsg
def process_getsensorreading_payload(block):
	vdm_payload = new_payload()
	# If the block length is 25 and the last two data entries are both "00", determine whether it is a request.
	if len(block) == 25 and block[-2:] == ["00", "00"]:
		sensor_id = get_sensor_id(block)
		if sensor_id is None:
			return vdm_payload
		sensor_func = get_value_from_ini(INI_NIC_SENSOR, "SENSOR_LIST", sensor_id)
		vdm_payload["output"].append(f"Request sensor id {sensor_id} value means request {sensor_func}")
		return vdm_payload
	# process respond msg
	keys = ["completion_code", "sensor_data_size", "sensor_operational_state", 
			"sensor_event_message_enable", "present_state", "previous_state", "event_state"]
	values_from_the_keys = get_values_according_to_keys(block, INI_TYPE2, "GET_SENSOR_READING_RESPOND", keys)
	present_reading = get_present_reading(block, "GET_SENSOR_READING_RESPOND", values_from_the_keys["sensor_data_size"])
	
	vdm_payload["output"].append(f"present reading is hex data {present_reading['hex']} (dec data {present_reading['dec']})")
	vdm_payload["verbose"].append(f"completion_code = {values_from_the_keys['completion_code']}, sensor_data_size = {values_from_the_keys['sensor_data_size']}, sensor_operational_state = {values_from_the_keys['sensor_operational_state']}, sensor_event_message_enable = {values_from_the_keys['sensor_event_message_enable']},present_state = {values_from_the_keys['present_state']}, previous_state = {values_from_the_keys['previous_state']}, event_state = {values_from_the_keys['event_state']}, present_reading = {present_reading}")

	return vdm_payload
