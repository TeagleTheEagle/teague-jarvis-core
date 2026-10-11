// What the You panel says and sends (static/you.js; about_you.py, docs/ABOUT-YOU.md). The Core keeps and checks the
// entries; these are the words on screen, the grouping and the fields of an add.
const assert=require('node:assert/strict');
const y=require('./static/you.js');
assert.deepEqual(y.SECTIONS,['about','person','date','like','dislike','goal'],'the same order as about_you.SECTIONS');
assert.equal(y.MONTHS.length,12);
for(const id of y.SECTIONS)assert.ok(y.NAMES[id]&&y.FORM[id]&&y.FORM[id].title,'every section has a name and a form: '+id);
const entries=[{section:'like',line:'AC/DC'},{section:'person',line:'Will (brother)'},{section:'about',line:'Electrician'},{section:'like',line:'Pies'}];
assert.deepEqual(y.grouped(entries).map(g=>[g.name,g.rows.map(r=>r.line)]),[['About you',['Electrician']],['People',['Will (brother)']],['Likes',['AC/DC','Pies']]],'grouped in the page order, empty sections left out');
assert.deepEqual(y.grouped(null),[]);
assert.equal(y.countText(1),'1 entry');
assert.equal(y.countText(0),'0 entries');
// An add sends the date only where the section has one and both the day and the month are chosen; the year when written.
assert.deepEqual(y.addBody('person',' Will ','brother','14','3','1996'),{action:'add',section:'person',title:'Will',detail:'brother',day:14,month:3,year:1996});
assert.deepEqual(y.addBody('person','Mum','mother','10','10',''),{action:'add',section:'person',title:'Mum',detail:'mother',day:10,month:10});
assert.deepEqual(y.addBody('person','Will','brother','14','',''),{action:'add',section:'person',title:'Will',detail:'brother'},'no month: no date');
assert.deepEqual(y.addBody('like','AC/DC','ignored','14','3',''),{action:'add',section:'like',title:'AC/DC',detail:''},'a like has no detail and no date');
console.log('you view: ok');
