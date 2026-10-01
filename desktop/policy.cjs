function trusted(url,origin){try{return new URL(url).origin===origin;}catch{return false;}}
function external(url){try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}}
// Every spelling of the desktop credential header is removed; only the Core's own origin gets one canonical token.
function desktopHeaders(requestHeaders,url,origin,token){const headers={...requestHeaders};for(const key of Object.keys(headers))if(key.toLowerCase()==='x-jarvis-desktop')delete headers[key];if(trusted(url,origin))headers['X-Jarvis-Desktop']=token;return headers;}
module.exports={trusted,external,desktopHeaders};
