#!/usr/bin/python
#
# cake-maker is a script for producing 'cake' maps for
# OpenStreetMap mapping parties.
#
# See README for more information
#
#  usage:   cake_maker.py cakefile.osm   
#  Output files are generated in the current working directory
#  with filenames 'image.1.[png|svg] image.2.[png|svg] ...
#
import mapnik
import xml.parsers.expat
import xml.sax
import sys, os
import cairo
import math
from shapely.geometry import Polygon
from shapely.geometry import Point


class Node:
    def __init__(self):
        self.id_no=None
        self.lat=None
        self.lon=None
    
class Way:
    def __init__(self):
        self.id_no=None
        self.nodes=[]
    
    def getBounds(self):
        pointArray=[]
        for n in self.nodes:
            #p = Point(float(n.lat),float(n.lon))
            p = (float(n.lon),float(n.lat))
            pointArray.append(p)
        if len(pointArray) > 4:
            poly = Polygon(pointArray)
            return poly.bounds
        return None

##
# Builds up a list of cake slices.
#
##
class SliceList:

    def startElement(self,name,attributes):
        if name=='node':
            newNode=Node()
            newNode.id_no=attributes['id']
            newNode.lat=attributes['lat']
            newNode.lon=attributes['lon']
            self.nodeList[newNode.id_no]=newNode
        elif name=='way':
            self.current_way = Way()
            self.current_way.id_no=attributes['id']
        elif name=='nd' :
            node=self.nodeList[attributes['ref']]
            self.current_way.nodes.append(node)
        
 

    def endElement(self,name):
        if name=='way':
            self.wayList[self.current_way.id_no]=self.current_way

    def __init__(self,file):
        self.nodeList={}
        self.wayList={}
        parser =xml.parsers.expat.ParserCreate()
        parser.StartElementHandler=self.startElement
        parser.EndElementHandler=self.endElement
        parser.ParseFile(file)
        

def renderPage(ll,file):

        z = 2
        #imgx = 987 * z
        #imgy = 801 * z
        imgx = int(987 * z )
        imgy = int(987 * z *0.77 )
        m = mapnik.Map(imgx,imgy)
        mapnik.load_map(m,mapfile)
        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        c0 = prj.forward(mapnik.Coord(ll[0],ll[1]))
        c1 = prj.forward(mapnik.Coord(ll[2],ll[3]))
        if hasattr(mapnik,'mapnik_version') and mapnik.mapnik_version() >= 800:
            bbox = mapnik.Box2d(c0.x,c0.y,c1.x,c1.y)
        else:
            bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
            m.zoom_to_box(bbox)
            im = mapnik.Image(imgx,imgy)
            mapnik.render(m, im)
            view = im.view(0,0,imgx,imgy) # x,y,width,height
            map_uri=file + '.png'
            view.save(map_uri,'png')
        
        
            file=open(file+'.svg' ,'w')
            surface=cairo.SVGSurface(file.name,imgx,imgy)
            mapnik.render(m,surface)
            #c = cairo.Context(surface)
            #c.move_to(50,50)
            #c.show_text('testing')

            surface.finish();

if __name__ == "__main__":
    try:
        mapfile = os.environ['MAPNIK_MAP_FILE']
    except KeyError:
        mapfile = "osm.xml"
    
    cake_file=sys.argv[1]
    sliceList=SliceList(open(cake_file,'r'))
    idx=1
    #---------------------------------------------------
    #  Change this to the bounding box you want
    #
    ll = (-79.38216, 43.66565, -79.35656, 43.63584)
    #---------------------------------------------------
    renderPage(ll,'image0')
    for w in sliceList.wayList:
        ll1 = sliceList.wayList[w].getBounds()        
        if ll1==None:
            continue
        #londiff=abs(ll1[2]-ll1[0])*.10
        #latdiff=abs(ll1[3]-ll1[1])*.10
        londiff=0.0003
        latdiff=0.0003
        ll=(ll1[0]-londiff,ll1[1]-latdiff,
            ll1[2]+londiff,ll1[3]+latdiff)
        map_uri = "image." + str(idx)    
        renderPage(ll,map_uri)
        idx=idx+1
