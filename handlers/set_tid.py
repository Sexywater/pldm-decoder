# handlers/set_tid.py
from core.config import INI_TYPE0
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block, is_request_block
from protocol.payload import new_payload


def process_set_tid_payload(block):
	vdm_payload = new_payload()
		
	if is_request_block(block, 25, 4):
		completion_code = get_values_according_to_keys(block, INI_TYPE0, "SET_TID", ['completion_code'])
		vdm_payload["output"].append(f"Device has {completion_code} received the request ")
		return vdm_payload
	else:
		tid = get_multi_data_from_block(block, INI_TYPE0, "SET_TID", "tid")
		vdm_payload["output"].append(f"Assigne TID {tid} to device")
		return vdm_payload
