# handlers/platform_event_msg.py
from core.config import get_value_from_ini, INI_TYPE2, INI_NIC_SENSOR
from protocol.reader import get_multi_data_from_block, get_values_according_to_keys, get_present_reading, is_request_block
from protocol.sensor import get_sensor_id
from protocol.payload import new_payload


def process_platformeventmsg_payload(block):
	vdm_payload = new_payload()
	# handle ACK info
	if is_request_block(block, 25, 4):
		vdm_payload["output"].append("send an ack message from BMC to device")
		return vdm_payload

	# extract basic info
	format_version = get_multi_data_from_block(block, INI_TYPE2, "PLATFORM_EVENT_MESSAGE", "format_version")
	tid = get_multi_data_from_block(block, INI_TYPE2, "PLATFORM_EVENT_MESSAGE", "tid")
	event_class = get_values_according_to_keys(block, INI_TYPE2, "PLATFORM_EVENT_MESSAGE", ["event_class"])
	sensor_id = get_sensor_id(block)
	if sensor_id is None:
		return vdm_payload
	sensor_func = get_value_from_ini(INI_NIC_SENSOR, "SENSOR_LIST", sensor_id)
	sensor_event_class = get_values_according_to_keys(block, INI_TYPE2, "SENSOR_EVENT", ["sensor_event_class"])

	# process state sensor data
	if sensor_event_class == "state_sensor_state":
		sensor_offset = get_multi_data_from_block(block, INI_TYPE2, "STATE_SENSOR_STATE", "sensor_offset")
		offset_section_map = {"00": "LINK_STATE", "01": "LEASH_STATUS"}
		state_section = offset_section_map.get(sensor_offset, "LINK_STATE")
		
		event_state_value = get_multi_data_from_block(block, INI_TYPE2, "STATE_SENSOR_STATE", "event_state")
		event_state = get_value_from_ini(INI_NIC_SENSOR, state_section, event_state_value)
		previous_event_state_value = get_multi_data_from_block(block, INI_TYPE2, "STATE_SENSOR_STATE", "previous_event_state")
		previous_event_state = get_value_from_ini(INI_NIC_SENSOR, state_section, previous_event_state_value)
			
		vdm_payload["output"].append(f"sensor id {sensor_id} offset {sensor_offset} change from {previous_event_state_value} to {event_state_value} means {sensor_func} change from {previous_event_state} to {event_state}")
		vdm_payload["verbose"].append(f"format_version: {format_version} , tid : {tid}, event_class : {event_class}, sensor_id : {sensor_id}, sensor_func = {sensor_func}, sensor_event_class = {sensor_event_class}, sensor_offset = {sensor_offset}, previous_event_state_value = {previous_event_state_value}, previous_event_state = {previous_event_state}, event_state_value = {event_state_value}, event_state = {event_state}")

	# process numeric sensor data
	elif sensor_event_class == "numeric_sensor_state":
		keys = ["event_state", "previous_event_state", "sensor_data_size"]
		values_from_the_keys = get_values_according_to_keys(block, INI_TYPE2, "NUMERIC_SENSOR_STATE", keys)
		present_reading = get_present_reading(block, "NUMERIC_SENSOR_STATE", values_from_the_keys["sensor_data_size"])
		
		vdm_payload["output"].append(f"{sensor_func} sensor (sensor id {sensor_id}) present reading is hex data {present_reading['hex']} (dec data {present_reading['dec']})")
		vdm_payload["verbose"].append(f"format_version : {format_version} , tid : {tid}, event_class : {event_class}, sensor_id : {sensor_id}, sensor_func = {sensor_func}, sensor_event_class = {sensor_event_class}, event_state = {values_from_the_keys['event_state']}, previous_event_state = {values_from_the_keys['previous_event_state']}, sensor_data_size = {values_from_the_keys['sensor_data_size']}, present_reading = {present_reading}")

	return vdm_payload
