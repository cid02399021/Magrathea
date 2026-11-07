// Synthetic constructor regression. No observed planet fit or grid.
#include "hydro.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
double rho_eps_rel=1e-11,T_eps_rel=1e-11,ode_eps_rel0=1e-7,ode_eps_rel1=1e-10,ode_eps_rel2=1e-10,R_eps_rel=2e-5,P_eps_rel=1e-10,fit_eps_rel=1e-4;
int fit_iter=0,count_shoot=0,count_step=0;bool verbose=false;
EOS *inner_fixture=nullptr,*outer_fixture=nullptr;
double inner_density(double p,double t,double){return 8.+.001*t+1e-14*p;}
double outer_density(double p,double t,double){return 2.+.002*t+1e-14*p;}
double fixture_gradient(double,double,double&){return 1e-11;}
EOS* inner_phase(double,double){return inner_fixture;}
EOS* outer_phase(double,double){return outer_fixture;}
int main(){try{
 gsl_set_error_handler_off();
 inner_fixture=new EOS("SYNTHETIC_INNER",inner_density);
 outer_fixture=new EOS("SYNTHETIC_OUTER",outer_density);
 inner_fixture->modify_dTdP(fixture_gradient);outer_fixture->modify_dTdP(fixture_gradient);
 PhaseDgm a("fixture_core",inner_phase),b("fixture_water",outer_phase);
 std::vector<PhaseDgm> comp={a,a,b,b};
 std::vector<double> masses={.1,0,.2,0},gaps={0,0,0,300};
 double ri,pi,ti,ro,po,to;
 hydro h(2*RE,2e13,3000,comp,masses,gaps,false,.15*ME,1e-5,1e5,ri,pi,ti,ro,po,to);
 if(h.getsize()<10)throw std::runtime_error("synthetic constructor has no usable profile");
 int boundary=0;double maximum=0;
 for(int i=0;i<h.getsize();++i){
  EOS* phase=const_cast<EOS*>(h.getphase(i));
  double expected=phase->density(h.getP(i),h.getT(i),-1);
  double error=std::abs(h.getrho(i)-expected)/expected;maximum=std::max(maximum,error);
  if(i&&h.getM(i)==h.getM(i-1)&&h.getphase(i)!=h.getphase(i-1))++boundary;
 }
 if(!boundary)throw std::runtime_error("synthetic material interface not exercised");
 std::cout<<"SYNTHETIC_FIXTURE interface rows="<<boundary<<" max_density_relative="<<maximum<<"\n";
 if(maximum>1e-10)throw std::runtime_error("stored material-interface density uses stale temperature");
 std::cout<<"INTERFACE_TEMPERATURE_PASS\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
