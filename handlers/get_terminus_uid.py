# handlers/get_terminus_uid.py
from core.config import INI_TYPE2
from protocol.reader import get_values_according_to_keys
from protocol.payload import new_payload


def process_get_terminus_UID_payload(block):
	vdm_payload = new_payload()
	
	if len(block) == 21:
		vdm_payload["output"].append(f"Request device terminus UID")
		return vdm_payload
		
	completion_code = get_values_according_to_keys(block, INI_TYPE2, "GET_SENSOR_READING_RESPOND", ['completion_code'])
	
	tertminus_UID = ' '.join(block[22:38])
	vdm_payload["output"].append(f"Terminus UID : {tertminus_UID}, completion code : {completion_code}")
		
	return vdm_payload
