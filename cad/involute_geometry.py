"""Analytic involute candidate; manufacturing release still requires process and strength review."""
import math
import cadquery as cq
from shapely.geometry import Polygon
from scipy.optimize import brentq
M=.3
ALPHA=math.radians(20)
THINNING=.01 # mm circular tooth-thickness reduction PER gear; 0.02 mm pair backlash
COUNTS={'sun':20,'planet':70,'ring':160}
CENTER=13.5
ROOT_FILLET=.06

def polar(r,a):return cq.Vector(r*math.cos(a),r*math.sin(a),0)
def inv_t(t):return t-math.atan(t)
def profile(name):
 z=COUNTS[name];rp=M*z/2;rb=rp*math.cos(ALPHA);internal=name=='ring'
 low=rp-M if internal else rp-1.25*M
 high=rp+1.25*M if internal else rp+M
 half=math.pi/(2*z)+(THINNING if internal else -THINNING)/(2*rp)
 def theta(r):
  t=math.sqrt(max(0,(r/rb)**2-1));return half+math.tan(ALPHA)-ALPHA-inv_t(t)
 first=max(low,rb);t0=math.sqrt(max(0,(first/rb)**2-1));t1=math.sqrt((high/rb)**2-1)
 edges=[];max_error=0
 def arc(radius,a,b):
  return cq.Edge.makeThreePointArc(polar(radius,a),polar(radius,(a+b)/2),polar(radius,b))
 def basepoint(t):return polar(rb*math.sqrt(1+t*t),-(half+math.tan(ALPHA)-ALPHA-inv_t(t)))
 def fillet_center(t):
  r=rb*math.sqrt(1+t*t);ang=-(half+math.tan(ALPHA)-ALPHA-inv_t(t))
  dr=rb*t/math.sqrt(1+t*t);da=t*t/(1+t*t)
  dx=dr*math.cos(ang)-r*math.sin(ang)*da;dy=dr*math.sin(ang)+r*math.cos(ang)*da
  norm=math.hypot(dx,dy);sign=-1 if internal else 1
  return basepoint(t)+cq.Vector(sign*ROOT_FILLET*dy/norm,-sign*ROOT_FILLET*dx/norm,0)
 curved_root=internal or low>=rb
 if curved_root:
  target=high-ROOT_FILLET if internal else low+ROOT_FILLET
  tf=brentq(lambda t:fillet_center(t).Length-target,max(t0,1e-8),t1)
  fc=fillet_center(tf);fp=basepoint(tf);fq=fc.normalized()*(high if internal else low)
  if internal:t1=tf
  else:t0=tf
 def transform(p,c,side):
  x,y=p.x, p.y if side==-1 else -p.y
  return cq.Vector(x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c),0)
 def blend(c,side,reverse=False):
  q,p,center=[transform(v,c,side) for v in (fq,fp,fc)]
  mid=center+((q-center).normalized()+(p-center).normalized()).normalized()*ROOT_FILLET
  return cq.Edge.makeThreePointArc(p,mid,q) if reverse else cq.Edge.makeThreePointArc(q,mid,p)
 for k in range(z):
  c=k*2*math.pi/z
  if curved_root and not internal:edges.append(blend(c,-1))
  elif low<rb:edges.append(cq.Edge.makeLine(polar(low,c-theta(first)),polar(first,c-theta(first))))
  ts=[t0+(t1-t0)*j/48 for j in range(49)]
  def point(t,side):return polar(rb*math.sqrt(1+t*t),c+side*(half+math.tan(ALPHA)-ALPHA-inv_t(t)))
  flank=cq.Edge.makeSpline([point(t,-1) for t in ts],parameters=ts,tol=1e-9)
  if k==0:
   for j in range(193):
    t=t0+(t1-t0)*j/192
    max_error=max(max_error,(flank.positionAt(t,'parameter')-point(t,-1)).Length)
  edges.append(flank)
  if internal:
   edges.append(blend(c,-1,True))
   qa=math.atan2(fq.y,fq.x)
   edges.append(arc(high,c+qa,c-qa))
   edges.append(blend(c,1))
  else:edges.append(arc(high,c-theta(high),c+theta(high)))
  edges.append(cq.Edge.makeSpline([point(t,1) for t in reversed(ts)],parameters=[t1-t for t in reversed(ts)],tol=1e-9))
  if curved_root and not internal:
   edges.append(blend(c,1,True));root_angle=-math.atan2(fq.y,fq.x)
  else:
   root_angle=theta(first)
   if low<rb:edges.append(cq.Edge.makeLine(polar(first,c+root_angle),polar(low,c+root_angle)))
  edges.append(arc(low,c+root_angle,(k+1)*2*math.pi/z-root_angle))
 w=cq.Wire.assembleEdges(edges)
 f=cq.Face.makeFromWires(w)
 # Explicit circular root fillets; not claimed to be a hob/shaper-generated trochoid.
 radius=high if internal else low
 vertices=[v for v in f.Vertices() if abs(math.hypot(v.X,v.Y)-radius)<1e-6]
 if not curved_root:f=f.fillet2D(ROOT_FILLET,vertices)
 assert f.isValid()
 w=f.outerWire()
 # Sample the actual CAD boundary for independent planar mesh/collision checks.
 sampled=[]
 from OCP.BRepTools import BRepTools_WireExplorer
 from OCP.TopAbs import TopAbs_REVERSED
 explorer=BRepTools_WireExplorer(w.wrapped)
 while explorer.More():
  edge=cq.Edge(explorer.Current());pts=edge.sample(20 if edge.geomType()!='LINE' else 2)[0]
  if explorer.Current().Orientation()==TopAbs_REVERSED:pts=list(reversed(pts))
  sampled.extend([[p.x,p.y] for p in pts[:-1]])
  explorer.Next()
 poly=Polygon(sampled)
 assert poly.is_valid, name
 assert max_error<.000001,(name,max_error)
 return w,poly,{'teeth':z,'module_mm':M,'pressure_angle_deg':20,'pitch_diameter_mm':2*rp,'base_diameter_mm':2*rb,'root_diameter_mm':2*(high if internal else low),'tip_diameter_mm':2*(low if internal else high),'root_fillet_mm':ROOT_FILLET,'tooth_thinning_mm':THINNING,'sampled_spline_error_mm':max_error}

if __name__=='__main__':
 for name in COUNTS:
  w,p,info=profile(name);print(name,info,flush=True)
