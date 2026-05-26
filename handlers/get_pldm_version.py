# handlers/get_pldm_version.py
from core.config import INI_TYPE0
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block, is_request_block
from protocol.payload import new_payload


def process_get_pldm_version_payload(block):
	vdm_payload = new_payload()
	
	if is_request_block(block, 29, 2):
		data_transfer_handle = get_multi_data_from_block(block, INI_TYPE0, "GET_PLDM_VERSION_REQUEST", "data_transfer_handle")
		transfer_operation_flag = get_values_according_to_keys(block, INI_TYPE0, "GET_PLDM_VERSION_REQUEST", ["transfer_operation_flag"])
		pldm_type = get_multi_data_from_block(block, INI_TYPE0, "GET_PLDM_VERSION_REQUEST", "pldm_type")
		
		vdm_payload["output"].append(f"Request the device's support status regarding PLDM Type {pldm_type}")
		vdm_payload["verbose"].append(f"data_transfer_handle : {data_transfer_handle} , transfer_operation_flag : {transfer_operation_flag}")
	
		return vdm_payload

	else:
		keys = ["completion_code", "transfer_flag"]
		values_from_the_keys = get_values_according_to_keys(block, INI_TYPE0, "GET_PLDM_VERSION_RESPONSE", keys)
		# Parse version bytes: filter 0xFF padding, use 0x00 as segment separator
		pldm_version_bytes = block[27:-6]
		pldm_version_bytes.reverse()
		segments = []
		current = []
		for b in pldm_version_bytes:
			if b == 'FF':
				continue
			if b == '00':
				if current:
					segments.append('.'.join(current))
					current = []
			else:
				# PLDM version bytes are BCD-like: high nibble is 0xF, low nibble is the digit
				# e.g. 'F1' -> '1', 'F3' -> '3', '10' -> '10' (for 1.0)
				if len(b) == 2 and b[0] == 'F':
					current.append(b[1])
				else:
					current.append(b)
		if current:
			segments.append('.'.join(current))
		pldm_version_str = ' | '.join(segments)
		
		vdm_payload["output"].append(f"Device support PLDM version : {pldm_version_str}")
		vdm_payload["verbose"].append(f"completion code = {values_from_the_keys['completion_code']}, transfer_flag = {values_from_the_keys['transfer_flag']}")
		
		return vdm_payload
