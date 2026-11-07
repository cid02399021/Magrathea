"""Read-only audit of the conditional pure-Fe/water/prescribed-HHe pilot."""
import argparse,bisect,csv,json,math,struct
from pathlib import Path
from check_tp_model import require,finite_tree,close
ME=5.9722e27;RE=6.3781e8
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def table_data(path):
 lines=Path(path).read_text().splitlines()
 rows=[list(map(float,s.split())) for s in lines[1:] if s.strip()]
 ts=sorted(set(x[1] for x in rows));ps=sorted(set(x[0] for x in rows))
 require(len(rows)==len(ts)*len(ps),'table grid')
 # Existing C++ loads every subsequent axis value through float, including T0 rewritten by next P block.
 pp=[ps[0]]+[f32(x) for x in ps[1:]];tt=[f32(x) for x in ts]
 rho={(p,t):v for p,t,v,*_ in rows}
 def value(P,T):
  P/=1e10;require(pp[0]<=P<=pp[-1] and tt[0]<=T<=tt[-1],'independent HHe table domain')
  i=min(max(bisect.bisect_right(pp,P)-1,0),len(pp)-2);j=min(max(bisect.bisect_right(tt,T)-1,0),len(tt)-2)
  a=(P-pp[i])/(pp[i+1]-pp[i]);b=(T-tt[j])/(tt[j+1]-tt[j])
  return (1-a)*((1-b)*rho[ps[i],ts[j]]+b*rho[ps[i],ts[j+1]])+a*((1-b)*rho[ps[i+1],ts[j]]+b*rho[ps[i+1],ts[j+1]])
 return value
