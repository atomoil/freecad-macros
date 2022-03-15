
import FreeCAD as App
from FreeCAD import Placement, Vector, Rotation, ActiveDocument
import Part

import math

def trig(x, y, angle, distance):
	theta = math.radians(angle+90)
	x = x + (math.sin(theta) * distance)
	y = y + (math.cos(theta) * distance)
	return (x,y)


def addCutterPart (doc, x, y, size, lineWidth, addTo):

	# lineWidth = 0.1
	# size = 5

	cutterHeight = baseHeight + 12

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


def addBaseHolePart (doc, x, y, size, lineWidth, addTo):

	innerSize = size + 0.5

	inner = doc.addObject("Part::Cylinder","InnerBaseHole")
	inner.Radius = str(innerSize) + ' mm'
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

	innerGroup = App.ActiveDocument.addObject("Part::MultiFuse", "InnerFuse")
	innerGroup.Shapes = addTo['inners']

	if len(addTo['outers']) > 1:
		outerGroup = App.ActiveDocument.addObject("Part::MultiFuse", "OuterFuse")
		outerGroup.Shapes = addTo['outers']
	elif len(addTo['outers']) == 1:
		outerGroup = addTo['outers'][0]

	# Cut the inner from the outer into the final stencil
	stencil = App.activeDocument().addObject("Part::Cut",name)
	stencil.Base = outerGroup
	stencil.Tool = innerGroup