# parser/vdm_header.py
from core.config import get_value_from_ini, INI_VMD_HEADER, INI_TYPE0, INI_TYPE2
from core.utils import get_data_from_lst

# Extract VDM header from the block
def extract_vdm_header(block):
	pldm_type_code = get_data_from_lst(block, get_value_from_ini(INI_VMD_HEADER, "PACKET_FORMAT", "pldm_type_code"))
	
	if pldm_type_code == "00":
		ini_file = INI_TYPE0
	elif pldm_type_code == "02":
		ini_file = INI_TYPE2
	else:
		return None
	
	pldm_command_code_idx = get_value_from_ini(ini_file, "PACKET_FORMAT", "pldm_command_code")
	pldm_command_code = get_data_from_lst(block, pldm_command_code_idx)
	pldm_command = get_value_from_ini(ini_file, "PLDM_COMMAND_CODE", pldm_command_code)
	
	return {
		"pldm_type_code": pldm_type_code,
		"pldm_type": get_value_from_ini(INI_VMD_HEADER, "PLDM_TYPE_CODE", pldm_type_code),
		"pldm_command_code": pldm_command_code,
		"pldm_command": pldm_command,
		"requester_busid": get_data_from_lst(block, get_value_from_ini(INI_VMD_HEADER, "PACKET_FORMAT", "requester_pcie_busid")),
		"target_busid": get_data_from_lst(block, get_value_from_ini(INI_VMD_HEADER, "PACKET_FORMAT", "target_pcie_busid")),
		"dest_eid": get_data_from_lst(block, get_value_from_ini(INI_VMD_HEADER, "PACKET_FORMAT", "dest_eid")),
		"source_eid": get_data_from_lst(block, get_value_from_ini(INI_VMD_HEADER, "PACKET_FORMAT", "source_eid"))
	}
	

# Format the VDM header as a printable string (separated from output logic)
def format_vdm_header(block):
	vdm_header = extract_vdm_header(block)
	if vdm_header is None:
		return None
	
	lines = [
		"=" * 160,
		block[0],
		f"PLDM MSG type {vdm_header['pldm_type_code']} {vdm_header['pldm_type']} command code {vdm_header['pldm_command_code']} {vdm_header['pldm_command']} send From EID {vdm_header['source_eid']} (pcie busid: {vdm_header['requester_busid']}:00) To EID {vdm_header['dest_eid']} (pcie busid: {vdm_header['target_busid']}:00) :"
	]
	return "\n".join(lines)
