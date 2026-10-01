'use strict';
// Fixed packaged TEST client entry. Never loads the legacy backend branches.
if(typeof process.send!=='function')throw Error('TRUSTED_TEST_LAUNCHER_REQUIRED');
// Only nonsecret identity/path metadata crosses argv. Establish the existing
// TEST profile/rendering policy synchronously, before Electron readiness.
const args=process.argv.filter(a=>a.startsWith('--stage4-bootstrap='));
if(args.length!==1||args[0].length>16384)throw Error('DEPLOYMENT_BOOTSTRAP');
const cfg=JSON.parse(Buffer.from(args[0].slice('--stage4-bootstrap='.length),'base64url').toString('utf8'));
if(!cfg||Object.keys(cfg).sort().join(',')!=='clientId,deployment'||!cfg.deployment||!['teague','intelligence'].includes(cfg.clientId))throw Error('DEPLOYMENT_CONFIG');
require('./stage4_client.cjs').launchTestClient(cfg.clientId,cfg.deployment);
// launchTestClient retains the private IPC listener and validates/authenticates
// the full configuration before attachment and BrowserWindow creation.
