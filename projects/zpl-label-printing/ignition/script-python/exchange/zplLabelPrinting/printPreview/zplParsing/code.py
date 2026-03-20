import re

class ZplCmdParser:
	def __call__(self, cmd, fieldDict):
		pass

# Handle parsing of individual ZPL command flags
zplParseDict = {}



# =================================================================================================
# ^BYw,r,h : Bar Code Field Default 
class BY(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:(\d+))?(?:,(\d+))?(?:,(\d+))?", args).groups()
		if (argsParsed):
			fieldDict['by_width'] = argsParsed[0] if argsParsed[0] != None and argsParsed[0] != '' else 3
			fieldDict['by_width_ratio'] = argsParsed[1] if argsParsed[1] != None and argsParsed[1] != '' else 3 
			fieldDict['by_height'] = argsParsed[2] if argsParsed[2] != None and argsParsed[2] != '' else 10
		return argsParsed
zplParseDict['BY'] = BY()


###################### 1D BARCODES, represented by a black rectangle
# =================================================================================================
# ^B1o,e,h,f,g : Code 11 Bar Code
class B1(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,([YN]?))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bc11_check_digit'] = argsParsed[1] if argsParsed[1] is not None else "N"
			fieldDict['bc_height'] = argsParsed[2] #if argsParsed[2] is not None else "10"
			#fieldDict['bc11_print_interp_line'] = argsParsed[3] if argsParsed[3] is not None else "Y"
			#fieldDict['bc11_print_interp_line_above'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['B1'] = B1() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B3o,e,h,f,g : Code 39 Bar Code
class B3(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,([YN]?))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bc39_check_digit'] = argsParsed[1] if argsParsed[1] is not None else "N"
			fieldDict['bc_height'] = argsParsed[2] #if argsParsed[2] is not None else "10"
			#fieldDict['bc39_print_interp_line'] = argsParsed[3] if argsParsed[3] is not None else "Y"
			#fieldDict['bc39_print_interp_line_above'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['B3'] = B3() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BPo,e,h,f,g : Plessey Bar Code
class BP(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,([YN]?))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bcples_check_digit'] = argsParsed[1] if argsParsed[1] is not None else "N"
			fieldDict['bc_height'] = argsParsed[2] #if argsParsed[2] is not None else "10"
			#fieldDict['bcples_print_interp_line'] = argsParsed[3] if argsParsed[3] is not None else "Y"
			#fieldDict['bcples_print_interp_line_above'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['BP'] = BP() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BKo,e,h,f,g,k,l : ANSI Codabar Bar Code
