from java.awt import AlphaComposite, BasicStroke, Color, Font, FontMetrics, Graphics2D, GraphicsEnvironment, RenderingHints
from java.awt.geom import AffineTransform 
from java.awt.image import BufferedImage
from javax.imageio import ImageIO
from java.io import ByteArrayOutputStream
from java.util import Base64
import math



def getFontList():
	# Get all available font family names from the local graphics environment and print
	genv = GraphicsEnvironment.getLocalGraphicsEnvironment()
	fontFamilyNames = genv.getAvailableFontFamilyNames()
	for name in fontFamilyNames:
		print(name)
	return fontFamilyNames
	# font list results include "Arial Narrow", "PT Sans Narrow", "Andale Mono" (monospace), "Courier" (monospace), "Noto Sans"



def rotationCharToDeg(value):
	if value == 'N': return 0 # Normal
	if value == 'R': return 90 # Rotate 90
	if value == 'I': return 180 # Inverted
	if value == 'B': return 270 # Read From Bottom
	return -1



def roundToNearest(x, base):
	return int(base * round(float(x)/base))



def drawBlankLabel(widthInches, heightInches, dpi):
	# create an in-memory image. Use TYPE_INT_ARGB to handle transparency if needed
	widthDots = int(widthInches * dpi)
	heightDots = int(heightInches * dpi)
	image = BufferedImage(widthDots, heightDots, BufferedImage.TYPE_INT_ARGB)
	
	# start new Graphics2D object 
	g = image.createGraphics()
	g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
	g.setComposite(AlphaComposite.Src)
	
	# draw a white background (filled rectangle) on the image
	g.setColor(Color.WHITE)
	g.fillRect(0, 0, widthDots, heightDots)
	
	# dispose of Graphics2D object when done drawing. drawn graphic will persist on buffered image
	g.dispose() 
	
	return image



def drawGraphicBox(image, gbX, gbY, justification, fieldType, gbWidth, gbHeight, gbThickness, gbColor = 'B', gbRoundness = 0):
	# start new Graphics2D object
	g = image.createGraphics()
	g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
	g.setComposite(AlphaComposite.Src)
	
	# Set the color and stroke for the graphic box (values can only be 'W' for white or 'B' for black)
	g.setColor(Color.WHITE) if gbColor == 'W' else g.setColor(Color.BLACK) 
	
	# a square becomes a circle if gbRoundness = 8. At a value of 8, the arc diameter equals the shortest side length
	arcDiameter = int(0.1248 * gbRoundness * min(gbWidth, gbHeight)) # weird behavior if exactly dividing by 8
	
	# set stroke thickness, which extends both inward and outward
	g.setStroke(BasicStroke(gbThickness))
	
	# the thickness in Labelary only grows inward, but not sure if this is the actual behavior when printed.
	# if the thickness is only supposed to grow inward, gbX, gbY, gbWidth, and gbHeight will need to be adjusted
	# x and y will need to be increased by half the thickness, while width and height will need to be decreased by 1 thickness
	gbX = int(gbX + 0.5 * gbThickness)
	gbY = int(gbY + 0.5 * gbThickness)
	gbWidth = int(gbWidth - gbThickness)
	gbHeight = int(gbHeight - gbThickness)
	
	# finally draw the rectangle or rounded rectangle
	if gbRoundness == 0:
		g.drawRect(gbX, gbY, gbWidth, gbHeight)
	else:
		g.drawRoundRect(gbX, gbY, gbWidth, gbHeight, arcDiameter, arcDiameter)
	
	# dispose of Graphics2D object when done drawing. drawn graphic will persist on buffered image
	g.dispose() 
	
	return image



