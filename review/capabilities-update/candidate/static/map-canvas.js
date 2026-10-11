'use strict';
(()=>{
  let map,layer,line,markers=[],latest=0,loading;
  const tell=(type,message)=>parent.postMessage({type,message},location.origin);
  const styles=[{elementType:'geometry',stylers:[{color:'#182630'}]},{elementType:'labels.text.stroke',stylers:[{color:'#182630'}]},{elementType:'labels.text.fill',stylers:[{color:'#abbfc9'}]},{featureType:'road',elementType:'geometry',stylers:[{color:'#344955'}]},{featureType:'road.highway',elementType:'geometry',stylers:[{color:'#4c6470'}]},{featureType:'water',elementType:'geometry',stylers:[{color:'#0a1722'}]},{featureType:'poi.park',elementType:'geometry',stylers:[{color:'#203b3b'}]},{featureType:'poi.business',stylers:[{visibility:'off'}]}];
  function load(key){
    if(loading)return loading;
    loading=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(Error('Map connection timed out.')),18000);
      window.gm_authFailure=()=>{clearTimeout(timer);tell('map-error','Custom map access was rejected. Enable Maps JavaScript API and Geocoding API for your existing browser key.');reject(Error('Custom map access was rejected.'));};
      window.jarvisMapLoaded=()=>{clearTimeout(timer);resolve();};
      const script=document.createElement('script');script.src='https://maps.googleapis.com/maps/api/js?'+new URLSearchParams({key,loading:'async',callback:'jarvisMapLoaded',libraries:'geometry',v:'quarterly'});script.async=true;script.onerror=()=>{clearTimeout(timer);reject(Error('Could not connect to Google Maps.'));};document.head.append(script);
    });return loading;
  }
  function reset(){line?.setMap(null);markers.forEach(marker=>marker.setMap(null));markers=[];}
  function marker(position,label){markers.push(new google.maps.Marker({map,position,label:{text:label,color:'#07161e',fontWeight:'700'},icon:{path:google.maps.SymbolPath.CIRCLE,scale:14,fillColor:'#76e1ed',fillOpacity:1,strokeColor:'#e6fcff',strokeWeight:2}}));}
  addEventListener('message',async event=>{
    if(event.origin!==location.origin||event.source!==parent||event.data?.type!=='show-map')return;
    const request=++latest,{key,place,polyline}=event.data;
    try{
      await load(key);if(request!==latest)return;
      if(!map){map=new google.maps.Map(document.getElementById('map'),{center:{lat:0,lng:0},zoom:2,styles,mapTypeControl:false,streetViewControl:false,fullscreenControl:true,gestureHandling:'cooperative'});layer=new google.maps.TrafficLayer();document.getElementById('traffic').onchange=e=>layer.setMap(e.target.checked?map:null);}
      reset();
      if(polyline){
        const path=google.maps.geometry.encoding.decodePath(polyline);if(!path.length)throw Error('No route geometry was returned.');
        line=new google.maps.Polyline({map,path,strokeColor:'#63deed',strokeOpacity:1,strokeWeight:6});const bounds=new google.maps.LatLngBounds();path.forEach(point=>bounds.extend(point));map.fitBounds(bounds,65);marker(path[0],'A');marker(path[path.length-1],'B');
      }else{
        const coordinates=/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/.exec(place||'');
        let position;
        if(coordinates)position={lat:Number(coordinates[1]),lng:Number(coordinates[2])};
        else{const result=await new google.maps.Geocoder().geocode({address:place});if(request!==latest)return;position=result.results[0]?.geometry.location;if(!position)throw Error('Address not found.');}
        map.setCenter(position);map.setZoom(14);marker(position,'A');
      }
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>{google.maps.event.removeListener(listener);reject(Error('Map tiles did not load.'));},12000);
        const listener=google.maps.event.addListenerOnce(map,'tilesloaded',()=>{clearTimeout(timer);resolve();});
      });
      if(request===latest)tell('map-success','JARVIS map · Google Maps data');
    }catch(error){if(request===latest)tell('map-error','Custom map unavailable. Check Maps JavaScript API and Geocoding API access on your browser key, or use the standard map.');}
  });
  tell('map-ready');
})();