class BK(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,([N]?))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([ABCD]))?(?:,([ABCD]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bcancb_check_digit'] = argsParsed[1] if argsParsed[1] is not None else "N"
			fieldDict['bc_height'] = argsParsed[2] #if argsParsed[2] is not None else "10"
			#fieldDict['bcancb_print_interp_line'] = argsParsed[3] if argsParsed[3] is not None else "Y"
			#fieldDict['bcancb_print_interp_line_above'] = argsParsed[4] if argsParsed[4] is not None else "N"
			#fieldDict['bcancb_start_character'] = argsParsed[5] if argsParsed[5] is not None else "N"
			#fieldDict['bcancb_stop_character'] = argsParsed[6] if argsParsed[6] is not None else "N"
		return argsParsed
zplParseDict['BK'] = BK() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BMo,e,h,f,g,e2 : MSI Bar Code
class BM(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,([ABCD]?))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bcmsi_check_digit_type'] = argsParsed[1] if argsParsed[1] is not None else "N"
			fieldDict['bc_height'] = argsParsed[2] #if argsParsed[2] is not None else "10"
			#fieldDict['bcmsi_print_interp_line'] = argsParsed[3] if argsParsed[3] is not None else "Y"
			#fieldDict['bcmsi_print_interp_line_above'] = argsParsed[4] if argsParsed[4] is not None else "N"
			#fieldDict['bcmsi_ucc_check_digit_interp'] = argsParsed[5] if argsParsed[5] is not None else "N"
		return argsParsed
zplParseDict['BM'] = BM() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BLo,h,g : LOGMARS Bar Code
class BL(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcplan_print_interp_line_above'] = argsParsed[2] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['BL'] = BL() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BZo,h,f,g,t : POSTAL Bar Code
class BZ(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:([0123]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcpost_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcpost_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bcpost_postal_code_type'] = argsParsed[4] if argsParsed[3] is not None else 0
		return argsParsed
zplParseDict['BZ'] = BZ() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B5o,h,f,g : Planet Bar Code
class B5(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcplan_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcplan_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['B5'] = B5() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B8o,h,f,g : EAN-8 Bar Code
class B8(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcean8_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcean8_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['B8'] = B8() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BEo,h,f,g : EAN-13 Bar Code
class BE(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcean13_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcean13_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['BE'] = BE() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BIo,h,f,g : Industrial 2 of 5 Bar Code
class BI(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bci25_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bci25_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['BI'] = BI() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BJo,h,f,g : Standard 2 of 5 Bar Code
class BJ(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcs25_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcs25_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['BJ'] = BJ() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BSo,h,f,g : UPC/EAN Extension Bar Code
class BS(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcext_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcext_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
		return argsParsed
zplParseDict['BS'] = BS() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BUo,h,f,g,e : UPC-A Bar Code
class BU(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcupca_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcupca_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bcupca_ucc_check_digit'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['BU'] = BU() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B9o,h,f,g,e : UPC-E Bar Code
class B9(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bcupce_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bcupce_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bcupce_ucc_check_digit'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['B9'] = B9() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B2o,h,f,g,e : Interleaved 2 of 5 Bar Code
class B2(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bc225_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bc225_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bc225_ucc_check_digit'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['B2'] = B2() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BAo,h,f,g,e : Code 93 Bar Code
class BA(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bc93_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bc93_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bc93_ucc_check_digit'] = argsParsed[4] if argsParsed[4] is not None else "N"
		return argsParsed
zplParseDict['BA'] = BA() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BCo,h,f,g,e,m : Code 128 Bar Code
class BC(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,([YN]))?(?:,([YN]))?(?:,([NUAD]?))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['bc128_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['bc128_print_interp_line_above'] = argsParsed[3] if argsParsed[3] is not None else "N"
			#fieldDict['bc128_ucc_check_digit'] = argsParsed[4] if argsParsed[4] is not None else "N"
			#fieldDict['bc128_mode'] = argsParsed[5] if argsParsed[5] is not None else "N"
		return argsParsed
zplParseDict['BC'] = BC() # need to parse as generic barcode or add parsers for all barcode commands and output the same info





###### SPECIAL GRAPHICS LIKE 2D BARCODES AND IMAGES, represented by a 100x100 black square placed onto the image
# =================================================================================================
# ^GFa,b,c,d,data : Graphic Field or Image 
class GF(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([ABC]))?(?:,(\d*))?(?:,(\d*))?(?:,(\d*))?(?:,(.*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = 'N' # bc orientation doesn't exist but I add it anyway
			#fieldDict['compression_type'] = argsParsed[0] if argsParsed[0] is not None else "A"
			#fieldDict['binary_byte_count'] = argsParsed[1] if argsParsed[1] is not None else 1
			#fieldDict['graphic_field_count'] = argsParsed[2] if argsParsed[2] is not None else 1
			#fieldDict['bytes_per_row'] = argsParsed[3] if argsParsed[3] is not None else 1
			#fieldDict['image_data'] = argsParsed[4] if argsParsed[4] is not None else ""
		return argsParsed
zplParseDict['GF'] = GF() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BO/^B0a,b,c,d,e,f,g :  Aztec 2D Bar Code (either ^B0 or ^BO)
class BO(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,(\d*))?(?:,([YN]))?(?:,(\d*))?(?:,(.*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['magnification'] = argsParsed[1] if argsParsed[1] is not None else 2
			#fieldDict['aztec_ecic'] = argsParsed[2] if argsParsed[2] is not None else "N"
			#fieldDict['aztec_ecss'] = argsParsed[3] if argsParsed[3] is not None else 0
			#fieldDict['aztec_menu_symbol_indicator'] = argsParsed[4] if argsParsed[4] is not None else "N"
			#fieldDict['aztec_number_of_symbols'] = argsParsed[5] if argsParsed[5] is not None else 1
			#fieldDict['aztec_id_field'] = argsParsed[6] if argsParsed[6] is not None else ""
		return argsParsed
zplParseDict['BO'] = BO() # need to parse as generic barcode or add parsers for all barcode commands and output the same info
class B0(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,(\d*))?(?:,([YN]))?(?:,(\d*))?(?:,(.*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['magnification'] = argsParsed[1] if argsParsed[1] is not None else 2
			#fieldDict['aztec_ecic'] = argsParsed[2] if argsParsed[2] is not None else "N"
			#fieldDict['aztec_ecss'] = argsParsed[3] if argsParsed[3] is not None else 0
			#fieldDict['aztec_menu_symbol_indicator'] = argsParsed[4] if argsParsed[4] is not None else "N"
			#fieldDict['aztec_number_of_symbols'] = argsParsed[5] if argsParsed[5] is not None else 1
			#fieldDict['aztec_id_field'] = argsParsed[6] if argsParsed[6] is not None else ""
		return argsParsed
zplParseDict['B0'] = B0() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BBo,h,s,c,r,m : CODABLOCK Bar Code
class BB(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([YN]))?(?:,(\d*))?(?:,(\d*))?(?:,([AEF]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_row_height'] = argsParsed[1] if argsParsed[1] is not None else 8
			#fieldDict['security'] = argsParsed[2] if argsParsed[2] is not None else "Y"
			#fieldDict['characters_per_row'] = argsParsed[3] if argsParsed[3] is not None else 2
			fieldDict['number_of_rows'] = argsParsed[4] if argsParsed[4] is not None else 2
			#fieldDict['charset_mode'] = argsParsed[5] if argsParsed[5] is not None else "F"
			
			#fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_height'] = int(argsParsed[1] * argsParsed[4]) if argsParsed[1] is not None and argsParsed[4] is not None else None
		return argsParsed
zplParseDict['BB'] = BB() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BDm,n,t : UPS Maxicode Bar Code 
class BD(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([2-6]))?(?:,([1-8]))?(?:,([1-8]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = 'N' # bc orientation doesn't exist but I add it anyway
			#fieldDict['mode'] = argsParsed[0] if argsParsed[0] is not None else 2
			#fieldDict['symbol_number'] = argsParsed[1] if argsParsed[1] is not None else 1
			#fieldDict['total_symbols'] = argsParsed[2] if argsParsed[2] is not None else 1
		return argsParsed
zplParseDict['BD'] = BD() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B4o,h,f,m : Code 49 Bar Code 
class B4(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([NAB]))?(?:,([A0-5]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bc_row_height'] = argsParsed[1] if argsParsed[1] is not None else 1
			#fieldDict['bc49_print_interp_line'] = argsParsed[2] if argsParsed[2] is not None else "N"
			#fieldDict['starting_mode'] = argsParsed[3] if argsParsed[3] is not None else 1
		return argsParsed
zplParseDict['B4'] = B4() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^B7o,h,s,c,r,t : PDF417 Bar Code 
class B7(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,([0-8]))?(?:,(\d*))?(?:,(\d*))?(?:,([YN]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_row_height'] = argsParsed[1] if argsParsed[1] is not None else 1
			#fieldDict['security'] = argsParsed[2] if argsParsed[2] is not None else "N"
			#fieldDict['number_of_columns'] = argsParsed[3] if argsParsed[3] is not None else 1
			fieldDict['number_of_rows'] = argsParsed[4] if argsParsed[4] is not None else 3
			#fieldDict['truncate'] = argsParsed[5] if argsParsed[5] is not None else "N"
			
			#fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_height'] = int(argsParsed[1] * argsParsed[4]) if argsParsed[1] is not None and argsParsed[4] is not None else None
		return argsParsed
zplParseDict['B7'] = B7() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BFo,h,m : MicroPDF417 Bar Code 
class BF(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,(\d*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			fieldDict['bc_height'] = argsParsed[1] #if argsParsed[1] is not None else "10"
			#fieldDict['mode'] = argsParsed[2] if argsParsed[2] is not None else 0
		return argsParsed
zplParseDict['BF'] = BF() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BTo,w1,r1,h1,w2,h2 : TLC39 Bar Code 
class BT(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,(\d+))?(?:,(\d*))?(?:,(\d*))?(?:,(\d*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['bc39_width'] = argsParsed[1] if argsParsed[1] is not None else 2
			#fieldDict['bc39_width_ratio'] = argsParsed[2] if argsParsed[2] is not None else 2
			#fieldDict['bc39_height'] = argsParsed[3] if argsParsed[3] is not None else 60
			#fieldDict['bc417_row_height'] = argsParsed[4] if argsParsed[4] is not None else 4
			#fieldDict['bc417_narrow_bar_width'] = argsParsed[5] if argsParsed[5] is not None else 2
		return argsParsed
zplParseDict['BT'] = BT() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BQa,b,c,d,e : QR Code 
class BQ(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([N]))?(?:,([12]))?(?:,(\d*))?(?:,([HQML]))?(?:,([0-7]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			#fieldDict['bc_orientation'] = 'N' # bc orientation doesn't exist but I add it anyway
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['qr_model'] = argsParsed[1] if argsParsed[1] is not None else 2
			#fieldDict['magnification'] = argsParsed[2] if argsParsed[2] is not None else 2
			#fieldDict['error_correction'] = argsParsed[3] if argsParsed[3] is not None else "Q"
			#fieldDict['mask_value'] = argsParsed[4] if argsParsed[4] is not None else 7
		return argsParsed
zplParseDict['BQ'] = BQ() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BRa,b,c,d,e,f : GS1 Databar 
class BR(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,(\d*))?(?:,([12]))?(?:,(\d*))?(?:,(\d*))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "R"
			#fieldDict['symbology'] = argsParsed[1] if argsParsed[1] is not None else 1
			#fieldDict['magnification'] = argsParsed[2] if argsParsed[2] is not None else 3
			#fieldDict['separator_height'] = argsParsed[3] if argsParsed[3] is not None else 1
			#fieldDict['bc_height'] = argsParsed[4] #if argsParsed[4] is not None else 25
			#fieldDict['segment_width'] = argsParsed[5] if argsParsed[5] is not None else 22
		return argsParsed
zplParseDict['BR'] = BR() # need to parse as generic barcode or add parsers for all barcode commands and output the same info

# =================================================================================================
# ^BXo,h,s,c,r,f,g,a : Data Matrix 2D Barcode
class BX(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(?:([NRIB]))?(?:,(\d*))?(?:,(\d*))?(?:,(\d*))?(?:,(\d*))?(?:,([1-6]))?(?:,([^ ]))?(?:,([12]))?", args).groups()
		if (argsParsed):
			fieldDict['bc_square'] = 100 # unknown dimensions so I give it default square side length
			fieldDict['bc_orientation'] = argsParsed[0] if argsParsed[0] is not None else "N"
			#fieldDict['symbol_element_height'] = argsParsed[1] if argsParsed[1] is not None else 2
			#fieldDict['quality_level'] = argsParsed[2] if argsParsed[2] is not None else 0
			#fieldDict['number_of_columns'] = argsParsed[3] if argsParsed[3] is not None else 9
			#fieldDict['number_of_rows'] = argsParsed[4] if argsParsed[4] is not None else 9
			#fieldDict['format_id'] = argsParsed[5] if argsParsed[5] is not None else 6
			#fieldDict['escape_character'] = argsParsed[6] if argsParsed[6] is not None else "~"
			#fieldDict['aspect_ratio'] = argsParsed[7] if argsParsed[7] is not None else 1
		return argsParsed
zplParseDict['BX'] = BX() # need to parse as generic barcode or add parsers for all barcode commands and output the same info









###################### TEXT AND OTHER IMPORTANT STUFF
# =================================================================================================
# ^Afo,h,w : Scalable/Bitmapped Font
class A(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"([A-Z0-9])([NRIB]),(\d+),(\d+)", args).groups()
		if (argsParsed):
			fieldDict['font_name'] = argsParsed[0]
			fieldDict['font_orientation'] = argsParsed[1]
			fieldDict['font_height'] = argsParsed[2]
			fieldDict['font_width'] = argsParsed[3] if argsParsed[2] != None else 0
		return argsParsed
zplParseDict['A'] = A()

# =================================================================================================
# ^FBa,b,c,d,e : Field Block
class FB(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d*),(\d*),(\d*),([LCRJ]?)(?:,(\d*))?", args).groups()
		if (argsParsed):
			fieldDict['field_block_width'] = argsParsed[0] if argsParsed[0] is not None else 0
			fieldDict['field_block_max_lines'] = argsParsed[1] if argsParsed[1] is not None else 1
			fieldDict['field_block_line_space'] = argsParsed[2] if argsParsed[2] is not None else 0
			fieldDict['field_block_justify'] = argsParsed[3] if argsParsed[3] is not None else "L"
			fieldDict['field_block_indent'] = argsParsed[4] if argsParsed[4] is not None else 0
		return argsParsed
zplParseDict['FB'] = FB()

# =================================================================================================
# FDa : Field Data
class FD(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(.*)", args).groups()
		if (argsParsed):
			fieldDict['field_data'] = argsParsed[0]
		return argsParsed
zplParseDict['FD'] = FD()

# =================================================================================================
# FHa : Field Hexadecimal Indicator
class FH(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"((?![\^\~]).)", args).groups()
		if (argsParsed):
			fieldDict['field_hex_indicator'] = argsParsed[0]
		return argsParsed
zplParseDict['FH'] = FH()

# =================================================================================================
# ^FOx,y,z : Field Origin
class FO(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+),(\d+)(?:,([0-2]))?", args).groups()
		if (argsParsed):
			fieldDict['field_origin_x'] = argsParsed[0]
			fieldDict['field_origin_y'] = argsParsed[1]
			fieldDict['field_origin_z'] = argsParsed[2] if argsParsed[2] != None else '0'
		return argsParsed
zplParseDict['FO'] = FO()

# =================================================================================================
# ^FTx,y,z : Field Typeset
class FT(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+),(\d+)(?:,([0-2]))?", args).groups()
		if (argsParsed):
			fieldDict['field_typeset_x'] = argsParsed[0]
			fieldDict['field_typeset_y'] = argsParsed[1]
			fieldDict['field_typeset_z'] = argsParsed[2] if argsParsed[2] != None else '0'
		return argsParsed
zplParseDict['FT'] = FT()

# =================================================================================================
# ^FX : Comment
class FX(ZplCmdParser):
	def __call__(self, args, fieldDict):
		# Ignore comments
		return True
zplParseDict['FX'] = FX()

# =================================================================================================
# ^GBw,h,t,c,r : Graphic Box
class GB(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+),(\d+),(\d+)(?:,([BW]))?(?:,(\d+))?", args).groups()
		if (argsParsed):
			fieldDict['graphic_box_w'] = argsParsed[0]
			fieldDict['graphic_box_h'] = argsParsed[1]
			fieldDict['graphic_box_t'] = argsParsed[2]
			fieldDict['graphic_box_c'] = argsParsed[3] if argsParsed[3] is not None else 'B'
			fieldDict['graphic_box_r'] = argsParsed[4] if argsParsed[4] is not None else '0'
		return argsParsed
zplParseDict['GB'] = GB()

# =================================================================================================
# LL : Label Length
class LL(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+)", args).groups()
		if (argsParsed):
			fieldDict['label_length'] = argsParsed[0]
		return argsParsed
zplParseDict['LL'] = LL()

# =================================================================================================
# LS : Label Shift
class LS(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+)", args).groups()
		if (argsParsed):
			fieldDict['label_shift_left_value'] = argsParsed[0]
		return argsParsed
zplParseDict['LS'] = LS()

# =================================================================================================
# MM : Print Mode
class MM(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"([TPRACD])(?:,(NY))?", args).groups()
		if (argsParsed):
			fieldDict['print_mode'] = argsParsed[0] if argsParsed[0] is not None else 'T'
			fieldDict['preepel_select'] = argsParsed[1] if argsParsed[1] is not None else 'Y'
		return argsParsed
zplParseDict['MM'] = MM()

# =================================================================================================
# ^POa : Print Orientation
class PO(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"([NI])", args).groups()
		if (argsParsed):
			fieldDict['print_orientation'] = argsParsed[0]
		return argsParsed
zplParseDict['PO'] = PO()

# =================================================================================================
# PQ : Print Quantity
class PQ(ZplCmdParser):
	def __call__(self, args, fieldDict):
		# Ignore print commands
		return True
zplParseDict['PQ'] = PQ()

# =================================================================================================
# PW : Print Width
class PW(ZplCmdParser):
	def __call__(self, args, fieldDict):
		argsParsed = re.search(r"(\d+)", args).groups()
		if (argsParsed):
			fieldDict['label_width'] = argsParsed[0]
		return argsParsed
zplParseDict['PW'] = PW()







# =================================================================================================
# ===================================== Text Parsing Scripts ======================================
# =================================================================================================

# Parse individual Commands after splitting text up by '^FS' pattern
def zplFieldToDict(zplFieldStr):
	fieldDict = {}
	cmdIdentifier = r"\^([A]|[A-Z0-9]{2})(.*?)(?=\^[A-Z0-9$]{2}|$)" 
	cmds = re.findall(cmdIdentifier, zplFieldStr)
	for cmd in cmds:
		cmdId = cmd[0]
		cmdArgs = cmd[1]
		if cmdId in zplParseDict:
			parsed = zplParseDict[cmdId](cmdArgs, fieldDict)
			if not parsed:
				system.perspective.print("Couldn't parse |" + cmd + "|")
		else:
			system.perspective.print(cmdId + " parsing not defined")
			system.perspective.print(cmd)
	
	return fieldDict



# if any ^GF images exist, get those out of the labelStr before continuing, since they do not have ^FS at the end
def replaceImages(labelString):
	image_identifier = r"(?<=\^GF)(.*?)(?=\^)"
	imageStrings = re.findall(image_identifier, labelString) # always returns exact order in which entries are found
	
	images = []
	for i in imageStrings:
		imageCmd = '^GF' + i # add the ^GF part back in, since we removed it when we looked between ^GF and ^
		labelString = labelString.replace(imageCmd, '^FH\^BQN,2,3^FDimagePlaceholder^FS')
		
	# return the labelString with the GF command removed, replaced by the ^BQ command for QR code
	return labelString



# Get Field Dicts from Label
def getFieldDicts(zplText):
	# get rid of any whitespaces and then break into separate labels (labelStrs) (each label is between ^XA and ^XZ)
	zplTextNoLineBreaks = ''.join(char for char in zplText if char not in '\n\r')
	label_identifier = r"(?<=\^XA)(.*?)(?=\^XZ)"
	labelStrs = re.findall(label_identifier, zplTextNoLineBreaks)
	
	fieldDicts = []
	for labelStr in labelStrs:
		if '^GF' in labelStr:
			# remove any images first and break into fields
			newLabelStr = replaceImages(labelStr)
			fieldStrs = newLabelStr.split('^FS')
		else:
			# just break into fields
			fieldStrs = labelStr.split('^FS')
		
		for fieldStr in fieldStrs:
			system.perspective.print(fieldStr)
			fieldDicts.append(zplFieldToDict(fieldStr))
	
	return fieldDicts