def drawText(image, fieldData, fieldX, fieldY, justification, fieldType, fontWidth, fontHeight, fontZebra = '0', orientation = 'N', fontColor = 'B', blockWidth = 0, blockLines = 1, blockSpacing = 0, blockJustify = 'L', blockIndent = 0):
	# start new Graphics2D object and Affine Transform
	at = AffineTransform()
	g = image.createGraphics()
	g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON)
	g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
	g.setComposite(AlphaComposite.Src)
	
	# set font color, font, and width scale factor depending on the font
	g.setColor(Color.WHITE) if fontColor == 'W' else g.setColor(Color.BLACK)
	
	if fontZebra == 'A':
		# in Zebra Designer, Font A can have widths in increments of 5 up to 50, and heights in increments of 9 up to 90 dots
		# there are only 100 different discrete sizes for Font A text (9,5), (9,10), ..., (18,5), (18,10), (18,15), ... (90, 50)
		fontHeight = max(9, min(90, roundToNearest(fontHeight, 9))) # adjust to make sure fontHeight is set between 9 and 90
		if fontWidth != 0:
			fontWidth = max(5, min(50, roundToNearest(fontWidth, 5))) # adjust to make sure fontWidth is set between 5 and 50
			scaleFactor = 1.125 * (float(fontWidth) / 50) / (float(fontHeight) / 90)
		else:
			scaleFactor = 1.125 # by default, scale Andale Mono by 1.125 to try to match Zebra Font A 
		g.setFont(Font("Andale Mono", Font.PLAIN, fontHeight)) # Andale Mono Plain is similar to the monospace Zebra A font
		
	else: # everything else will be Zebra Font (Arial Narrow), which scales naturally
		#scaleFactor = fontWidth / rectWidth # scale factor to achieve zpl font width (but this is not how it works)
		scaleFactor = 1.025 * float(fontWidth) / float(fontHeight) if fontHeight != 0 else 1 # by default, scale Arial Narrow by 1.025
		g.setFont(Font("Arial Narrow", Font.BOLD, fontHeight)) # Arial Narrow Bold is similar to the default Zebra 0 font
	
	# after font is set, get font rectangle width. getHeight() is not needed, since it is undesirably 10-15% more than fontHeight
	font = g.getFont()
	if blockWidth == 0:
		rectWidth = g.getFontMetrics(font).getStringBounds(fieldData, g).getWidth() # getHeight()
	else:
		rectWidth = blockWidth # if defined, use block width instead of calculating imaginary rectangle around text
	
	# get rotation and use it to determine which affine transformations will be needed
	rotation = rotationCharToDeg(orientation)
	
	# Affine Transforms involve matrix multiplication which is order-dependent. for each rotation value, do these steps:
	# step 1: resize font width, while preserving xy position, if provided font width from ZPL is nonzero
	# step 2: rotate text rectangle
	# step 3: translate slightly after rotation, since it rotates about the wrong corner
	# step 4: lastly, right-justify if necessary (shift to the left by 1 rectangle width).
	# there are 16 permutations of ^FT vs ^FO, 0 vs 90 vs 180 vs 270 degrees, and left vs right justification. 
	if rotation == 90:
		if fontWidth > 0 and scaleFactor > 0: 
			stretch = AffineTransform.getScaleInstance(1, scaleFactor) # apply scaleFactor to height if rotated 90 or 270 degrees
			fieldY = int(fieldY / scaleFactor) # also requires scaling the y position
			at.concatenate(stretch)
		
		at.rotate(math.radians(rotation), fieldX, fieldY)
		
		if fieldType == 'FO' and int(justification) == 0:
			translate = AffineTransform.getTranslateInstance(0, -fontHeight)
			at.concatenate(translate)
		elif fieldType == 'FT' and int(justification) == 1:
			justify = AffineTransform.getTranslateInstance(-rectWidth, 0)
			at.concatenate(justify)
		
	elif rotation == 180:
		if fontWidth > 0 and scaleFactor > 0: 
			stretch = AffineTransform.getScaleInstance(scaleFactor, 1) # apply scaleFactor to the width
			fieldX = int(fieldX / scaleFactor) # also requires scaling the x position
			at.concatenate(stretch)
		
		at.rotate(math.radians(rotation), fieldX, fieldY)
		
		if fieldType == 'FO' and int(justification) == 0:
			translate = AffineTransform.getTranslateInstance(-rectWidth, -fontHeight)
			at.concatenate(translate)
		elif fieldType == 'FO' and int(justification) == 1: 
			translateAndJustify = AffineTransform.getTranslateInstance(0, -fontHeight)
			at.concatenate(translateAndJustify)
		elif fieldType == 'FT' and int(justification) == 1:
			justify = AffineTransform.getTranslateInstance(-rectWidth, 0)
			at.concatenate(justify)
		
	elif rotation == 270:
		if fontWidth > 0 and scaleFactor > 0: 
			stretch = AffineTransform.getScaleInstance(1, scaleFactor) # apply scaleFactor to height if rotated 90 or 270 degrees
			fieldY = int(fieldY / scaleFactor) # also requires scaling the y position
			at.concatenate(stretch)
		
		at.rotate(math.radians(rotation), fieldX, fieldY)
		
		if fieldType == 'FO' and int(justification) == 0:
			translate = AffineTransform.getTranslateInstance(-rectWidth, 0)
			at.concatenate(translate)
		elif fieldType == 'FO' and int(justification) == 1:
			translateAndJustify = AffineTransform.getTranslateInstance(-rectWidth, -fontHeight)
			at.concatenate(translateAndJustify)
		elif fieldType == 'FT' and int(justification) == 1: 
			justify = AffineTransform.getTranslateInstance(-rectWidth, 0)
			at.concatenate(justify)
		
	else: # if rotation == 0: (no rotate transform)
		if fontWidth > 0 and scaleFactor > 0: 
			stretch = AffineTransform.getScaleInstance(scaleFactor, 1) # apply scaleFactor to the width
			fieldX = int(fieldX / scaleFactor) # also requires scaling the x position
			at.concatenate(stretch)
		
		if int(justification) == 1: 
			justify = AffineTransform.getTranslateInstance(-rectWidth, 0)
			at.concatenate(justify)
		
	# apply all affine transforms to drawing before drawing string
	g.setTransform(at)
	
	# change Y position of text based on whether the fieldType in the zpl command is ^FT or ^FO 
	# the default behavior of graphics2D.drawString matches ^FT zpl command, which puts xy position at bottom left of text
	# need to add fontHeight to y position to get behavior of ^FO zpl command.
	if fieldType == 'FO':
		fieldY += 0.75 * fontHeight # this ratio seems to work well
	
	# finally draw the string at the final xy positions. This string may be contained within a text block.
	# parameters for the FB text block are blockWidth = 0, blockLines = 1, blockSpacing = 0, blockJustify = 'L', blockIndent = 0
	
	if blockWidth == 0: # draw the string as a single line as normal
		#g.drawRect(int(fieldX), int(fieldY), int(rectWidth), int(fontHeight)) # comment this out if rectangles around text not desired
		g.drawString(fieldData, int(fieldX), int(fieldY)) 
		
	else: # account for text block behavior
		# first adjust starting x and y positions depending on rotation 
		if fieldType == 'FO' and (rotation == 90 or rotation == 180):
			fieldY -= ((blockLines - 1) * fontHeight + blockLines * blockSpacing)
		elif fieldType == 'FT':
			fieldY -= ((blockLines - 1) * fontHeight + (blockLines - 1) * blockSpacing) # adjust by one blockSpacing 
		
		# also draw rectangle to denote the box which defines the FB text block, 
		if fieldType == 'FO':
			g.drawRect(int(fieldX), int(fieldY-0.75*fontHeight), int(blockWidth), int(blockLines*(fontHeight+blockSpacing))) # draw a starter rectangle to be filled
		else: #if fieldType == 'FT':
			g.drawRect(int(fieldX), int(fieldY-0.75*fontHeight-blockSpacing), int(blockWidth), int(blockLines*(fontHeight+blockSpacing))) # draw a starter rectangle to be filled
		
		# and get font scale factor to stretch font before fitting into FB text block
		sf = scaleFactor if scaleFactor != 0 else 1
		
		# split fieldData string into a list of words and remove any blank string characters from the word list
		wordList = fieldData.split(' ') # only space characters count as word separators (hyphens are treated like letters)
		for w in range(len(wordList)): 
			if wordList[w] == '':
				wordList.pop(w)
		#system.perspective.print(wordList)
		#system.perspective.print(str(blockWidth) + ', ' + str(blockLines))
		
		currentLine = 1 # the current line
		currentLineString = '' # the currently assembled string on the current line, initialized with blank string
		
		wordListIndices = range(len(wordList)) # need this to be editable from inside the for loop 
		for i in wordListIndices:
			word = wordList[i]
			if currentLine == 1:
				maxWidth = blockWidth
			else:
				maxWidth = blockWidth - blockIndent
			
			# measure what the width will be when adding the new word to see if there's enough room on the line to add the new word
			# if predictedWidth is ok, add a space and then the word (unless it's the very first word at index 0)
			predictedWidth = sf * g.getFontMetrics(font).getStringBounds(currentLineString + ' ' + word, g).getWidth() 
			
			if predictedWidth <= maxWidth: 
				currentLineString += ' ' + word if currentLineString != '' else word 
				
			else: # if there's not enough room, the current line is done and needs to be drawn on the image
				# before doing that, if the current line string is also blank and still cannot fit the next word, split up the word
				if currentLineString == '': 
					currentWidth = 0
					while currentWidth <= maxWidth:
						currentLineString += word[0] # add (transfer) next letter in word to cutLineString
						word = word[1:] # then remove that same letter from the word until maxWidth is reached
						
						# if the length of the word has not run out, the width of the currentLineString + the next letter can be updated
						# if the word is exactly short enough after transferring letters to fit in the block and there are no more letters, 
						# then forcefully exit the loop
						if len(word) > 0:
							currentWidth = sf * g.getFontMetrics(font).getStringBounds(currentLineString + word[0], g).getWidth() 
						else:
							currentWidth = maxWidth + 1 # exit loop
				
				# if there are remaining letters on the word, preserve and add them to the next position in the wordList
				# The length of wordList and wordListIndices will both increase by 1 and will take effect in the next cycle of this for loop
				# so that the next word to be evaluated is the remaining letters on this word.
				# CAUTION as this can send the script into an infinite loop if the insert position is exactly i (so it needs to be i+1)
				if len(word) > 0:
					wordList.insert(i+1, word) # DO NOT CHANGE
					wordListIndices.append(len(wordListIndices))
				
				# finally draw the current line string and then start a fresh line
				if blockJustify == 'R':
					stringWidth = g.getFontMetrics(font).getStringBounds(currentLineString, g).getWidth()
					g.drawString(currentLineString, int(fieldX + (blockWidth - stringWidth)), int(fieldY))
				elif blockIndent > 0 and currentLine > 1:
					g.drawString(currentLineString, int(fieldX + blockIndent), int(fieldY))
				else:
					g.drawString(currentLineString, int(fieldX), int(fieldY)) # draw the string using the current line string
				
				if currentLine < blockLines:
					fieldY += fontHeight + blockSpacing # increment the fieldY position to create a new line on the image for the next line
				currentLineString = '' 
				currentLine += 1
		
		# the last string is still waiting to be drawn, so need this extra script to draw it
		if blockJustify == 'R':
			stringWidth = g.getFontMetrics(font).getStringBounds(currentLineString, g).getWidth()
			g.drawString(currentLineString, int(fieldX + (blockWidth - stringWidth)), int(fieldY))
		elif blockIndent > 0 and currentLine > 1:
			g.drawString(currentLineString, int(fieldX + blockIndent), int(fieldY))
		else:
			g.drawString(currentLineString, int(fieldX), int(fieldY)) # draw the string using the current line string
		
		system.perspective.print('xy: ' + str(fieldX) + ', ' + str(fieldY))
	# dispose of Graphics2D object when done drawing the text. drawn graphic will persist on buffered image
	g.dispose() 
	
	return image



