# handlers/get_tid.py
from core.config import INI_TYPE0
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block
from protocol.payload import new_payload


def process_get_tid_payload(block):
	vdm_payload = new_payload()
	
	if len(block) == 21:
		vdm_payload["output"].append(f"Get device tid request.")
		return vdm_payload
		
	else:
		completion_code = get_values_according_to_keys(block, INI_TYPE0, "SET_TID", ['completion_code'])
		tid = get_multi_data_from_block(block, INI_TYPE0, "GET_TID", "tid")
		vdm_payload["output"].append(f"Device return its tid {tid}, completion code : {completion_code}")
		return vdm_payload
