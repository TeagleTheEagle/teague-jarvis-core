function trusted(url,origin){try{return new URL(url).origin===origin;}catch{return false;}}
function external(url){try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}}
module.exports={trusted,external};