def verify(diag,config,profile,table):
 d=json.loads(Path(diag).read_text());c=json.loads(Path(config).read_text());finite_tree(d);finite_tree(c)
 require(d['schema_version']==2 and d['status']=='success','schema/status')
 require(d['eos_selector']=='gas_hhe_prescribed' and d['helium_mass_fraction']==.275,'HHe identity')
 require('mmol' not in d and 'n' not in d,'misleading ideal EOS constants')
 require(d['ode_status']==0 and not d['corrected_fit'] and d['strict_table_audit'],'numerical status/strict audit')
 fractions=c['fractions'];require(len(fractions)==4 and fractions[1]==0 and min(fractions)>=0 and abs(sum(fractions)-1)<1e-14,'composition')
 mass=c['mass_earth']*ME
 require(abs(d['total_mass_g']/mass-1)<1e-10,'mass')
 require(abs(d['gas_base_mass']/mass-(1-fractions[3]))<1e-10,'gas interval')
 raw=d['fit_raw']
 for key,a,b in [('radius','Ri','Ro'),('pressure','Pi','Po'),('temperature','Ti','To')]:
  require(raw[a]>0 and raw[b]>0,'fit positivity')
  v=(raw[a]-raw[b])/(raw[a]+raw[b]);require(close(d['fit_residual'][key],v,1e-14) and abs(v)<=1e-6,'fit '+key)
 points=list(csv.reader(Path(profile).open()));require(points.pop(0)==['P_bar','T_K'],'TP header')
 points=[(float(p)*1e6,float(t)) for p,t in points];pp=[p for p,t in points]
 def temp(p):
  require(pp[0]<=p<=pp[-1],'external TP coverage')
  i=min(max(bisect.bisect_right(pp,p)-1,0),len(pp)-2);p0,t0=points[i];p1,t1=points[i+1]
  return t0+(t1-t0)*math.log(p/p0)/math.log(p1/p0)
 require(close(d['outer_pressure_cgs'],c['surface_pressure_cgs'],1e-12) and close(d['outer_temperature_K'],temp(c['surface_pressure_cgs']),1e-12),'surface')
 require(pp[0]<=d['gas_pressure_min']<=d['gas_pressure_max']<=pp[-1],'trial TP coverage')
 require(0<=d['max_pre_projection_relative']<=1e-7,'raw TP mismatch')
 require(0<=d['max_knot_pressure_projection_relative']<=128*2.220446049250313e-16,'knot roundoff')
 rho_hhe=table_data(table);bounds=[];v=0.
 for f in fractions:bounds.append((v*mass,(v+f)*mass));v+=f
 allowed_fe={'Fe_hcp','Fe_liquid','Fe_liquid2'}
 allowed_water={'Water_SF','Water_Brown','Water_IAPWS','Water_Vap_IAPWS','Water_sc_Mazevet','IceIh_SF','IceII_SF','IceIII_SF','IceV_SF','IceVI_SF','IceVII_Bezacier','IceVII_Fei','IceX','vdW_H2O','vdW_H2O_iso','vdW_H2O_lo','vdW_H2O_hi'}
 allowed=[allowed_fe,set(),allowed_water,{'Gas_hhe'}]
 rows=d['layer_rows'];require(len(rows)>10 and len(rows)==d['accepted_model_rows'],'complete accepted profile rows')
 require(rows[0]['mass_g']==0 and rows[0]['radius_cm']==0,'center anchor missing')
 maxrho=maxgas=maxT=0.;seen={};boundary=0;previous_m=previous_r=-1.
 slack=64*2.220446049250313e-16*mass
 for row in rows:
  m,r,p,t,rho=[row[k] for k in ('mass_g','radius_cm','pressure_cgs','temperature_K','density_g_cm3')]
  require(m>=previous_m-slack and r>=previous_r and 0<=m<=mass+slack and min(r,p,t,rho)>=0 and min(p,t,rho)>0,'accepted row order/state')
  previous_m,previous_r=m,r;actual=row['actual_eos_id'];seen[actual]=seen.get(actual,0)+1
  require(row['table_domain_contains'] is True,'accepted EOS outside numerical table bounds')
  newrho=row['reevaluated_density_g_cm3'];require(newrho>0,'native density positive');maxrho=max(maxrho,abs(rho-newrho)/newrho)
  candidates=[]
  require(len(row['expected_eos_by_slot'])==4,'component diagnostics')
  for j,(lo,hi) in enumerate(bounds):
   e=row['expected_eos_by_slot'][j];require(e['slot']==j and close(e['mass_ME'],fractions[j]*c['mass_earth'],1e-12),'component mass identity')
   if fractions[j]==0:require(e['exact_eos_id']=='' and e['nearby_eos_ids']==[],'zero component skipped')
   elif lo-slack<=m<=hi+slack:candidates.append(e)
  matches=[e for e in candidates if actual in allowed[e['slot']] and (actual==e['exact_eos_id'] or actual in e['nearby_eos_ids'])]
  require(matches,'wrong material or phase pointer '+actual+' at mass '+str(m))
  if not any(actual==e['exact_eos_id'] for e in matches):boundary+=1
  if actual=='Gas_hhe':
   expected=temp(p);maxT=max(maxT,abs(t-expected)/max(1,abs(expected)))
   maxgas=max(maxgas,abs(rho-rho_hhe(p,expected))/rho_hhe(p,expected))
  elif actual in allowed_fe:
   P=p/1e10
   expected='Fe_hcp' if not(t>12.8*P+2424 and t>13.7*P+2328) else ('Fe_liquid2' if P<.0001 or P<(t-3020)/110 or t>10000 else 'Fe_liquid')
   require(actual==expected or any(actual in e['nearby_eos_ids'] for e in matches),'independent Fe branch')
 require(any(k in allowed_fe for k in seen),'iron layer missing')
 require(fractions[2]==0 or any(k in allowed_water for k in seen),'water layer missing')
 require(seen.get('Gas_hhe',0)==len(d['gas_rows']),'gas row coverage differs')
 require(close(rows[-1]['mass_g'],mass,1e-10) and close(rows[-1]['radius_cm'],d['total_radius_cm'],1e-12),'outer anchors')
 require(close(rows[-1]['pressure_cgs'],c['surface_pressure_cgs'],1e-12),'surface pressure')
 require(maxrho<=1e-7 and maxgas<=1e-10 and maxT<=1e-10,'stored density/temperature consistency '+str((maxrho,maxgas,maxT)))
 for key in ('density_audit_counts','gradient_audit_counts'):
  require(all(v>=0 and k in allowed_fe|allowed_water|{'Gas_hhe'} for k,v in d[key].items() if v),'unexpected EOS queries '+key)
 require(d['gradient_audit_counts'].get('Gas_hhe',0)==0,'gas adiabat called under prescribedTP')
 return {'status':'PASS_CONDITIONAL_NUMERICAL','radius_earth':d['total_radius_cm']/RE,'layer_rows':len(rows),'gas_rows':seen.get('Gas_hhe',0),'phase_counts':seen,'local_phase_boundary_rows':boundary,'max_native_density_relative':maxrho,'max_independent_hhe_density_relative':maxgas,'max_external_temperature_relative':maxT,'rejected_numerical_table_trials':d['rejected_table_queries'],'physical_acceptance':False}
if __name__=='__main__':
 a=argparse.ArgumentParser()
 for k in ('diagnostics','config','profile','table'):a.add_argument('--'+k,required=True)
 x=a.parse_args()
 try:print(json.dumps(verify(x.diagnostics,x.config,x.profile,x.table),indent=2))
 except Exception as e:a.exit(1,'FAIL '+str(e)+'\n')
