# handlers/get_pldm_types.py
from core.config import INI_TYPE0
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block
from protocol.payload import new_payload


def process_getpldmtypes_payload(block):
	vdm_payload = new_payload()
	
	if len(block) == 21:
		vdm_payload["output"].append(f"Get PLDM types request.")
		return vdm_payload
		
	else:
		completion_code = get_values_according_to_keys(block, INI_TYPE0, "GET_PLDM_TYPES", ['completion_code'])
		pldm_types_hex = get_multi_data_from_block(block, INI_TYPE0, "GET_PLDM_TYPES", "pldm_types")
		pldm_types_int = int(pldm_types_hex, 16)
		pldm_types_bin = bin(int(pldm_types_hex, 16))[2:]
		
		support_type = 0
		binary_num = pldm_types_int
		output = f"completion_code = {completion_code} , pldm_types_hex = {pldm_types_hex} , pldm_types_bin = {pldm_types_bin} , means it support pldm type " 
		
		while binary_num > 0:
			if binary_num & 1:  
				output = output + str(support_type) + " / "
			binary_num >>= 1
			support_type += 1
			
		vdm_payload["output"].append(output)
		return vdm_payload
