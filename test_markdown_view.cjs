// Formatted replies (static/markdown-view.js): the parser turns the marks the AI model writes into structure, keeps
// anything unfinished exactly as typed, and never treats reply text as HTML.
const assert=require('node:assert/strict');
const md=require('./static/markdown-view.js');
const flat=nodes=>nodes.map(n=>n.t==='text'?n.v:n.t==='code'?'<code:'+n.v+'>':n.t==='link'?'<link:'+n.v+'|'+n.url+'>':'<'+n.t+':'+flat(n.c)+'>').join('');
// Inline marks.
assert.equal(flat(md.inline('**Better reasoning.** Answer the question.')),'<b:Better reasoning.> Answer the question.');
assert.equal(flat(md.inline('plain *emphasis* and _also this_ and `code **kept**`')),'plain <i:emphasis> and <i:also this> and <code:code **kept**>');
assert.equal(flat(md.inline('***both***')),'<b:<i:both>>');
assert.equal(flat(md.inline('read-only assessment → **sandboxed improvements** → done')),'read-only assessment → <b:sandboxed improvements> → done');
// Not marks: arithmetic, snake_case names, a lone star, escaped stars.
assert.equal(flat(md.inline('2 * 3 * 4 and file_name_here and 5*')),'2 * 3 * 4 and file_name_here and 5*');
assert.equal(flat(md.inline('\\*not bold\\*')),'*not bold*');
// A reply that is still arriving keeps its unfinished mark as typed.
assert.equal(flat(md.inline('**Better reaso')),'**Better reaso');
assert.equal(flat(md.inline('finished `code and then `unfinished')),'finished <code:code and then >unfinished');
// Links are data for a label, never markup; only http(s) addresses are recognised.
assert.equal(flat(md.inline('see [the page](https://example.com/a) now')),'see <link:the page|https://example.com/a> now');
assert.equal(flat(md.inline('[x](javascript:alert(1))')),'[x](javascript:alert(1))');
// HTML in a reply stays text.
assert.equal(flat(md.inline('<img src=x onerror=alert(1)> **b**')),'<img src=x onerror=alert(1)> <b:b>');

// Blocks: the owner's two example replies in miniature.
let blocks=md.parse('Mr. Teague, intro line.\n\n1. **First.** One\n   two words.\n2. **Second.** Two.\n10. **Tenth.** Ten.\n\nMy top three would be these.');
assert.deepEqual(blocks.map(b=>b.type),['p','ol','p']);
// A note app.js adds on its own line after a list is a paragraph, not part of the last item.
assert.deepEqual(md.parse('- one\n- two\nStopped.').map(b=>b.type),['ul','p']);
assert.deepEqual(blocks[1].items.map(i=>i.number),[1,2,10]);
assert.equal(flat(blocks[1].items[0].lines[0]),'<b:First.> One');
blocks=md.parse('1. **Recursive self-improvement**\n   I would need a loop.\n\n2. **Setting goals**\n   I would need a planner.\n\nThe foundation is measurement.');
assert.deepEqual(blocks.map(b=>b.type),['ol','p']);
assert.equal(blocks[0].items.length,2);
assert.deepEqual(blocks[0].items[0].lines.map(flat),['<b:Recursive self-improvement>','I would need a loop.']);
assert.equal(blocks[0].items[1].number,2);
// Headings, bullets, rules, quotes, code fences.
blocks=md.parse('## Plan\n- one\n- two\n\n---\n> quoted\n> again\n\n```\nx = **1**\n<b>\n```\nend');
assert.deepEqual(blocks.map(b=>b.type),['h','ul','hr','quote','code','p']);
assert.equal(blocks[0].level,2);assert.equal(blocks[1].items.length,2);assert.equal(blocks[3].lines.length,2);
assert.equal(blocks[4].text,'x = **1**\n<b>');
// A bold line is not a bullet; an unfinished code fence takes the rest; empty input gives nothing.
assert.deepEqual(md.parse('**Title**\ntext').map(b=>b.type),['p']);
assert.deepEqual(md.parse('```\nstill arriving').map(b=>b.type),['code']);
assert.deepEqual(md.parse(''),[]);assert.deepEqual(md.parse(null),[]);
// A numbered list followed by bullets, then numbers again, keeps each number.
blocks=md.parse('1. one\n   - detail\n2. two');
assert.deepEqual(blocks.map(b=>b.type+(b.indent?'+':'')),['ol','ul+','ol']);assert.equal(blocks[2].items[0].number,2);
console.log('Formatted reply parser checks passed.');