def drawBarcodePlaceholder(image, fieldData, bcX, bcY, justification, fieldType, bcWidth, bcHeight, orientation = 'N'):
	# barcode generation logic is too difficult to do without external libraries such as zxing or BinaryKits
	# a placeholder is used instead. draw a solid black box with white text to signify a barcode. 
	# not going to bother with supporting right justification, since the barcode length is unknown anyway.
	# also ignoring widthRatio since how that affects barcode width is unknown
	
	# initialize graphics element
	g = image.createGraphics()
	g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
	g.setComposite(AlphaComposite.Src)
	g.setColor(Color.BLACK)
	
	# based on rotation and field type, determine how the black rectangle should be drawn to match Labelary
	#bcLength = int(bcWidth * (11 * len(fieldData) + 46)) # this equation emulates a-z barcode length for code128 rendering by labelary
	if bcWidth <= 10:
		bcLength = int(bcWidth * 10 * len(fieldData)) # just use a basic equation for barcode length
		bcID = 'barcode: '
	else:
		bcHeight = 100 # bcWidth # change barcode Height if bc_square was found in the field dictionary
		bcLength = bcHeight # make a square for anything that is not a 1D barcode
		bcID = '2D code: '
	
	rotation = rotationCharToDeg(orientation)
	if rotation == 90:
		g.fillRect(bcX, bcY, bcHeight, bcLength)
		
	elif rotation == 180:
		if fieldType == 'FT':
			bcX -= bcLength
		g.fillRect(bcX, bcY, bcLength, bcHeight)
		
	elif rotation == 270:
		if fieldType == 'FT':
			bcX -= bcHeight
			bcY -= bcLength
		g.fillRect(bcX, bcY, bcHeight, bcLength)
		
	else: # if rotation == 0:
		if fieldType == 'FT':
			bcY -= bcHeight
		g.fillRect(bcX, bcY, bcLength, bcHeight)
	
	g.dispose()
	
	# now use the text block function to draw some white text onto the black rectangle
	blockLines = 4
	textHeight = int(bcHeight / blockLines)
	textWidth = 0 
	image = drawText(image, bcID + fieldData, int(bcX), int(bcY), justification, 'FO', textWidth, textHeight, '0', orientation, 'W', bcLength, blockLines, 0, 'L', 0)
	
	# did not want to bother with the interpretation line either, since it is complicated to move with the rectangle
