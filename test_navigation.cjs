const assert=require('node:assert/strict');
const nav=require('./static/navigation.js');
for(const [input,want] of [['Hey Jarvis, open projects.','projects'],['Please switch to the mission log tab','mission'],['show me system status','system'],['open focus and tasks','focus'],['go to command center','command'],['open settings please','settings'],['open maps','maps'],['take me to the transcript','communications']])assert.equal(nav.destination(input),want,input);
for(const text of ['How do I open projects?','open projects and delete them','open https://example.com','tell me about maps','do not open projects'])assert.equal(nav.destination(text),null,text);
console.log('Navigation commands and non-navigation exclusions passed.');

for(const input of ['Can you open Projects?', 'Hey Jarvis, could you please go from the command page to projects?', 'switch from command to the projects page', 'navigate to projects'])assert.equal(nav.destination(input),'projects',input);
for(const [input,want] of [['open dashboard','command'],['Hey Jarvis, open the activity log','mission'],['show me release history','changes'],['open chat','communications'],['go to tasks','focus'],['go from the dashboard to projects','projects']])assert.equal(nav.destination(input),want,input);
