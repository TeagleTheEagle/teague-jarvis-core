/* Formatted view of JARVIS's replies (1.0.15). The AI model writes Markdown (**bold**, numbered lists, headings);
   the conversation used to print those marks as typed. This file reads the reply text that app.js keeps in the
   message paragraph and shows a formatted copy beside it. The paragraph stays the source: app.js still appends to
   it while a reply streams, screen readers still read it, and nothing here is sent anywhere.
   Safety: the formatted copy is built from elements and text nodes only. Reply text is never parsed as HTML, and
   links are shown as text, not as links. The parser is shared with test_markdown_view.cjs. */
const JarvisMarkdown = (() => {
  // Inline marks -> [{t:'text',v} | {t:'code',v} | {t:'b',c} | {t:'i',c} | {t:'link',v,url}]. A mark without its
  // closing partner stays as typed, so a reply that is still arriving never loses characters.
  function inline(text) {
    const out = []; let buffer = '', i = 0;
    const flush = () => { if (buffer) { out.push({t: 'text', v: buffer}); buffer = ''; } };
    const space = ch => ch === undefined || /\s/.test(ch), word = ch => ch !== undefined && /[A-Za-z0-9]/.test(ch);
    while (i < text.length) {
      const ch = text[i];
      if (ch === '\\' && '*_`#[]()\\'.includes(text[i + 1] || ' ')) { buffer += text[i + 1]; i += 2; continue; }
      if (ch === '`') { const end = text.indexOf('`', i + 1); if (end > i + 1) { flush(); out.push({t: 'code', v: text.slice(i + 1, end)}); i = end + 1; continue; } }
      if (ch === '[') { const link = text.slice(i).match(/^\[([^\]\n]{1,300})\]\((https?:\/\/[^\s)]{1,2000})\)/);
        if (link) { flush(); out.push({t: 'link', v: link[1], url: link[2]}); i += link[0].length; continue; } }
      if (text.startsWith('**', i) && !space(text[i + 2])) {
        let end = text.indexOf('**', i + 2); while (end !== -1 && space(text[end - 1])) end = text.indexOf('**', end + 1);
        if (end !== -1 && text[end + 2] === '*') end += 1;  // "***both***": close on the last pair
        if (end > i + 2) { flush(); out.push({t: 'b', c: inline(text.slice(i + 2, end))}); i = end + 2; continue; }
      }
      if ((ch === '*' || ch === '_') && text[i + 1] !== ch && !space(text[i + 1]) && (ch === '*' || !word(text[i - 1]))) {
        let end = text.indexOf(ch, i + 2);
        while (end !== -1 && (space(text[end - 1]) || text[end + 1] === ch || (ch === '_' && word(text[end + 1])))) end = text.indexOf(ch, end + 1);
        if (end !== -1) { flush(); out.push({t: 'i', c: inline(text.slice(i + 1, end))}); i = end + 1; continue; }
      }
      buffer += ch; i += 1;
    }
    flush(); return out;
  }

  // Blocks -> [{type:'p'|'quote',lines} | {type:'h',level,inline} | {type:'ul'|'ol',indent,items:[{number,lines}]} |
  //            {type:'code',text} | {type:'hr'}], where lines is a list of inline lists (one per source line).
  function parse(text) {
    const lines = String(text == null ? '' : text).replace(/\r\n?/g, '\n').split('\n'), blocks = [];
    let para = null, list = null, i = 0;
    const bulletOf = line => line.match(/^(\s{0,8})[-*•]\s+(.*)$/), numberOf = line => line.match(/^(\s{0,8})(\d{1,3})[.)]\s+(.*)$/);
    const close = () => { para = null; list = null; };
    while (i < lines.length) {
      const line = lines[i];
      if (/^\s*```/.test(line)) { close(); const body = []; i += 1; while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) body.push(lines[i++]);
        i += 1; blocks.push({type: 'code', text: body.join('\n')}); continue; }
      if (!line.trim()) { para = null;  // a list survives blank lines while another item, or an indented line of an item, follows
        const next = lines.slice(i + 1).find(l => l.trim());
        if (list && !(next !== undefined && ((list.type === 'ul' ? bulletOf(next) : numberOf(next)) || /^\s{2,}\S/.test(next)))) list = null;
        i += 1; continue; }
      const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (heading) { close(); blocks.push({type: 'h', level: heading[1].length, inline: inline(heading[2])}); i += 1; continue; }
      if (/^\s{0,3}([-*_])(\s*\1){2,}\s*$/.test(line)) { close(); blocks.push({type: 'hr'}); i += 1; continue; }
      const bullet = bulletOf(line), numbered = bullet ? null : numberOf(line);
      if (bullet || numbered) { para = null; const type = bullet ? 'ul' : 'ol', indent = (bullet || numbered)[1].length >= 2;
        if (!list || list.type !== type || list.indent !== indent) { list = {type, indent, items: []}; blocks.push(list); }
        list.items.push({number: numbered ? Number(numbered[2]) : null, lines: [inline(bullet ? bullet[2] : numbered[3])]}); i += 1; continue; }
      // An indented line continues the item above. A line that is not indented starts a new paragraph, so the notes
      // app.js adds on their own line ("Stopped.", an error) never end up inside the last list item.
      if (list && /^\s{2,}\S/.test(line)) { list.items[list.items.length - 1].lines.push(inline(line.trim())); i += 1; continue; }
      const quote = line.match(/^\s{0,3}>\s?(.*)$/), kind = quote ? 'quote' : 'p';
      list = null; if (!para || para.type !== kind) { para = {type: kind, lines: []}; blocks.push(para); }
      para.lines.push(inline(quote ? quote[1] : line.trim())); i += 1;
    }
    return blocks;
  }
  return {inline, parse};
})();
if (typeof module !== 'undefined') module.exports = JarvisMarkdown;

if (typeof document !== 'undefined') (() => {
  const messages = document.querySelector('#messages'); if (!messages) return;
  const el = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };
  const spans = (nodes, parent) => { for (const n of nodes) {
    if (n.t === 'text') parent.append(document.createTextNode(n.v));
    else if (n.t === 'code') { const code = el('code'); code.textContent = n.v; parent.append(code); }
    else if (n.t === 'link') { const label = el('span', 'md-link'); label.textContent = n.v; label.title = n.url; parent.append(label); }
    else { const mark = el(n.t === 'b' ? 'strong' : 'em'); spans(n.c, mark); parent.append(mark); } } };
  const rows = (lines, parent) => lines.forEach((nodes, i) => { if (i) parent.append(el('br')); spans(nodes, parent); });
  function render(text) {
    const root = document.createDocumentFragment();
    for (const block of JarvisMarkdown.parse(text)) {
      if (block.type === 'h') { const h = el('h4', 'md-h' + Math.min(block.level, 3)); spans(block.inline, h); root.append(h); }
      else if (block.type === 'code') { const pre = el('pre'), code = el('code'); code.textContent = block.text; pre.append(code); root.append(pre); }
      else if (block.type === 'hr') root.append(el('hr'));
      else if (block.type === 'ul' || block.type === 'ol') { const listEl = el(block.type, block.indent ? 'md-indent' : '');
        for (const item of block.items) { const li = el('li'); if (item.number !== null) li.value = item.number; rows(item.lines, li); listEl.append(li); }
        root.append(listEl); }
      else { const p = el(block.type === 'quote' ? 'blockquote' : 'p'); rows(block.lines, p); root.append(p); }
    }
    return root;
  }

  const SOURCE = '.message.assistant > p';
  const views = new WeakMap(), shown = new WeakMap(), waiting = new Set(); let scheduled = false;
  function refresh(p) {
    let viewEl = views.get(p);
    if (!viewEl) { viewEl = el('div', 'md-view'); viewEl.setAttribute('aria-hidden', 'true'); views.set(p, viewEl); p.classList.add('md-source'); p.after(viewEl); }
    const text = p.textContent;
    if (shown.get(p) !== text) { shown.set(p, text); viewEl.replaceChildren(render(text)); }
    const activity = p.dataset.activity || ''; if (viewEl.dataset.activity !== activity) viewEl.dataset.activity = activity;
  }
  const queue = p => { waiting.add(p); if (scheduled) return; scheduled = true;
    requestAnimationFrame(() => { scheduled = false; const batch = [...waiting]; waiting.clear(); for (const item of batch) if (item.isConnected) refresh(item); }); };
  new MutationObserver(records => { for (const record of records) {
    const target = record.target.nodeType === 1 ? record.target : record.target.parentElement;
    if (target && target.matches(SOURCE)) queue(target);
    for (const node of record.addedNodes) if (node.nodeType === 1) { if (node.matches(SOURCE)) queue(node); for (const p of node.querySelectorAll(SOURCE)) queue(p); }
  } }).observe(messages, {childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['data-activity']});
  for (const p of messages.querySelectorAll(SOURCE)) queue(p);
})();
