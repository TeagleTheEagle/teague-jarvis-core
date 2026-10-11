// Dashboard world map (static/world-map.js): the hand-typed outlines put land and sea in the right places, and the
// day and night sides follow the clock.
const assert=require('node:assert/strict');
const map=require('./static/world-map.js');
const land={Paris:[2.35,48.85],Moscow:[37.6,55.75],Delhi:[77.2,28.6],Beijing:[116.4,39.9],'Alice Springs':[133.9,-23.7],Nairobi:[36.8,-1.3],Kinshasa:[15.3,-4.3],
  Denver:[-105,39.7],Winnipeg:[-97.1,49.9],'Mexico City':[-99.1,19.4],Brasilia:[-47.9,-15.8],Bogota:[-74.1,4.7],Madrid:[-3.7,40.4],Riyadh:[46.7,24.7],Novosibirsk:[82.9,55],
  Ankara:[32.9,39.9],Rome:[12.5,42.2],Nuuk:[-49,66],Birmingham:[-1.9,52.5],Nagano:[138.2,36.6]};
for(const [name,[lon,lat]] of Object.entries(land))assert.equal(map.isLand(lon,lat),true,name+' should be land');
const sea={'mid Pacific':[-150,0],'north Atlantic':[-35,30],'south Atlantic':[-15,-25],'Indian Ocean':[75,-20],'Black Sea':[34,43.2],'Caspian Sea':[51,41.5],
  'Hudson Bay':[-86,59],'Gulf of Mexico':[-90,25],Mediterranean:[18,35],'Bay of Bengal':[88,15],'Arabian Sea':[64,15],'Tasman Sea':[160,-38],
  'Gulf of Carpentaria':[139.5,-14.5],'Persian Gulf':[51.5,27],'Baltic Sea':[19.5,57.5],'Sea of Japan':[135,40],'South China Sea':[114,14],'North Sea':[3,56],'Bay of Biscay':[-5,45.5]};
for(const [name,[lon,lat]] of Object.entries(sea))assert.equal(map.isLand(lon,lat),false,name+' should be water');
// Every listed time-zone city sits on or beside land (within about two degrees: the outlines are coarse).
for(const zone of ['Australia/Sydney','Australia/Perth','Europe/London','America/New_York','Asia/Tokyo','Africa/Johannesburg','America/Sao_Paulo','Asia/Kolkata','Pacific/Auckland']){
  const [lon,lat]=map.zonePoint(zone);let near=false;
  for(const dx of [0,-2,2])for(const dy of [0,-2,2])if(map.isLand(lon+dx,lat+dy))near=true;
  assert.ok(near,zone+' should be near land');
}
assert.equal(map.zonePoint('Etc/UTC'),null,'an unlisted zone has no marker');
// Sun: overhead near the Tropic of Cancer at Greenwich at noon UTC on the June solstice, near the Tropic of Capricorn
// on the date line at midnight UTC on the December solstice, near the equator at the March equinox.
let s=map.sun(new Date(Date.UTC(2026,5,21,12)));assert.ok(Math.abs(s.lat-23.44)<0.4&&Math.abs(s.lon)<2,JSON.stringify(s));
s=map.sun(new Date(Date.UTC(2026,11,21,0)));assert.ok(Math.abs(s.lat+23.44)<0.4&&180-Math.abs(s.lon)<2,JSON.stringify(s));
s=map.sun(new Date(Date.UTC(2026,2,20,12)));assert.ok(Math.abs(s.lat)<1.2,JSON.stringify(s));
// Day and night: at noon UTC in June London is lit and Sydney is dark; twelve hours later the other way round.
s=map.sun(new Date(Date.UTC(2026,5,21,12)));assert.equal(map.daylight(-0.1,51.5,s),true);assert.equal(map.daylight(151.2,-33.9,s),false);
s=map.sun(new Date(Date.UTC(2026,5,22,2)));assert.equal(map.daylight(151.2,-33.9,s),true);assert.equal(map.daylight(-74,40.7,s),false);
// Polar day: the far north is lit around the clock in June and dark in December.
s=map.sun(new Date(Date.UTC(2026,5,21,0)));assert.equal(map.daylight(20,75,s),true);
s=map.sun(new Date(Date.UTC(2026,11,21,12)));assert.equal(map.daylight(20,75,s),false);
// Projection keeps a point inside the box.
const [x,y]=map.project(151.2,-33.9,960,346);assert.ok(x>880&&x<890&&y>290&&y<305,x+','+y);
console.log('World map land, sea, sun position and day/night checks passed.');