#	# if the interpretation line needs to be printed, text also must go above or below the barcode
#	# again just guesstimating distances again
#	if printText == 'Y':
#		x = textX # int(bcX + 0.5 * bcHeight)
#		if printTextAbove == 'Y':
#			y = int(bcY - 1.2 * textHeight)
#			image = drawText(image, fieldData, x, y, justification, 'FO', textWidth, textHeight, 'A', orientation, 'B')
#		else:
#			y = int(bcY + bcHeight + 0.2 * textHeight)
#			image = drawText(image, fieldData, x, y, justification, 'FO', textWidth, textHeight, 'A', orientation, 'B')
	
	return image



def rotateImage(image, rotation = 0):
	# image is generated. now need to rotate the entire thing. get image dimensions.
	imageType = image.getType()
	widthDots = image.getWidth()
	heightDots = image.getHeight()
	
	# depending on rotation, create new resized buffered image, perform rotation of original image, and paste onto buffered image.
	if rotation == 90:
		rotatedImage = BufferedImage(heightDots, widthDots, imageType)
		g = rotatedImage.createGraphics()
		g.rotate(math.radians(rotation), heightDots / 2, heightDots / 2)
		g.drawImage(image, None, 0, 0)
		g.dispose()
	elif rotation == 180:
		rotatedImage = BufferedImage(widthDots, heightDots, imageType)
		g = rotatedImage.createGraphics()
		g.rotate(math.radians(rotation), widthDots / 2, heightDots / 2)
		g.drawImage(image, None, 0, 0)
		g.dispose()
	elif rotation == 270:
		rotatedImage = BufferedImage(heightDots, widthDots, imageType)
		g = rotatedImage.createGraphics()
		g.rotate(math.radians(rotation), widthDots / 2, widthDots / 2)
		g.drawImage(image, None, 0, 0)
		g.dispose()
	else:
		rotatedImage = image # if rotation is 0, just return the original image
	
	return rotatedImage



def convertImageToBase64(image):
	# write the image data to a ByteArrayOutputStream as PNG (lossless and good for simple graphics)
	outputStream = ByteArrayOutputStream()
	ImageIO.write(image, "png", outputStream)
	
	# Encode the PNG byte array to Base64 to work with Perspective Image component
	imageByteArray = outputStream.toByteArray()
	imageEncoded = Base64.getEncoder().encodeToString(imageByteArray) 
	labelImageString = "data:imagef;base64,%s"%imageEncoded
	
	# Return the Base64 encoded string
	return labelImageString










