
import FreeCAD as App
from FreeCAD import Placement, Vector, Rotation, ActiveDocument
import Part

import math

def trig(x, y, angle, distance):
	theta = math.radians(angle+90)
	x = x + (math.sin(theta) * distance)
	y = y + (math.cos(theta) * distance)
	return (x,y)


def getEmptyLayers():
	layers = {}
	layers['bases'] = []
	layers['inners'] = []
	layers['outers'] = []
	return layers


def extrudeBase (shape, height, addTo):
	extrude = App.activeDocument().addObject('Part::Extrusion','ExtrudedBaseSketch')
	extrude.Base = shape
	extrude.Solid = True
	extrude.LengthFwd = height

	# stop rendering the shape as it doesn't hide properly
	shape.Visibility = False

	addTo['bases'].append(extrude)


def addCutterPart (doc, x, y, size, lineWidth, addTo, baseHeight=2):

	# 1st baseHeight to add to it's own base
	# 2nd baseHeight to get through the holder
	# 1/4" = 6.35mm which is thickest usual clay
	cutterHeight = baseHeight + baseHeight + 6.35 

	outerSize = size
	outerSupportSize = size + 0.5
	outerSupportSize2 = size + 0.25
	innerSize = size-(lineWidth*2)

	outer = doc.addObject("Part::Cylinder","Outer")
	outer.Radius = str(outerSize) + ' mm'
	outer.Height = str(cutterHeight) + ' mm'

	outerSupport1 = doc.addObject("Part::Cylinder","OuterSupportLow")
	outerSupport1.Radius = str(outerSupportSize) + ' mm'
	outerSupport1.Height = str(baseHeight+1.0) + ' mm'

	outerSupport2 = doc.addObject("Part::Cylinder","OuterSupportHigh")
	outerSupport2.Radius = str(outerSupportSize2) + ' mm'
	outerSupport2.Height = str(baseHeight+2.0) + ' mm'

	inner = doc.addObject("Part::Cylinder","Inner")
	inner.Radius = str(innerSize) + ' mm'
	inner.Height = '20 mm'

	placement = Placement(Vector(x,y,0),Rotation(Vector(0,0,1),1))

	inner.Placement = placement
	outer.Placement = placement
	outerSupport1.Placement = placement
	outerSupport2.Placement = placement

	addTo['inners'].append(inner)
	addTo['outers'].append(outer)
	addTo['outers'].append(outerSupport1)
	addTo['outers'].append(outerSupport2)


def addPusherPart (doc, x, y, size, lineWidth, addTo, baseHeight):

	# 1st & 2nd baseHeight are the height on the cutter and holder
	# 3rd baseHeight to get beyond pusher base
	# 1/4" = 6.35mm which is thickest usual clay
	# Add an extra margin
	pusherHeight = baseHeight + baseHeight + baseHeight + 6.35 + 0.75 

	poleSize = size - (lineWidth*2.5)

	pole = doc.addObject("Part::Cylinder","Pusher")
	pole.Radius = '{} mm'.format(poleSize)
	pole.Height = '{} mm'.format(pusherHeight)

	placement = Placement(Vector(x,y,0),Rotation(Vector(0,0,1),1))

	pole.Placement = placement

	addTo['outers'].append(pole)


def addBaseHolePart (doc, x, y, size, lineWidth, addTo):

	innerSize = size + 0.5

	inner = doc.addObject("Part::Cylinder","InnerBaseHole")
	inner.Radius = '{} mm'.format(innerSize)
	inner.Height = '5 mm'

	inner.Placement = Placement(Vector(x,y,0),Rotation(Vector(0,0,1),1))

	addTo['inners'].append(inner)


def appendPointsToSketch(sketch, points):

	countPoints = len(points)

	geoList = []
	for i in range(countPoints):
		j = i+1
		if j >= countPoints:
			j = 0

		(x1, y1) = points[i]
		(x2, y2) = points[j]
		pt1 = App.Vector(x1,y1)
		pt2 = App.Vector(x2,y2)
		line = Part.LineSegment(pt1,pt2)
		geoList.append(line)

	sketch.addGeometry(geoList,False)


def createPerpendicularBase(x,y,w,h,extrudeHeight,addTo):
	sketch = App.activeDocument().addObject('Sketcher::SketchObject', 'BaseSketch')

	nearL = (x,y)
	nearR = (x+w,y) 
	farL = (x,y+h)
	farR = (x+w,y+h)

	points = [nearL, farL, farR, nearR]
	appendPointsToSketch(sketch, points)

	extrude = App.activeDocument().addObject('Part::Extrusion','PerpBase')
	extrude.Base = sketch
	extrude.Solid = True
	extrude.LengthFwd = extrudeHeight

	# stop rendering the sketch as it doesn't hide properly
	sketch.Visibility = False

	addTo['bases'].append(extrude)


def groupHolesIntoStencil(addTo, name):

	# group the shapes
	if len(addTo['bases']) > 1:
		baseGroup = App.ActiveDocument.addObject("Part::MultiFuse", "BaseFuse")
		baseGroup.Shapes = addTo['bases']
		addTo['outers'].append( baseGroup )
	elif len(addTo['bases']) == 1:
		addTo['outers'].append( addTo['bases'][0] )


	if len(addTo['outers']) > 1:
		outerGroup = App.ActiveDocument.addObject("Part::MultiFuse", "OuterFuse")
		outerGroup.Shapes = addTo['outers']
	elif len(addTo['outers']) == 1:
		outerGroup = addTo['outers'][0]
	
	if len(addTo['inners']) > 0:
		innerGroup = App.ActiveDocument.addObject("Part::MultiFuse", "InnerFuse")
		innerGroup.Shapes = addTo['inners']

		# Cut the inner from the outer into the final stencil
		stencil = App.activeDocument().addObject("Part::Cut",name)
		stencil.Base = outerGroup
		stencil.Tool = innerGroup
	else:
		outerGroup.Label = name	

	
