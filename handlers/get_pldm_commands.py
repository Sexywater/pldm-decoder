# handlers/get_pldm_commands.py
from core.config import INI_TYPE0
from protocol.reader import get_values_according_to_keys, get_multi_data_from_block, is_request_block
from protocol.payload import new_payload


def process_get_pldm_commands_payload(block):
	vdm_payload = new_payload()
	
	if is_request_block(block, 29, 3):
		pldm_type = get_multi_data_from_block(block, INI_TYPE0, "GET_PLDM_COMMANDS_REQUEST", "pldm_type")
		
		pldm_version_lst = block[22:-3]
		pldm_version_lst.reverse()
		# Filter out FF padding bytes, then format version segments separated by 00
		filtered = [b for b in pldm_version_lst if b != 'FF']
		segments = []
		current = []
		for b in filtered:
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
		
		vdm_payload["output"].append(f"Request the device's supported pldm commands regarding PLDM Type {pldm_type} version {pldm_version_str}")	
		return vdm_payload
	
	else:
		completion_code = get_values_according_to_keys(block, INI_TYPE0, "GET_PLDM_COMMANDS_RESPOND", ['completion_code'])
		pldm_commands_lst = block[22:]
		
		# Parse command bitmap: each byte's bits represent supported command codes
		# Bit 0 of byte 0 = command 0, Bit 1 of byte 0 = command 1, etc.
		supported_commands = []
		for byte_idx, hex_byte in enumerate(pldm_commands_lst):
			try:
				byte_val = int(hex_byte, 16)
			except ValueError:
				continue
			for bit in range(8):
				if byte_val & (1 << bit):
					command_code = byte_idx * 8 + bit
					supported_commands.append(f"0x{command_code:02X}")
		
		vdm_payload["output"].append(f"Supported pldm commands : {supported_commands}, completion_code : {completion_code} ")
		
		return vdm_payload
