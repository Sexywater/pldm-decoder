# main.py
import argparse
import sys
from parser.log_processor import process_file, merge_log_blocks, clean_block
from parser.vdm_header import extract_vdm_header
from protocol.payload import decode_payload
from handlers.platform_event_msg import process_platformeventmsg_payload
from handlers.get_sensor_reading import process_getsensorreading_payload
from handlers.get_terminus_uid import process_get_terminus_UID_payload
from handlers.set_tid import process_set_tid_payload
from handlers.get_tid import process_get_tid_payload
from handlers.get_pldm_version import process_get_pldm_version_payload
from handlers.get_pldm_types import process_getpldmtypes_payload
from handlers.get_pldm_commands import process_get_pldm_commands_payload
from handlers.get_state_sensor_readings import process_getstatesensorreadings_payload
from handlers.get_pdr_repository_info import process_get_pdr_repository_info_payload
from handlers.get_pdr import process_get_pdr_payload

# Dispatch table: (type_code, command_code) -> (ini_file, handler)
DISPATCH = {
    ("02", "0A"): ("pldm_type2.ini", process_platformeventmsg_payload),
    ("02", "11"): ("pldm_type2.ini", process_getsensorreading_payload),
    ("02", "21"): ("pldm_type2.ini", process_getstatesensorreadings_payload),
    ("02", "03"): ("pldm_type2.ini", process_get_terminus_UID_payload),
    ("02", "50"): ("pldm_type2.ini", process_get_pdr_repository_info_payload),
    ("02", "51"): ("pldm_type2.ini", process_get_pdr_payload),
    ("00", "01"): ("pldm_type0.ini", process_set_tid_payload),
    ("00", "02"): ("pldm_type0.ini", process_get_tid_payload),
    ("00", "03"): ("pldm_type0.ini", process_get_pldm_version_payload),
    ("00", "04"): ("pldm_type0.ini", process_getpldmtypes_payload),
    ("00", "05"): ("pldm_type0.ini", process_get_pldm_commands_payload),
}


def main():
	parser = argparse.ArgumentParser(
		prog='pldm_decoder',
		description='PLDM (Platform Level Data Model) trace decoder for MCTP over PCIe VDM logs',
		epilog='Examples:\n'
		       '  python3 pldm_decoder.py -e 08 -f mctp_trace.txt\n'
		       '  python3 pldm_decoder.py -e 08 -f mctp_trace.txt -v',
		formatter_class=argparse.RawDescriptionHelpFormatter
	)
	parser.add_argument('-e', '--eid', type=str, required=True, metavar='EID',
	                    help='Target device Endpoint ID to filter (e.g. 08)')
	parser.add_argument('-f', '--file', type=str, required=True, metavar='FILE',
	                    help='Path to the MCTP trace log file')
	parser.add_argument('-v', '--verbose', action='store_true',
	                    help='Enable verbose output with detailed field information')
	
	args = parser.parse_args()

	# Read file once: filter-print and extract blocks simultaneously
	blocks = merge_log_blocks(process_file(args.file, args.eid))
	
	for block in blocks:
		cleaned_block = clean_block(block)
		if not cleaned_block:
			continue
		vdm_header = extract_vdm_header(cleaned_block)
		if vdm_header:
			type_code = vdm_header["pldm_type_code"]
			command_code = vdm_header["pldm_command_code"]
			handler = DISPATCH.get((type_code, command_code))
			if handler:
				_, process_func = handler
				decode_payload(cleaned_block, process_func(cleaned_block), args.verbose)

if __name__ == "__main__":
	main()
