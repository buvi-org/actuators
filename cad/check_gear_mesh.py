import math,json
from involute_geometry import profile,COUNTS,CENTER,ALPHA,M
from shapely.affinity import rotate,translate
p={n:profile(n)[1] for n in COUNTS}
worst=0;outside=0
for k in range(720):
 sunang=18*math.pi*k/719;carrier=sunang/9
 sun=rotate(p['sun'],sunang,origin=(0,0),use_radians=True)
 hole=rotate(p['ring'],math.pi/160,origin=(0,0),use_radians=True)
 planets=[]
 for i in range(3):
  a=carrier+i*2*math.pi/3
  rot=a+math.pi+math.pi/70+20/70*(a-sunang)
  planet=translate(rotate(p['planet'],rot,origin=(0,0),use_radians=True),CENTER*math.cos(a),CENTER*math.sin(a))
  worst=max(worst,sun.intersection(planet).area)
  outside=max(outside,planet.difference(hole).area)
  planets.append(planet)
 for i in range(3):worst=max(worst,planets[i].intersection(planets[(i+1)%3]).area)
assert worst<1e-8 and outside<1e-8
rp={n:M*z/2 for n,z in COUNTS.items()};rb={n:r*math.cos(ALPHA) for n,r in rp.items()}
ra={n:r+(-M if n=='ring' else M) for n,r in rp.items()}
path=lambda n:math.sqrt(ra[n]**2-rb[n]**2)
bp=math.pi*M*math.cos(ALPHA)
report={'ratio':1+COUNTS['ring']/COUNTS['sun'],'ring_fixed':True,'sun_input_carrier_output':True,'sun_planet_center_mm':(rp['sun']+rp['planet']),'planet_ring_center_mm':rp['ring']-rp['planet'],'equal_spacing_integer':(COUNTS['sun']+COUNTS['ring'])/3,'no_undercut_min_teeth':2/math.sin(ALPHA)**2,'external_contact_ratio':(path('sun')+path('planet')-CENTER*math.sin(ALPHA))/bp,'internal_contact_ratio':(path('planet')-path('ring')+CENTER*math.sin(ALPHA))/bp,'pair_circular_backlash_mm':.02,'sampled_carrier_revolutions':1,'sample_positions':720,'maximum_overlap_mm2':worst,'planet_outside_ring_space_mm2':outside,'scope':'Sampled planar CAD-boundary check, not loaded tooth contact analysis or proof at all intermediate positions.'}
assert report['ratio']==9 and report['equal_spacing_integer'].is_integer()
assert report['external_contact_ratio']>1 and report['internal_contact_ratio']>1
from pathlib import Path
Path('public/design/gear-mesh-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
