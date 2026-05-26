# parser/log_processor.py
from core.utils import remove_keyword, remove_keyword_list
import re

# Filter, print, and extract log blocks in a single file pass
def process_file(file_path, eid):
	"""Read file once, simultaneously filter-print and extract blocks for the given EID"""
	capture = False
	current_block = []
	blocks = []
	with open(file_path, 'r', encoding='utf-8') as f:
		for line in f:
			line = line.rstrip()
			
			if f'>>{eid}' in line or f'<<{eid}' in line:
				capture = True
				print(line)
				current_block.extend(line.split())
				current_block = current_block[:1] + current_block[9:]
			elif "RECV <<<<<<<<<<<<<<<<<<<<<<<<<<<" in line:
				capture = True
				print(line)
				current_block.extend(line.split())
			elif capture:
				if not line:
					capture = False
					print()
					if current_block:
						blocks.append(current_block)
						current_block = []
				else:
					print(line)
					current_block.extend(line.split())
	
	return blocks


def merge_log_blocks(blocks):
	merged_blocks = []
	
	for block in blocks:
		if len(block) >= 3 and block[1] == 'RECV' and block[2] == '<<<<<<<<<<<<<<<<<<<<<<<<<<<':
			processed_block = block[21:]
			
			if merged_blocks:
				merged_blocks[-1].extend(processed_block)
			else:
				merged_blocks.append(processed_block)
		else:
			merged_blocks.append(block)
	return merged_blocks

def clean_block(block):
	return remove_keyword(block, remove_keyword_list)
