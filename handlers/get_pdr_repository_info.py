# handlers/get_pdr_repository_info.py
from core.config import INI_TYPE2
from protocol.reader import get_values_according_to_keys, get_multi_keys_data_from_block
from protocol.payload import new_payload


def process_get_pdr_repository_info_payload(block):
	vdm_payload = new_payload()
	
	if len(block) == 21:
		vdm_payload["output"].append(f"Get PDR Repository Info request.")
		return vdm_payload
		
	else:
		keys_2_values = ["completion_code", "repository_state", "data_transfer_handle_timeout"]
		values_from_the_keys = get_values_according_to_keys(block, INI_TYPE2, "GET_PDR_REPOSITORY_INFO", keys_2_values)
		
		keys_2_datas = ["update_time", "oem_update_time", "record_count", "repository_size", "largest_record_size"]
		datas_from_the_keys = get_multi_keys_data_from_block(block, INI_TYPE2, "GET_PDR_REPOSITORY_INFO", keys_2_datas)
		
		vdm_payload["output"].append(f"completion code : {values_from_the_keys['completion_code']} , reporsitory_state : {values_from_the_keys['repository_state']}")
		vdm_payload["verbose"].append(f"update_time = {datas_from_the_keys['update_time']} , oem_update_time = {datas_from_the_keys['oem_update_time']}, record_count = {datas_from_the_keys['record_count']} , repository_size = {datas_from_the_keys['repository_size']} , largest_record_size = {datas_from_the_keys['largest_record_size']} , data_transfer_handle_timeout = {values_from_the_keys['data_transfer_handle_timeout']}")
		
		return vdm_payload
