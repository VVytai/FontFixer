import os
import sys
from fontTools.ttLib import TTFont
import fontforge

def fix_font_mojibake(input_fontfile, output_fontfile):

	hasEncodingProblems = False

	with TTFont(input_fontfile) as font:

		name = font['name'].names
		for namerecord in name:
			isUnicode = namerecord.isUnicode()
			isUnicodeCompatible = namerecord.encodingIsUnicodeCompatible()
			actualEncoding = namerecord.getEncoding()
			
			if not isUnicode and not isUnicodeCompatible and namerecord.platformID == 3:
				try:
					try_decode_string = namerecord.toStr()
				except UnicodeDecodeError as e:
					if not hasEncodingProblems:
						hasEncodingProblems = True
						print(f"Found encoding problems in {input_fontfile}")

				bs = namerecord.string
				bs_fixed = bytes([byte for byte in bs if byte != 0x00])
				fixed_string = bs_fixed.decode(actualEncoding)
				namerecord.string = fixed_string
				namerecord.platEncID = 1
				
		cmap = font["cmap"]
		for subtable in cmap.tables:
			isUnicode = subtable.isUnicode()
			if not isUnicode and subtable.platformID == 3:
				subtable.platEncID = 1
		font.save(output_fontfile)

	if hasEncodingProblems:
		print("Encoding repaired.")
		font = fontforge.open(output_fontfile)
		print(f"Repaired 'name' table: {font.sfnt_names}")
		font.generate(output_fontfile, flags=('opentype', 'dummy-dsig', 'no-FFTM-table'))
		print(f"Saved to {output_fontfile}")
		font.close()
	else:
		print(f"No encoding problems in {output_fontfile}")

if __name__ == "__main__":

	output_folder = 'repaired_fonts'

	if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
		current_dir = os.path.dirname(sys.executable)
		print(f"Temp folder: {sys._MEIPASS}\n")
	else:
		current_dir = os.path.dirname(os.path.abspath(__file__))

	output_dir = os.path.join(current_dir, output_folder)
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	for root, dirs, files in os.walk(current_dir):
		if output_folder in dirs:
			dirs.remove(output_folder)
		for file in files:
			if file.lower().endswith(('.ttf', '.otf')):
				input_file_path = os.path.join(root, file)
				relative_path = os.path.relpath(input_file_path, current_dir)
				output_file_path = os.path.join(output_dir, relative_path)
				if not os.path.exists(os.path.dirname(output_file_path)):
					os.makedirs(os.path.dirname(output_file_path))
					
				try:
					fix_font_mojibake(input_file_path, output_file_path)
					print()
				except Exception as e:
					print(f"An error occurred when processing fonts: {str(e)}\n")

	print("Completed!")
	os.system("pause")
